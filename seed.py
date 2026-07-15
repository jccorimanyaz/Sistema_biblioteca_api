from app import app
from models import db
from models.usuario import Usuario
from models.libro import Libro
from models.prestamo import Prestamo
from datetime import datetime, timedelta

def seed_db():
    print("Iniciando poblamiento de la base de datos...")
    
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()
        print("Base de datos limpiada y recreada.")
        
        # 1. Seed Users
        admin = Usuario(nombre="Administrador General", email="admin@biblioteca.com", rol="admin", estado="activo")
        admin.set_password("admin123")
        
        lector1 = Usuario(nombre="Juan Pérez", email="juan@correo.com", rol="lector", estado="activo")
        lector1.set_password("lector123")
        
        lector2 = Usuario(nombre="María Gómez", email="maria@correo.com", rol="lector", estado="activo")
        lector2.set_password("lector123")
        
        lector_suspendido = Usuario(nombre="Usuario Suspendido", email="suspendido@correo.com", rol="lector", estado="suspendido")
        lector_suspendido.set_password("lector123")
        
        db.session.add_all([admin, lector1, lector2, lector_suspendido])
        db.session.commit()
        print("Usuarios de prueba creados.")
        
        # 2. Seed Books
        libro1 = Libro(
            titulo="Cien años de soledad",
            autor="Gabriel García Márquez",
            isbn="978-0307474728",
            categoria="Ficción",
            editorial="Sudamericana",
            ano=1967,
            cantidad_total=3,
            cantidad_disponible=3,
            estado="disponible"
        )
        
        libro2 = Libro(
            titulo="1984",
            autor="George Orwell",
            isbn="978-0451524935",
            categoria="Novela",
            editorial="Seix Barral",
            ano=1949,
            cantidad_total=1,
            cantidad_disponible=1,
            estado="disponible"
        )
        
        libro3 = Libro(
            titulo="El ingenioso hidalgo Don Quijote de la Mancha",
            autor="Miguel de Cervantes",
            isbn="978-8420668291",
            categoria="Clásicos",
            editorial="Alianza",
            ano=1605,
            cantidad_total=2,
            cantidad_disponible=2,
            estado="disponible"
        )
        
        libro4 = Libro(
            titulo="Breve historia del tiempo",
            autor="Stephen Hawking",
            isbn="978-8498925470",
            categoria="Divulgación",
            editorial="Crítica",
            ano=1988,
            cantidad_total=1,
            cantidad_disponible=1,
            estado="disponible"
        )
        
        db.session.add_all([libro1, libro2, libro3, libro4])
        db.session.commit()
        print("Libros de prueba creados.")
        
        # 3. Seed an active loan to deplete book2 ("1984") stock to 0
        # This allows testing the reservation system immediately!
        fecha_prestamo = datetime.utcnow() - timedelta(days=5)
        fecha_estimada = fecha_prestamo + timedelta(days=14)
        
        prestamo = Prestamo(
            id_libro=libro2.id,
            id_usuario=lector1.id,
            fecha_prestamo=fecha_prestamo,
            fecha_devolucion_estimada=fecha_estimada,
            estado="activo",
            multa_generada=0.0
        )
        libro2.cantidad_disponible = 0
        libro2.estado = "agotado"
        
        # Create a late loan for lector2 to test overdue fine calculation when returning
        fecha_prestamo_vencido = datetime.utcnow() - timedelta(days=20)
        fecha_estimada_vencida = fecha_prestamo_vencido + timedelta(days=14) # overdue by 6 days
        
        prestamo_vencido = Prestamo(
            id_libro=libro3.id,
            id_usuario=lector2.id,
            fecha_prestamo=fecha_prestamo_vencido,
            fecha_devolucion_estimada=fecha_estimada_vencida,
            estado="activo",
            multa_generada=0.0
        )
        libro3.cantidad_disponible -= 1
        
        db.session.add_all([prestamo, prestamo_vencido])
        db.session.commit()
        print("Préstamos de prueba creados (incluyendo uno vencido y uno que agota stock de '1984').")
        
        print("\nPoblamiento finalizado con éxito.")
        print("\nCuentas creadas:")
        print(f" - Admin: {admin.email} / admin123")
        print(f" - Lector 1: {lector1.email} / lector123 (Tiene en préstamo '1984')")
        print(f" - Lector 2: {lector2.email} / lector123 (Tiene en préstamo vencido 'Don Quijote')")
        print(f" - Lector Suspendido: {lector_suspendido.email} / lector123")

if __name__ == '__main__':
    seed_db()
