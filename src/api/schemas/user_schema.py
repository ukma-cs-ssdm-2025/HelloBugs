from marshmallow import Schema, fields, validate, EXCLUDE
from enum import Enum

class UserRole(str, Enum):
    GUEST = "GUEST"
    STAFF = "STAFF"
    ADMIN = "ADMIN"

# for responses (no password)
class UserOutSchema(Schema):
    class Meta:
        ordered = True

    id = fields.Int(dump_only=True, metadata={"description": "Unique user ID", "example": 1})
    first_name = fields.Str(required=True, metadata={"description": "User's first name", "example": "John"})
    last_name = fields.Str(required=True, metadata={"description": "User's last name", "example": "Doe"})
    email = fields.Email(required=True, metadata={"description": "User email", "example": "guest@example.com"})
    phone = fields.Str(required=True, metadata={"description": "Phone in international format", "example": "+380501234567"})
    role = fields.Str(required=True, validate=validate.OneOf([r.value for r in UserRole]), metadata={"description": "User role"})
    created_at = fields.DateTime(dump_only=True, metadata={"description": "Creation timestamp", "example": "2025-10-06T19:27:00Z"})

# for create/update input (password required)
class UserInSchema(Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    first_name = fields.Str(required=True, validate=validate.Length(min=1), metadata={"description": "User's first name", "example": "John"})
    last_name = fields.Str(required=True, validate=validate.Length(min=1), metadata={"description": "User's last name", "example": "Doe"})
    email = fields.Email(required=True, metadata={"description": "Email address", "example": "guest@example.com"})
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=8), metadata={"description": "Password (min 8 chars). Will not be returned in responses.", "example": "strongP@ssw0rd"})
    phone = fields.Str(required=True, validate=validate.Regexp(r'^\+?[\d\s\-\(\)]+$'), metadata={"description": "Phone number", "example": "+380501234567"})
    role = fields.Str(required=True, validate=validate.OneOf([r.value for r in UserRole]), metadata={"description": "User role", "example": "GUEST"})

# for PATCH (partial)
class UserPatchSchema(Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    first_name = fields.Str(validate=validate.Length(min=1), metadata={"description": "User's first name", "example": "John"})
    last_name = fields.Str(validate=validate.Length(min=1), metadata={"description": "User's last name", "example": "Doe"})
    email = fields.Email(metadata={"description": "Email address", "example": "guest@example.com"})
    password = fields.Str(load_only=True, validate=validate.Length(min=8), metadata={"description": "Password (min 8 chars). Will not be returned in responses.", "example": "strongP@ssw0rd"})
    phone = fields.Str(validate=validate.Regexp(r'^\+?[\d\s\-\(\)]+$'), metadata={"description": "Phone number", "example": "+380501234567"})
    role = fields.Str(validate=validate.OneOf([r.value for r in UserRole]), metadata={"description": "User role", "example": "GUEST"})
