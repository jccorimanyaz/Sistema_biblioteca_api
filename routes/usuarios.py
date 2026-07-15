from flask import Blueprint, request, jsonify
from models import db
from models.usuario import Usuario
from models.prestamo import Prestamo
from schemas import UsuarioResponseSchema, UsuarioUpdateSchema
from utils.auth_decorators import admin_required

usuarios_bp = Blueprint('usuarios', __name__, url_prefix='/usuarios')

@usuarios_bp.route('', methods=['GET'])
@admin_required()
def get_usuarios():
    usuarios = Usuario.query.all()
    schema = UsuarioResponseSchema(many=True)
    return jsonify({
        "status": "success",
        "message": "Usuarios obtenidos exitosamente",
        "data": schema.dump(usuarios)
    }), 200

@usuarios_bp.route('/<int:id>', methods=['GET'])
@admin_required()
def get_usuario(id):
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
        
    schema = UsuarioResponseSchema()
    return jsonify({
        "status": "success",
        "message": "Usuario obtenido exitosamente",
        "data": schema.dump(usuario)
    }), 200

@usuarios_bp.route('/<int:id>', methods=['PUT'])
@admin_required()
def update_usuario(id):
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
        
    schema = UsuarioUpdateSchema()
    errors = schema.validate(request.json or {})
    if errors:
        return jsonify({"status": "error", "message": "Datos de entrada inválidos", "errors": errors}), 400
        
    data = schema.load(request.json or {})
    
    # Check email duplication
    if 'email' in data and data['email'] != usuario.email:
        if Usuario.query.filter_by(email=data['email']).first():
            return jsonify({"status": "error", "message": "El correo electrónico ya está registrado por otro usuario"}), 409
            
    # Apply changes
    for field in ['nombre', 'email', 'rol', 'estado']:
        if field in data:
            setattr(usuario, field, data[field])
            
    db.session.commit()
    
    response_schema = UsuarioResponseSchema()
    return jsonify({
        "status": "success",
        "message": "Usuario actualizado exitosamente",
        "data": response_schema.dump(usuario)
    }), 200

@usuarios_bp.route('/<int:id>', methods=['DELETE'])
@admin_required()
def delete_usuario(id):
    usuario = Usuario.query.get(id)
    if not usuario:
        return jsonify({"status": "error", "message": "Usuario no encontrado"}), 404
        
    # Check if user has active loans
    active_loans = Prestamo.query.filter_by(id_usuario=id, estado='activo').first()
    if active_loans:
        return jsonify({
            "status": "error",
            "message": "No se puede eliminar el usuario porque tiene préstamos activos. Considere suspenderlo."
        }), 400
        
    db.session.delete(usuario)
    db.session.commit()
    
    return jsonify({
        "status": "success",
        "message": "Usuario eliminado de la base de datos exitosamente"
    }), 200
