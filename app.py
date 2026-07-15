from flask import Flask, jsonify
from config import Config
from models import db
from models.usuario import Usuario
from flask_jwt_extended import JWTManager
from marshmallow import ValidationError

# Import Blueprints
from routes import (
    auth_bp,
    libros_bp,
    usuarios_bp,
    prestamos_bp,
    reservas_bp,
    multas_bp,
    reportes_bp
)

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize DB
    db.init_app(app)
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    # Configure JWT user lookup loader
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return Usuario.query.get(int(identity))
        
    # Custom JWT Error Handlers for consistent JSON responses
    @jwt.unauthorized_loader
    def my_unauthorized_callback(err_str):
        return jsonify({
            "status": "error",
            "message": "Falta el token de autenticación o es inválido",
            "error_detail": err_str
        }), 401

    @jwt.expired_token_loader
    def my_expired_token_callback(jwt_header, jwt_data):
        return jsonify({
            "status": "error",
            "message": "El token ha expirado. Por favor, inicie sesión de nuevo."
        }), 401

    @jwt.invalid_token_loader
    def my_invalid_token_callback(err_str):
        return jsonify({
            "status": "error",
            "message": "El token proporcionado no es válido",
            "error_detail": err_str
        }), 401
        
    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(libros_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(prestamos_bp)
    app.register_blueprint(reservas_bp)
    app.register_blueprint(multas_bp)
    app.register_blueprint(reportes_bp)
    
    # Error Handlers
    @app.errorhandler(ValidationError)
    def handle_validation_error(err):
        return jsonify({
            "status": "error",
            "message": "Error de validación en los datos de entrada",
            "errors": err.messages
        }), 400
        
    @app.errorhandler(404)
    def handle_404(err):
        return jsonify({
            "status": "error",
            "message": "Recurso no encontrado"
        }), 404
        
    @app.errorhandler(500)
    def handle_500(err):
        return jsonify({
            "status": "error",
            "message": "Ocurrió un error interno en el servidor"
        }), 500

    # Auto-create tables in SQLite database
    with app.app_context():
        db.create_all()
        
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
