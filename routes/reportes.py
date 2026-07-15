from flask import Blueprint, jsonify
from sqlalchemy import func
from datetime import datetime
from models import db
from models.libro import Libro
from models.prestamo import Prestamo
from models.usuario import Usuario
from models.multa import Multa
from schemas import LibroSchema, UsuarioResponseSchema, PrestamoResponseSchema
from utils.auth_decorators import admin_required

reportes_bp = Blueprint('reportes', __name__, url_prefix='/reportes')

@reportes_bp.route('/libros-mas-prestados', methods=['GET'])
@admin_required()
def libros_mas_prestados():
    """
    Returns a top list of books sorted by total times they have been borrowed.
    """
    results = db.session.query(
        Libro,
        func.count(Prestamo.id).label('total_prestamos')
    ).join(Prestamo, Libro.id == Prestamo.id_libro)\
     .group_by(Libro.id)\
     .order_by(func.count(Prestamo.id).desc())\
     .limit(10).all()
     
    libro_schema = LibroSchema()
    data = []
    for libro, total in results:
        data.append({
            "libro": libro_schema.dump(libro),
            "total_prestamos": total
        })
        
    return jsonify({
        "status": "success",
        "message": "Reporte de libros más prestados obtenido",
        "data": data
    }), 200

@reportes_bp.route('/usuarios-con-multas', methods=['GET'])
@admin_required()
def usuarios_con_multas():
    """
    Returns a list of readers who have pending (unpaid) fines, including the total amount due.
    """
    results = db.session.query(
        Usuario,
        func.sum(Multa.monto).label('total_pendiente')
    ).join(Multa, Usuario.id == Multa.id_usuario)\
     .filter(Multa.estado == 'pendiente')\
     .group_by(Usuario.id)\
     .order_by(func.sum(Multa.monto).desc()).all()
     
    usuario_schema = UsuarioResponseSchema()
    data = []
    for usuario, total in results:
        data.append({
            "usuario": usuario_schema.dump(usuario),
            "total_pendiente": float(total)
        })
        
    return jsonify({
        "status": "success",
        "message": "Reporte de usuarios con multas pendientes obtenido",
        "data": data
    }), 200

@reportes_bp.route('/prestamos-vencidos', methods=['GET'])
@admin_required()
def prestamos_vencidos():
    """
    Returns all active loans where the expected return date has already passed.
    """
    now = datetime.utcnow()
    vencidos = Prestamo.query.filter(
        Prestamo.estado == 'activo',
        Prestamo.fecha_devolucion_estimada < now
    ).all()
    
    schema = PrestamoResponseSchema(many=True)
    return jsonify({
        "status": "success",
        "message": "Reporte de préstamos vencidos obtenido",
        "data": schema.dump(vencidos)
    }), 200
