from models import db
from datetime import datetime

class Prestamo(db.Model):
    __tablename__ = 'prestamos'
    
    id = db.Column(db.Integer, primary_key=True)
    id_libro = db.Column(db.Integer, db.ForeignKey('libros.id'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_prestamo = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    fecha_devolucion_estimada = db.Column(db.DateTime, nullable=False)
    fecha_devolucion_real = db.Column(db.DateTime, nullable=True)
    estado = db.Column(db.String(15), default='activo', nullable=False)  # 'activo', 'devuelto', 'vencido'
    multa_generada = db.Column(db.Float, default=0.0, nullable=False)
    
    # Relationship to fines (one loan can generate a fine)
    multas = db.relationship('Multa', backref='prestamo', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'id_libro': self.id_libro,
            'id_usuario': self.id_usuario,
            'fecha_prestamo': self.fecha_prestamo.isoformat() if self.fecha_prestamo else None,
            'fecha_devolucion_estimada': self.fecha_devolucion_estimada.isoformat() if self.fecha_devolucion_estimada else None,
            'fecha_devolucion_real': self.fecha_devolucion_real.isoformat() if self.fecha_devolucion_real else None,
            'estado': self.estado,
            'multa_generada': self.multa_generada
        }
