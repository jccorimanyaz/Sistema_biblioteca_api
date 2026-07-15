from datetime import datetime, timedelta
from models import db
from models.prestamo import Prestamo
from models.libro import Libro
from models.usuario import Usuario
from models.multa import Multa
from models.reserva import Reserva
from services.reserva_service import ReservaService
from config import Config

class PrestamoService:
    @staticmethod
    def crear_prestamo(id_libro, id_usuario, is_admin=False):
        """
        Creates a new loan for a book. Handles stock validation, user eligibility,
        and reservation priority check.
        """
        # Run cleanup first to clear expired hold times
        ReservaService.expire_reservations()
        
        # Validate user
        usuario = Usuario.query.get(id_usuario)
        if not usuario:
            return {"status": "error", "message": "Usuario no encontrado", "code": 404}
            
        if usuario.estado == 'suspendido':
            return {"status": "error", "message": "El usuario está suspendido", "code": 403}
            
        # Check active fines
        has_fines = Multa.query.filter_by(id_usuario=id_usuario, estado='pendiente').first()
        if has_fines:
            return {"status": "error", "message": "El usuario tiene multas pendientes y no puede solicitar préstamos", "code": 400}
            
        # Check maximum active loans
        active_loans_count = Prestamo.query.filter_by(id_usuario=id_usuario, estado='activo').count()
        if active_loans_count >= Config.MAX_ACTIVE_LOANS:
            return {"status": "error", "message": f"El usuario ya superó el límite de {Config.MAX_ACTIVE_LOANS} préstamos activos simultáneos", "code": 400}
            
        # Validate book
        libro = Libro.query.get(id_libro)
        if not libro:
            return {"status": "error", "message": "Libro no encontrado", "code": 404}
            
        if libro.estado == 'de baja':
            return {"status": "error", "message": "El libro está dado de baja y no se puede prestar", "code": 400}
            
        # Check reservation priority
        notified_reservations = Reserva.query.filter_by(id_libro=id_libro, estado='notificada').all()
        notified_count = len(notified_reservations)
        
        user_has_notified_res = next((r for r in notified_reservations if r.id_usuario == id_usuario), None)
        
        if notified_count > 0:
            if user_has_notified_res:
                # The user has priority. Complete the reservation.
                user_has_notified_res.estado = 'completada'
            else:
                # Stock is blocked for notified users
                if libro.cantidad_disponible <= notified_count:
                    return {
                        "status": "error", 
                        "message": "El stock disponible de este libro está reservado para otro usuario en la cola de espera", 
                        "code": 400
                    }
        else:
            # General availability check
            if libro.cantidad_disponible <= 0:
                return {"status": "error", "message": "El libro no tiene stock disponible para préstamo inmediato. Puede reservarlo.", "code": 400}
                
        # Create loan
        fecha_prestamo = datetime.utcnow()
        fecha_estimada = fecha_prestamo + timedelta(days=Config.LOAN_DAYS)
        
        nuevo_prestamo = Prestamo(
            id_libro=id_libro,
            id_usuario=id_usuario,
            fecha_prestamo=fecha_prestamo,
            fecha_devolucion_estimada=fecha_estimada,
            estado='activo',
            multa_generada=0.0
        )
        
        # Decrement stock
        libro.cantidad_disponible -= 1
        if libro.cantidad_disponible == 0:
            libro.estado = 'agotado'
            
        db.session.add(nuevo_prestamo)
        db.session.commit()
        
        return {
            "status": "success",
            "message": "Préstamo creado exitosamente",
            "data": nuevo_prestamo.to_dict(),
            "code": 201
        }

    @staticmethod
    def devolver_prestamo(id_prestamo, id_usuario, is_admin=False):
        """
        Processes the return of a borrowed book. Calculates any applicable delay fines,
        updates stock, and triggers reservation notifications for next-in-line readers.
        """
        # Run cleanup first
        ReservaService.expire_reservations()
        
        prestamo = Prestamo.query.get(id_prestamo)
        if not prestamo:
            return {"status": "error", "message": "Préstamo no encontrado", "code": 404}
            
        if not is_admin and prestamo.id_usuario != id_usuario:
            return {"status": "error", "message": "No tienes permisos para devolver este préstamo", "code": 403}
            
        if prestamo.estado == 'devuelto':
            return {"status": "error", "message": "El préstamo ya fue devuelto", "code": 400}
            
        # Update loan record
        now = datetime.utcnow()
        prestamo.fecha_devolucion_real = now
        prestamo.estado = 'devuelto'
        
        # Calculate fine if delayed
        multa_creada = None
        if now.date() > prestamo.fecha_devolucion_estimada.date():
            days_late = (now.date() - prestamo.fecha_devolucion_estimada.date()).days
            if days_late > 0:
                monto_multa = days_late * Config.FINE_PER_DAY
                prestamo.multa_generada = monto_multa
                
                multa_creada = Multa(
                    id_usuario=prestamo.id_usuario,
                    id_prestamo=prestamo.id,
                    monto=monto_multa,
                    estado='pendiente',
                    fecha_creacion=now
                )
                db.session.add(multa_creada)
        
        # Increment stock
        libro = prestamo.libro
        libro.cantidad_disponible += 1
        if libro.estado == 'agotado':
            libro.estado = 'disponible'
            
        # Trigger reservation notification for next person in line
        next_res = Reserva.query.filter_by(
            id_libro=prestamo.id_libro,
            estado='pendiente'
        ).order_by(Reserva.posicion_en_cola).first()
        
        if next_res:
            next_res.estado = 'notificada'
            next_res.notificado = True
            next_res.fecha_limite_retiro = now + timedelta(hours=Config.RESERVATION_HOLD_HOURS)
            next_res.posicion_en_cola = 0
            
            # Reorder queue
            ReservaService.reorder_queue(prestamo.id_libro)
            
        db.session.commit()
        
        res_data = prestamo.to_dict()
        if multa_creada:
            res_data['multa_generada_detalle'] = multa_creada.to_dict()
            
        return {
            "status": "success",
            "message": "Libro devuelto exitosamente" + (" con multa generada por retraso" if multa_creada else ""),
            "data": res_data,
            "code": 200
        }
