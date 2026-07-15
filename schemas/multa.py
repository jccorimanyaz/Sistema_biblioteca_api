from marshmallow import Schema, fields

class MultaResponseSchema(Schema):
    id = fields.Int(dump_only=True)
    id_usuario = fields.Int(dump_only=True)
    id_prestamo = fields.Int(dump_only=True)
    monto = fields.Float(dump_only=True)
    estado = fields.Str(dump_only=True)
    fecha_creacion = fields.DateTime(dump_only=True)
