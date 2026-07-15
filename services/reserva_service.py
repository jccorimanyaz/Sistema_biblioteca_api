from datetime import datetime, timedelta
from models import db
from models.reserva import Reserva
from models.libro import Libro
from models.usuario import Usuario
from models.multa import Multa

class ReservaService:
    @staticmethod
    def expire_reservations():
        """
        Looks for expired reservations that were notified and users failed to pick up.
        Cancels them and notifies the next person in queue.
        """
        now = datetime.utcnow()
        expired = Reserva.query.filter(
            Reserva.estado == 'notificada',
            Reserva.fecha_limite_retiro < now
        ).all()
        
        for res in expired:
            res.estado = 'cancelada'
            
            # Find next user in queue for this book
            next_res = Reserva.query.filter_by(
                id_libro=res.id_libro,
                estado='pendiente'
            ).order_by(Reserva.posicion_en_cola).first()
            
            if next_res:
                next_res.estado = 'notificada'
                next_res.notificado = True
                next_res.fecha_limite_retiro = now + timedelta(hours=48)
                next_res.posicion_en_cola = 0
                
                # Reorder the remaining queue
                ReservaService.reorder_queue(res.id_libro)
                
        db.session.commit()

    @staticmethod
    def reorder_queue(id_libro):
        """
        Re-indexes the positions of all pending reservations for a given book.
        """
        pending = Reserva.query.filter_by(
            id_libro=id_libro,
            estado='pendiente'
        ).order_by(Reserva.fecha_reserva).all()
        
        for idx, res in enumerate(pending, start=1):
            res.posicion_en_cola = idx

    @staticmethod
    def crear_reserva(id_libro, id_usuario):
        """
        Creates a new reservation for a book when there's no available general stock.
        """
        # Run cleanup first
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
            return {"status": "error", "message": "El usuario tiene multas pendientes y no puede reservar libros", "code": 400}
            
        # Validate book
        libro = Libro.query.get(id_libro)
        if not libro:
            return {"status": "error", "message": "Libro no encontrado", "code": 404}
            
        if libro.estado == 'de baja':
            return {"status": "error", "message": "El libro está dado de baja y no se puede reservar", "code": 400}
            
        # Check if user already has an active reservation for this book
        existing_res = Reserva.query.filter(
            Reserva.id_libro == id_libro,
            Reserva.id_usuario == id_usuario,
            Reserva.estado.in_(['pendiente', 'notificada'])
        ).first()
        if existing_res:
            return {"status": "error", "message": "Ya tienes una reserva activa para este libro", "code": 400}
            
        # Determine if reservation is allowed (stock must be fully occupied by loans or other reservations)
        notified_res_count = Reserva.query.filter_by(id_libro=id_libro, estado='notificada').count()
        
        # If there is unreserved stock, user should borrow instead of reserving
        if libro.cantidad_disponible > notified_res_count:
            return {
                "status": "error", 
                "message": f"El libro tiene stock disponible para préstamo inmediato ({libro.cantidad_disponible - notified_res_count} copias libres)", 
                "code": 400
            }
            
        # Calculate FIFO queue position
        pending_count = Reserva.query.filter_by(id_libro=id_libro, estado='pendiente').count()
        posicion = pending_count + 1
        
        nueva_reserva = Reserva(
            id_libro=id_libro,
            id_usuario=id_usuario,
            estado='pendiente',
            posicion_en_cola=posicion
        )
        
        db.session.add(nueva_reserva)
        db.session.commit()
        
        return {
            "status": "success",
            "message": "Reserva creada exitosamente",
            "data": nueva_reserva.to_dict(),
            "code": 201
        }

    @staticmethod
    def cancelar_reserva(id_reserva, id_usuario, is_admin=False):
        """
        Cancels a reservation. If the reservation was notified, the next pending user is notified.
        """
        ReservaService.expire_reservations()
        
        reserva = Reserva.query.get(id_reserva)
        if not reserva:
            return {"status": "error", "message": "Reserva no encontrada", "code": 404}
            
        if not is_admin and reserva.id_usuario != id_usuario:
            return {"status": "error", "message": "No tienes permisos para cancelar esta reserva", "code": 403}
            
        if reserva.estado in ['cancelada', 'completada']:
            return {"status": "error", "message": f"La reserva ya se encuentra {reserva.estado}", "code": 400}
            
        old_estado = reserva.estado
        reserva.estado = 'cancelada'
        reserva.posicion_en_cola = 0
        
        # Reorder remaining queue
        ReservaService.reorder_queue(reserva.id_libro)
        
        # If it was notified, notify the next person in line
        if old_estado == 'notificada':
            next_res = Reserva.query.filter_by(
                id_libro=reserva.id_libro,
                estado='pendiente'
            ).order_by(Reserva.posicion_en_cola).first()
            
            if next_res:
                next_res.estado = 'notificada'
                next_res.notificado = True
                next_res.fecha_limite_retiro = datetime.utcnow() + timedelta(hours=48)
                next_res.posicion_en_cola = 0
                
                # Reorder the queue again since we shifted next_res out of 'pendiente'
                ReservaService.reorder_queue(reserva.id_libro)
                
        db.session.commit()
        
        return {
            "status": "success",
            "message": "Reserva cancelada exitosamente",
            "data": reserva.to_dict(),
            "code": 200
        }
