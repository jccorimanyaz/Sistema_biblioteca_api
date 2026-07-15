from models import db
from datetime import datetime

class Reserva(db.Model):
    __tablename__ = 'reservas'
    
    id = db.Column(db.Integer, primary_key=True)
    id_libro = db.Column(db.Integer, db.ForeignKey('libros.id'), nullable=False)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_reserva = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    estado = db.Column(db.String(15), default='pendiente', nullable=False)  # 'pendiente', 'notificada', 'cancelada', 'completada'
    posicion_en_cola = db.Column(db.Integer, nullable=False)
    notificado = db.Column(db.Boolean, default=False, nullable=False)
    fecha_limite_retiro = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'id_libro': self.id_libro,
            'id_usuario': self.id_usuario,
            'fecha_reserva': self.fecha_reserva.isoformat() if self.fecha_reserva else None,
            'estado': self.estado,
            'posicion_en_cola': self.posicion_en_cola,
            'notificado': self.notificado,
            'fecha_limite_retiro': self.fecha_limite_retiro.isoformat() if self.fecha_limite_retiro else None
        }
