from marshmallow import Schema, fields, validate

class UsuarioRegistroSchema(Schema):
    nombre = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True, validate=validate.Length(max=100))
    password = fields.Str(required=True, validate=validate.Length(min=6))
    rol = fields.Str(validate=validate.OneOf(['admin', 'lector']), load_default='lector')

class UsuarioLoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

class UsuarioResponseSchema(Schema):
    id = fields.Int(dump_only=True)
    nombre = fields.Str(dump_only=True)
    email = fields.Email(dump_only=True)
    rol = fields.Str(dump_only=True)
    fecha_registro = fields.DateTime(dump_only=True)
    estado = fields.Str(dump_only=True)

class UsuarioUpdateSchema(Schema):
    nombre = fields.Str(validate=validate.Length(min=1, max=100))
    email = fields.Email(validate=validate.Length(max=100))
    rol = fields.Str(validate=validate.OneOf(['admin', 'lector']))
    estado = fields.Str(validate=validate.OneOf(['activo', 'suspendido']))
