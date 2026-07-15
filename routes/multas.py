from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt, current_user
from models.multa import Multa
from schemas import MultaResponseSchema
from services.multa_service import MultaService
from utils.auth_decorators import active_user_required

multas_bp = Blueprint('multas', __name__, url_prefix='/multas')

@multas_bp.route('', methods=['GET'])
@active_user_required()
def get_multas():
    claims = get_jwt()
    rol = claims.get('rol')
    
    if rol == 'admin':
        multas = Multa.query.all()
    else:
        multas = Multa.query.filter_by(id_usuario=current_user.id).all()
        
    schema = MultaResponseSchema(many=True)
    return jsonify({
        "status": "success",
        "message": "Multas obtenidas exitosamente",
        "data": schema.dump(multas)
    }), 200

@multas_bp.route('/<int:id>/pagar', methods=['PUT'])
@active_user_required()
def pagar_multa(id):
    claims = get_jwt()
    rol = claims.get('rol')
    is_admin = (rol == 'admin')
    
    result = MultaService.pagar_multa(id, current_user.id, is_admin=is_admin)
    
    if result['status'] == 'error':
        return jsonify(result), result.get('code', 400)
        
    return jsonify(result), result.get('code', 200)
