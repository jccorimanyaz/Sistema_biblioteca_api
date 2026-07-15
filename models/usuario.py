from models import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(15), default='lector', nullable=False)  # 'admin', 'lector'
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    estado = db.Column(db.String(15), default='activo', nullable=False)  # 'activo', 'suspendido'
    
    prestamos = db.relationship('Prestamo', backref='usuario', lazy=True)
    reservas = db.relationship('Reserva', backref='usuario', lazy=True)
    multas = db.relationship('Multa', backref='usuario', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'email': self.email,
            'rol': self.rol,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'estado': self.estado
        }
