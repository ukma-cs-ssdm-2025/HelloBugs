from marshmallow import Schema, fields, validate, EXCLUDE


class AmenityOutSchema(Schema):
    class Meta:
        ordered = True

    id = fields.Int(dump_only=True, attribute="amenity_id")
    amenity_name = fields.Str(required=True)
    icon_url = fields.Str(required=False, allow_none=True)


class AmenityInSchema(Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    amenity_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    icon_url = fields.Str(required=False, allow_none=True, validate=validate.URL())


class AmenityPatchSchema(Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    amenity_name = fields.Str(validate=validate.Length(min=1, max=100))
    icon_url = fields.Str(allow_none=True, validate=validate.URL())