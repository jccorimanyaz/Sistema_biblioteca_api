from marshmallow import Schema, fields

class PrestamoCrearSchema(Schema):
    id_libro = fields.Int(required=True)
    id_usuario = fields.Int(required=False)  # Admin can specify, Readers use their own ID from token

class PrestamoResponseSchema(Schema):
    id = fields.Int(dump_only=True)
    id_libro = fields.Int(dump_only=True)
    id_usuario = fields.Int(dump_only=True)
    fecha_prestamo = fields.DateTime(dump_only=True)
    fecha_devolucion_estimada = fields.DateTime(dump_only=True)
    fecha_devolucion_real = fields.DateTime(dump_only=True)
    estado = fields.Str(dump_only=True)
    multa_generada = fields.Float(dump_only=True)
