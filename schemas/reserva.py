from marshmallow import Schema, fields

class ReservaCrearSchema(Schema):
    id_libro = fields.Int(required=True)
    id_usuario = fields.Int(required=False)  # Admin can specify, Readers use their own ID from token

class ReservaResponseSchema(Schema):
    id = fields.Int(dump_only=True)
    id_libro = fields.Int(dump_only=True)
    id_usuario = fields.Int(dump_only=True)
    fecha_reserva = fields.DateTime(dump_only=True)
    estado = fields.Str(dump_only=True)
    posicion_en_cola = fields.Int(dump_only=True)
    notificado = fields.Boolean(dump_only=True)
    fecha_limite_retiro = fields.DateTime(dump_only=True)
