import os
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

import unittest
from datetime import datetime, timedelta
from app import app
from models import db
from models.usuario import Usuario
from models.libro import Libro
from models.prestamo import Prestamo
from models.reserva import Reserva
from models.multa import Multa

class BibliotecaTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.seed_data()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def seed_data(self):
        # Admin User
        self.admin = Usuario(nombre="Admin Test", email="admin@test.com", rol="admin")
        self.admin.set_password("password123")
        
        # Readers
        self.lector1 = Usuario(nombre="Lector Uno", email="lector1@test.com", rol="lector")
        self.lector1.set_password("password123")
        
        self.lector2 = Usuario(nombre="Lector Dos", email="lector2@test.com", rol="lector")
        self.lector2.set_password("password123")
        
        db.session.add_all([self.admin, self.lector1, self.lector2])
        db.session.commit()
        
        # Books
        self.libro_stock = Libro(
            titulo="Libro Stock", autor="Autor Test", isbn="1111",
            categoria="Cat", cantidad_total=1, cantidad_disponible=1
        )
        self.libro_nostock = Libro(
            titulo="Libro No Stock", autor="Autor Test", isbn="2222",
            categoria="Cat", cantidad_total=1, cantidad_disponible=0, estado="agotado"
        )
        db.session.add_all([self.libro_stock, self.libro_nostock])
        db.session.commit()
        
        # Active loan on libro_nostock for lector1 to justify 0 stock
        self.active_loan = Prestamo(
            id_libro=self.libro_nostock.id,
            id_usuario=self.lector1.id,
            fecha_prestamo=datetime.utcnow() - timedelta(days=2),
            fecha_devolucion_estimada=datetime.utcnow() + timedelta(days=12),
            estado="activo"
        )
        db.session.add(self.active_loan)
        db.session.commit()

    def get_token(self, email, password="password123"):
        res = self.client.post('/auth/login', json={"email": email, "password": password})
        return res.json['data']['token']

    def test_registration_and_login(self):
        # Register new reader
        res = self.client.post('/auth/register', json={
            "nombre": "Nuevo Lector",
            "email": "nuevo@test.com",
            "password": "password123"
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json['status'], 'success')
        
        # Login
        token = self.get_token("nuevo@test.com")
        self.assertIsNotNone(token)

    def test_catalog_access(self):
        # GET /libros (public)
        res = self.client.get('/libros')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(res.json['data']) >= 2)

    def test_borrow_success(self):
        token = self.get_token("lector1@test.com")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Borrow book with stock
        res = self.client.post('/prestamos', headers=headers, json={"id_libro": self.libro_stock.id})
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json['data']['estado'], 'activo')
        
        # Verify stock decreased
        libro = db.session.get(Libro, self.libro_stock.id)
        self.assertEqual(libro.cantidad_disponible, 0)
        self.assertEqual(libro.estado, 'agotado')

    def test_borrow_out_of_stock_triggers_reservation(self):
        token = self.get_token("lector2@test.com")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try borrowing out of stock book, should fail
        res = self.client.post('/prestamos', headers=headers, json={"id_libro": self.libro_nostock.id})
        self.assertEqual(res.status_code, 400)
        self.assertIn("no tiene stock disponible", res.json['message'])
        
        # Reserve book
        res_reserva = self.client.post('/reservas', headers=headers, json={"id_libro": self.libro_nostock.id})
        self.assertEqual(res_reserva.status_code, 201)
        self.assertEqual(res_reserva.json['data']['posicion_en_cola'], 1)
        self.assertEqual(res_reserva.json['data']['estado'], 'pendiente')

    def test_return_late_generates_fine(self):
        # Create an overdue loan manually for lector1
        overdue_loan = Prestamo(
            id_libro=self.libro_stock.id,
            id_usuario=self.lector1.id,
            fecha_prestamo=datetime.utcnow() - timedelta(days=20),
            fecha_devolucion_estimada=datetime.utcnow() - timedelta(days=6),  # Late by 6 days
            estado="activo"
        )
        db.session.add(overdue_loan)
        db.session.commit()
        
        token = self.get_token("lector1@test.com")
        headers = {"Authorization": f"Bearer {token}"}
        
        # Return loan
        res = self.client.put(f'/prestamos/{overdue_loan.id}/devolver', headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json['data']['estado'], 'devuelto')
        self.assertEqual(res.json['data']['multa_generada'], 12.0)  # 6 days * 2.0
        
        # Check active fine blocks new borrowing
        res_borrow = self.client.post('/prestamos', headers=headers, json={"id_libro": self.libro_stock.id})
        self.assertEqual(res_borrow.status_code, 400)
        self.assertIn("multas pendientes", res_borrow.json['message'])
        
        # Pay fine
        fine_id = res.json['data']['multa_generada_detalle']['id']
        res_pay = self.client.put(f'/multas/{fine_id}/pagar', headers=headers)
        self.assertEqual(res_pay.status_code, 200)
        self.assertEqual(res_pay.json['data']['estado'], 'pagada')
        
        # Now can borrow again
        res_borrow_ok = self.client.post('/prestamos', headers=headers, json={"id_libro": self.libro_stock.id})
        self.assertEqual(res_borrow_ok.status_code, 201)

    def test_reservation_notification_on_return(self):
        # Add lector2 reservation for libro_nostock
        reserva = Reserva(
            id_libro=self.libro_nostock.id,
            id_usuario=self.lector2.id,
            estado='pendiente',
            posicion_en_cola=1
        )
        db.session.add(reserva)
        db.session.commit()
        
        # Return book by lector1
        token_l1 = self.get_token("lector1@test.com")
        headers_l1 = {"Authorization": f"Bearer {token_l1}"}
        res_return = self.client.put(f'/prestamos/{self.active_loan.id}/devolver', headers=headers_l1)
        self.assertEqual(res_return.status_code, 200)
        
        # Verify reservation is notified
        res_updated = db.session.get(Reserva, reserva.id)
        self.assertEqual(res_updated.estado, 'notificada')
        self.assertTrue(res_updated.notificado)
        self.assertIsNotNone(res_updated.fecha_limite_retiro)
        
        # Lector1 tries to borrow it (should fail since it is held for lector2)
        res_borrow_l1 = self.client.post('/prestamos', headers=headers_l1, json={"id_libro": self.libro_nostock.id})
        self.assertEqual(res_borrow_l1.status_code, 400)
        self.assertIn("reservado para otro usuario", res_borrow_l1.json['message'])
        
        # Lector2 borrows it successfully
        token_l2 = self.get_token("lector2@test.com")
        headers_l2 = {"Authorization": f"Bearer {token_l2}"}
        res_borrow_l2 = self.client.post('/prestamos', headers=headers_l2, json={"id_libro": self.libro_nostock.id})
        self.assertEqual(res_borrow_l2.status_code, 201)
        self.assertEqual(db.session.get(Reserva, reserva.id).estado, 'completada')

if __name__ == '__main__':
    unittest.main()
