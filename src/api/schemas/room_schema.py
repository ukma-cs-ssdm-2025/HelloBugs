from marshmallow import Schema, fields, validate, EXCLUDE
from enum import Enum


class RoomType(str, Enum):
    ECONOMY = "ECONOMY"
    STANDARD = "STANDARD"
    DELUXE = "DELUXE"


class RoomStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    MAINTENANCE = "MAINTENANCE"


# for responses
class RoomOutSchema(Schema):
    class Meta:
        ordered = True

    id = fields.Int(dump_only=True, metadata={"description": "Unique room ID", "example": 1})
    room_number = fields.Str(required=True, metadata={"description": "Room number", "example": "101"})
    room_type = fields.Str(required=True, validate=validate.OneOf([t.value for t in RoomType]), metadata={"description": "Room type", "example": "STANDARD"})
    max_guest = fields.Int(required=True, metadata={"description": "Max guests", "example": 2})
    base_price = fields.Decimal(required=True, as_string=True, metadata={"description": "Price per night", "example": "120.00"})
    status = fields.Str(required=True, validate=validate.OneOf([s.value for s in RoomStatus]), metadata={"description": "Room status", "example": "AVAILABLE"})
    description = fields.Str(required=False, metadata={"description": "Room description", "example": "Spacious room with city view"})
    floor = fields.Int(required=True, metadata={"description": "Floor number", "example": 2})
    size_sqm = fields.Decimal(required=False, as_string=True, metadata={"description": "Room size (m²)", "example": "25.0"})
    main_photo_url = fields.Str(required=False, metadata={"description": "Main photo URL", "example": "https://example.com/rooms/101-main.jpg"})
    photo_urls = fields.List(fields.Str(), required=False, metadata={"description": "Additional photo URLs", "example": ["https://example.com/rooms/101-1.jpg"]})


# for create/update input
class RoomInSchema(Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    room_number = fields.Str(required=True, validate=validate.Length(min=1, max=10), metadata={"description": "Unique room number", "example": "101"})
    room_type = fields.Str(required=True, validate=validate.OneOf([t.value for t in RoomType]), metadata={"description": "Room type", "example": "STANDARD"})
    max_guest = fields.Int(required=True, validate=validate.Range(min=1, max=10), metadata={"description": "Max guests (1-10)", "example": 2})
    base_price = fields.Decimal(required=True, as_string=True, validate=validate.Range(min=0), metadata={"description": "Base price per night", "example": "120.00"})
    status = fields.Str(required=True, validate=validate.OneOf([s.value for s in RoomStatus]), metadata={"description": "Room status", "example": "AVAILABLE"})
    description = fields.Str(required=False, validate=validate.Length(min=10, max=1000), metadata={"description": "Room description", "example": "Comfortable standard room"})
    floor = fields.Int(required=True, validate=validate.Range(min=1, max=50), metadata={"description": "Floor number", "example": 2})
    size_sqm = fields.Decimal(required=False, as_string=True, validate=validate.Range(min=10, max=500), metadata={"description": "Room size (m²)", "example": "25.0"})
    main_photo_url = fields.Str(required=False, validate=validate.URL(), metadata={"description": "Main photo URL", "example": "https://example.com/rooms/101-main.jpg"})
    photo_urls = fields.List(fields.Str(validate=validate.URL()), required=False, load_default=list, metadata={"description": "Photo URLs", "example": ["https://example.com/rooms/101-1.jpg"]})


# for PATCH (partial update)
class RoomPatchSchema(Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    room_number = fields.Str(validate=validate.Length(min=1, max=10), metadata={"description": "Room number", "example": "101"})
    room_type = fields.Str(validate=validate.OneOf([t.value for t in RoomType]), metadata={"description": "Room type", "example": "STANDARD"})
    max_guest = fields.Int(validate=validate.Range(min=1, max=10), metadata={"description": "Max guests", "example": 3})
    base_price = fields.Decimal(as_string=True, validate=validate.Range(min=0), metadata={"description": "Base price per night", "example": "150.00"})
    status = fields.Str(validate=validate.OneOf([s.value for s in RoomStatus]), metadata={"description": "Room status", "example": "MAINTENANCE"})
    description = fields.Str(validate=validate.Length(min=10, max=1000), metadata={"description": "Description", "example": "Updated description"})
    floor = fields.Int(validate=validate.Range(min=1, max=50), metadata={"description": "Floor number", "example": 2})
    size_sqm = fields.Decimal(as_string=True, validate=validate.Range(min=10, max=500), metadata={"description": "Room size (m²)", "example": "25.0"})
    main_photo_url = fields.Str(validate=validate.URL(), metadata={"description": "Main photo URL", "example": "https://example.com/rooms/101-main.jpg"})
    photo_urls = fields.List(fields.Str(validate=validate.URL()), metadata={"description": "Photo URLs list", "example": ["https://example.com/rooms/101-1.jpg"]})
