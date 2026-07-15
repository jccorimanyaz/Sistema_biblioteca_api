from marshmallow import Schema, fields, validate

class LibroSchema(Schema):
    id = fields.Int(dump_only=True)
    titulo = fields.Str(required=True, validate=validate.Length(min=1, max=150))
    autor = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    isbn = fields.Str(required=True, validate=validate.Length(min=1, max=30))
    categoria = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    editorial = fields.Str(load_default=None, validate=validate.Length(max=100))
    ano = fields.Int(load_default=None)
    cantidad_total = fields.Int(required=True, validate=validate.Range(min=0))
    cantidad_disponible = fields.Int(dump_only=True)
    estado = fields.Str(validate=validate.OneOf(['disponible', 'agotado', 'de baja']), dump_only=True)
