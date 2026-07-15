from models import db

class Libro(db.Model):
    __tablename__ = 'libros'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    autor = db.Column(db.String(100), nullable=False)
    isbn = db.Column(db.String(30), unique=True, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    editorial = db.Column(db.String(100), nullable=True)
    ano = db.Column(db.Integer, nullable=True)
    cantidad_total = db.Column(db.Integer, default=1, nullable=False)
    cantidad_disponible = db.Column(db.Integer, default=1, nullable=False)
    estado = db.Column(db.String(20), default='disponible', nullable=False)  # 'disponible', 'agotado', 'de baja'
    
    prestamos = db.relationship('Prestamo', backref='libro', lazy=True)
    reservas = db.relationship('Reserva', backref='libro', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'autor': self.autor,
            'isbn': self.isbn,
            'categoria': self.categoria,
            'editorial': self.editorial,
            'ano': self.ano,
            'cantidad_total': self.cantidad_total,
            'cantidad_disponible': self.cantidad_disponible,
            'estado': self.estado
        }
