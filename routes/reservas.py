from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt, current_user
from models.reserva import Reserva
from schemas import ReservaCrearSchema, ReservaResponseSchema
from services.reserva_service import ReservaService
from utils.auth_decorators import active_user_required

reservas_bp = Blueprint('reservas', __name__, url_prefix='/reservas')

@reservas_bp.route('', methods=['GET'])
@active_user_required()
def get_reservas():
    claims = get_jwt()
    rol = claims.get('rol')
    
    if rol == 'admin':
        reservas = Reserva.query.all()
    else:
        reservas = Reserva.query.filter_by(id_usuario=current_user.id).all()
        
    schema = ReservaResponseSchema(many=True)
    return jsonify({
        "status": "success",
        "message": "Reservas obtenidas exitosamente",
        "data": schema.dump(reservas)
    }), 200

@reservas_bp.route('', methods=['POST'])
@active_user_required()
def create_reserva():
    schema = ReservaCrearSchema()
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
        id_usuario = current_user.id
        
    result = ReservaService.crear_reserva(id_libro, id_usuario)
    
    if result['status'] == 'error':
        return jsonify(result), result.get('code', 400)
        
    return jsonify(result), result.get('code', 201)

@reservas_bp.route('/<int:id>/cancelar', methods=['PUT'])
@active_user_required()
def cancelar_reserva(id):
    claims = get_jwt()
    rol = claims.get('rol')
    is_admin = (rol == 'admin')
    
    result = ReservaService.cancelar_reserva(id, current_user.id, is_admin=is_admin)
    
    if result['status'] == 'error':
        return jsonify(result), result.get('code', 400)
        
    return jsonify(result), result.get('code', 200)
