from flask import Blueprint, request, jsonify
from models import db
from models.usuario import Usuario
from schemas import UsuarioRegistroSchema, UsuarioLoginSchema, UsuarioResponseSchema
from flask_jwt_extended import create_access_token

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    schema = UsuarioRegistroSchema()
    errors = schema.validate(request.json or {})
    if errors:
        return jsonify({"status": "error", "message": "Datos de entrada inválidos", "errors": errors}), 400
        
    data = schema.load(request.json or {})
    
    # Check if user already exists
    if Usuario.query.filter_by(email=data['email']).first():
        return jsonify({"status": "error", "message": "El correo electrónico ya está registrado"}), 409
        
    nuevo_usuario = Usuario(
        nombre=data['nombre'],
        email=data['email'],
        rol=data.get('rol', 'lector'),
        estado='activo'
    )
    nuevo_usuario.set_password(data['password'])
    
    db.session.add(nuevo_usuario)
    db.session.commit()
    
    response_schema = UsuarioResponseSchema()
    return jsonify({
        "status": "success",
        "message": "Usuario registrado exitosamente",
        "data": response_schema.dump(nuevo_usuario)
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    schema = UsuarioLoginSchema()
    errors = schema.validate(request.json or {})
    if errors:
        return jsonify({"status": "error", "message": "Datos de entrada inválidos", "errors": errors}), 400
        
    data = schema.load(request.json or {})
    
    usuario = Usuario.query.filter_by(email=data['email']).first()
    if not usuario or not usuario.check_password(data['password']):
        return jsonify({"status": "error", "message": "Credenciales incorrectas"}), 401
        
    if usuario.estado == 'suspendido':
        return jsonify({"status": "error", "message": "Acceso denegado. El usuario se encuentra suspendido."}), 403
        
    # Generate JWT
    access_token = create_access_token(
        identity=str(usuario.id),
        additional_claims={"rol": usuario.rol}
    )
    
    response_schema = UsuarioResponseSchema()
    return jsonify({
        "status": "success",
        "message": "Inicio de sesión exitoso",
        "data": {
            "token": access_token,
            "usuario": response_schema.dump(usuario)
        }
    }), 200
