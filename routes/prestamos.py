from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, current_user
from models.prestamo import Prestamo
from schemas import PrestamoCrearSchema, PrestamoResponseSchema
from services.prestamo_service import PrestamoService
from utils.auth_decorators import active_user_required

prestamos_bp = Blueprint('prestamos', __name__, url_prefix='/prestamos')

@prestamos_bp.route('', methods=['GET'])
@active_user_required()
def get_prestamos():
    claims = get_jwt()
    rol = claims.get('rol')
    
    if rol == 'admin':
        # Admin sees all loans
        prestamos = Prestamo.query.all()
    else:
        # Lector sees only their own loans
        prestamos = Prestamo.query.filter_by(id_usuario=current_user.id).all()
        
    schema = PrestamoResponseSchema(many=True)
    return jsonify({
        "status": "success",
        "message": "Préstamos obtenidos exitosamente",
        "data": schema.dump(prestamos)
    }), 200

@prestamos_bp.route('/<int:id>', methods=['GET'])
@active_user_required()
def get_prestamo(id):
    prestamo = Prestamo.query.get(id)
    if not prestamo:
        return jsonify({"status": "error", "message": "Préstamo no encontrado"}), 404
        
    claims = get_jwt()
    rol = claims.get('rol')
    
    # Readers can only view their own loans
    if rol != 'admin' and prestamo.id_usuario != current_user.id:
        return jsonify({"status": "error", "message": "No tienes permisos para ver este préstamo"}), 403
        
    schema = PrestamoResponseSchema()
    return jsonify({
        "status": "success",
        "message": "Préstamo obtenido exitosamente",
        "data": schema.dump(prestamo)
    }), 200

@prestamos_bp.route('', methods=['POST'])
@active_user_required()
def create_prestamo():
    schema = PrestamoCrearSchema()
    errors = schema.validate(request.json or {})
    if errors:
        return jsonify({"status": "error", "message": "Datos de entrada inválidos", "errors": errors}), 400
        
    data = schema.load(request.json or {})
    id_libro = data['id_libro']
    
    claims = get_jwt()
    rol = claims.get('rol')
    
    if rol == 'admin':
        if 'id_usuario' not in data:
            return jsonify({
                "status": "error", 
                "message": "Como administrador, debes proporcionar el 'id_usuario' del lector"
            }), 400
        id_usuario = data['id_usuario']
    else:
        # Readers can only request loans for themselves
        id_usuario = current_user.id
        
    result = PrestamoService.crear_prestamo(id_libro, id_usuario)
    
    if result['status'] == 'error':
        return jsonify(result), result.get('code', 400)
        
    return jsonify(result), result.get('code', 201)

@prestamos_bp.route('/<int:id>/devolver', methods=['PUT'])
@active_user_required()
def devolver_prestamo(id):
    claims = get_jwt()
    rol = claims.get('rol')
    is_admin = (rol == 'admin')
    
    result = PrestamoService.devolver_prestamo(id, current_user.id, is_admin=is_admin)
    
    if result['status'] == 'error':
        return jsonify(result), result.get('code', 400)
        
    return jsonify(result), result.get('code', 200)
