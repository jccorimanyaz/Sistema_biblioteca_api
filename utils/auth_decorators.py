from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request, current_user

def admin_required():
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("rol") != "admin":
                return jsonify({
                    "status": "error",
                    "message": "Acceso denegado. Se requieren permisos de administrador."
                }), 403
            if current_user and current_user.estado == "suspendido":
                return jsonify({
                    "status": "error",
                    "message": "Acceso denegado. El usuario se encuentra suspendido."
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def active_user_required():
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            if current_user and current_user.estado == "suspendido":
                return jsonify({
                    "status": "error",
                    "message": "Acceso denegado. El usuario se encuentra suspendido."
                }), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
