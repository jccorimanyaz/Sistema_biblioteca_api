from flask import Blueprint, request, jsonify
from models import db
from models.libro import Libro
from schemas import LibroSchema
from utils.auth_decorators import admin_required

libros_bp = Blueprint('libros', __name__, url_prefix='/libros')

@libros_bp.route('', methods=['GET'])
def get_libros():
    categoria = request.args.get('categoria')
    autor = request.args.get('autor')
    disponibilidad = request.args.get('disponibilidad')
    search = request.args.get('search')
    
    query = Libro.query.filter(Libro.estado != 'de baja')
    
    if categoria:
        query = query.filter(Libro.categoria.ilike(f'%{categoria}%'))
    if autor:
        query = query.filter(Libro.autor.ilike(f'%{autor}%'))
    if disponibilidad:
        if disponibilidad.lower() == 'true':
            query = query.filter(Libro.cantidad_disponible > 0)
        elif disponibilidad.lower() == 'false':
            query = query.filter(Libro.cantidad_disponible == 0)
    if search:
        query = query.filter(
            (Libro.titulo.ilike(f'%{search}%')) | 
            (Libro.autor.ilike(f'%{search}%')) | 
            (Libro.isbn.ilike(f'%{search}%'))
        )
        
    libros = query.all()
    schema = LibroSchema(many=True)
    return jsonify({
        "status": "success",
        "message": "Libros obtenidos exitosamente",
        "data": schema.dump(libros)
    }), 200

@libros_bp.route('/<int:id>', methods=['GET'])
def get_libro(id):
    libro = Libro.query.filter_by(id=id).first()
    if not libro or libro.estado == 'de baja':
        return jsonify({"status": "error", "message": "Libro no encontrado"}), 404
        
    schema = LibroSchema()
    return jsonify({
        "status": "success",
        "message": "Libro obtenido exitosamente",
        "data": schema.dump(libro)
    }), 200

@libros_bp.route('', methods=['POST'])
@admin_required()
def create_libro():
    schema = LibroSchema()
    errors = schema.validate(request.json or {})
    if errors:
        return jsonify({"status": "error", "message": "Datos de entrada inválidos", "errors": errors}), 400
        
    data = schema.load(request.json or {})
    
    # Check duplicate ISBN
    if Libro.query.filter_by(isbn=data['isbn']).first():
        return jsonify({"status": "error", "message": "Ya existe un libro registrado con ese ISBN"}), 409
        
    cantidad_total = data['cantidad_total']
    nuevo_libro = Libro(
        titulo=data['titulo'],
        autor=data['autor'],
        isbn=data['isbn'],
        categoria=data['categoria'],
        editorial=data.get('editorial'),
        ano=data.get('ano'),
        cantidad_total=cantidad_total,
        cantidad_disponible=cantidad_total,
        estado='disponible' if cantidad_total > 0 else 'agotado'
    )
    
    db.session.add(nuevo_libro)
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "message": "Libro registrado exitosamente",
        "data": schema.dump(nuevo_libro)
    }), 201

@libros_bp.route('/<int:id>', methods=['PUT'])
@admin_required()
def update_libro(id):
    libro = Libro.query.filter_by(id=id).first()
    if not libro or libro.estado == 'de baja':
        return jsonify({"status": "error", "message": "Libro no encontrado o dado de baja"}), 404
        
    schema = LibroSchema(partial=True)
    errors = schema.validate(request.json or {})
    if errors:
        return jsonify({"status": "error", "message": "Datos de entrada inválidos", "errors": errors}), 400
        
    data = schema.load(request.json or {})
    
    # Check ISBN uniqueness if changed
    if 'isbn' in data and data['isbn'] != libro.isbn:
        if Libro.query.filter_by(isbn=data['isbn']).first():
            return jsonify({"status": "error", "message": "Ya existe otro libro registrado con ese ISBN"}), 409
            
    # Update text fields
    for field in ['titulo', 'autor', 'isbn', 'categoria', 'editorial', 'ano']:
        if field in data:
            setattr(libro, field, data[field])
            
    # If total quantity changed, update availability accordingly
    if 'cantidad_total' in data:
        old_total = libro.cantidad_total
        new_total = data['cantidad_total']
        diff = new_total - old_total
        
        # Calculate new available stock
        libro.cantidad_total = new_total
        libro.cantidad_disponible = max(0, libro.cantidad_disponible + diff)
        
        # Recalculate status
        if libro.cantidad_disponible > 0:
            libro.estado = 'disponible'
        else:
            libro.estado = 'agotado'
            
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "message": "Libro actualizado exitosamente",
        "data": LibroSchema().dump(libro)
    }), 200

@libros_bp.route('/<int:id>', methods=['DELETE'])
@admin_required()
def delete_libro(id):
    libro = Libro.query.filter_by(id=id).first()
    if not libro or libro.estado == 'de baja':
        return jsonify({"status": "error", "message": "Libro no encontrado o ya dado de baja"}), 404
        
    # Logical delete
    libro.estado = 'de baja'
    libro.cantidad_disponible = 0
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "message": "Libro dado de baja exitosamente (baja lógica)"
    }), 200

@libros_bp.route('/<int:id>/cola-reservas', methods=['GET'])
@admin_required()
def get_cola_reservas(id):
    from models.reserva import Reserva
    from schemas import ReservaResponseSchema
    
    libro = Libro.query.filter_by(id=id).first()
    if not libro or libro.estado == 'de baja':
        return jsonify({"status": "error", "message": "Libro no encontrado"}), 404
        
    cola = Reserva.query.filter_by(id_libro=id, estado='pendiente').order_by(Reserva.posicion_en_cola).all()
    schema = ReservaResponseSchema(many=True)
    return jsonify({
        "status": "success",
        "message": "Cola de reservas obtenida exitosamente",
        "data": schema.dump(cola)
    }), 200

