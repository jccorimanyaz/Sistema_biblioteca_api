from models import db
from models.multa import Multa

class MultaService:
    @staticmethod
    def pagar_multa(id_multa, id_usuario, is_admin=False):
        """
        Marks a pending fine as paid, validating user ownership and status.
        """
        multa = Multa.query.get(id_multa)
        if not multa:
            return {"status": "error", "message": "Multa no encontrada", "code": 404}
            
        if not is_admin and multa.id_usuario != id_usuario:
            return {"status": "error", "message": "No tienes permisos para pagar esta multa", "code": 403}
            
        if multa.estado == 'pagada':
            return {"status": "error", "message": "La multa ya se encuentra pagada", "code": 400}
            
        multa.estado = 'pagada'
        db.session.commit()
        
        return {
            "status": "success",
            "message": "Multa pagada exitosamente",
            "data": multa.to_dict(),
            "code": 200
        }
