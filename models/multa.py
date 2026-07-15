from models import db
from datetime import datetime

class Multa(db.Model):
    __tablename__ = 'multas'
    
    id = db.Column(db.Integer, primary_key=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_prestamo = db.Column(db.Integer, db.ForeignKey('prestamos.id'), nullable=False)
    monto = db.Column(db.Float, nullable=False)
    estado = db.Column(db.String(15), default='pendiente', nullable=False)  # 'pendiente', 'pagada'
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'id_usuario': self.id_usuario,
            'id_prestamo': self.id_prestamo,
            'monto': self.monto,
            'estado': self.estado,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None
        }
