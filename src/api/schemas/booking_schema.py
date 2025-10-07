from marshmallow import Schema, fields, validate, validates_schema, EXCLUDE, validates, ValidationError
from enum import Enum


class BookingStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# for responses
class BookingOutSchema(Schema):
    class Meta:
        ordered = True

    id = fields.Int(dump_only=True, metadata={"description": "Unique booking ID", "example": 1})
    booking_code = fields.Str(required=True, metadata={"description": "Unique booking code", "example": "BK001ABC"})
    user_id = fields.Int(allow_none=True, metadata={"description": "Registered user ID (null for guest)", "example": 1})
    guest_email = fields.Email(required=True, metadata={"description": "Guest email", "example": "guest@example.com"})
    guest_first_name = fields.Str(required=True, metadata={"description": "Guest first name", "example": "John"})
    guest_last_name = fields.Str(required=True, metadata={"description": "Guest last name", "example": "Doe"})
    guest_phone = fields.Str(required=True, metadata={"description": "Guest phone", "example": "+380501234567"})
    room_id = fields.Int(required=True, metadata={"description": "Booked room ID", "example": 1})
    check_in_date = fields.Date(required=True, metadata={"description": "Check-in date", "example": "2025-10-15"})
    check_out_date = fields.Date(required=True, metadata={"description": "Check-out date", "example": "2025-10-18"})
    special_requests = fields.Str(allow_none=True, metadata={"description": "Guest's special requests", "example": "Late check-in"})
    status = fields.Str(required=True, validate=validate.OneOf([s.value for s in BookingStatus]), metadata={"description": "Booking status", "example": "ACTIVE"})
    created_at = fields.DateTime(dump_only=True, metadata={"description": "Created at", "example": "2025-10-06T19:27:00Z"})
    updated_at = fields.DateTime(dump_only=True, metadata={"description": "Updated at", "example": "2025-10-07T10:15:00Z"})


# for create/update input
class BookingInSchema(Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    user_id = fields.Int(allow_none=True, metadata={"description": "User ID (optional for guests)", "example": 1})
    guest_email = fields.Email(required=True, metadata={"description": "Guest email", "example": "guest@example.com"})
    guest_first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100), metadata={"description": "Guest first name", "example": "John"})
    guest_last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100), metadata={"description": "Guest last name", "example": "Doe"})
    guest_phone = fields.Str(required=True, validate=validate.Regexp(r'^\+?[\d\s\-\(\)]+$'), metadata={"description": "Guest phone number", "example": "+380501234567"})
    room_id = fields.Int(required=True, validate=validate.Range(min=1), metadata={"description": "Room ID", "example": 1})
    check_in_date = fields.Date(required=True, metadata={"description": "Check-in date", "example": "2025-10-15"})
    check_out_date = fields.Date(required=True, metadata={"description": "Check-out date", "example": "2025-10-18"})
    special_requests = fields.Str(allow_none=True, validate=validate.Length(max=1000), metadata={"description": "Special requests", "example": "Extra towels"})

    @validates_schema
    def validate_dates(self, data, **kwargs):
        if data.get("check_out_date") and data.get("check_in_date"):
            if data["check_out_date"] <= data["check_in_date"]:
                raise ValidationError("Check-out date must be after check-in date")


# for PATCH (partial update)
class BookingPatchSchema(Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    guest_email = fields.Email(metadata={"description": "Guest email", "example": "new@example.com"})
    guest_first_name = fields.Str(validate=validate.Length(min=1, max=100), metadata={"description": "Guest first name", "example": "John"})
    guest_last_name = fields.Str(validate=validate.Length(min=1, max=100), metadata={"description": "Guest last name", "example": "Doe"})
    guest_phone = fields.Str(validate=validate.Regexp(r'^\+?[\d\s\-\(\)]+$'), metadata={"description": "Guest phone", "example": "+380501234567"})
    room_id = fields.Int(validate=validate.Range(min=1), metadata={"description": "Room ID", "example": 2})
    check_in_date = fields.Date(metadata={"description": "New check-in date", "example": "2025-10-16"})
    check_out_date = fields.Date(metadata={"description": "New check-out date", "example": "2025-10-19"})
    special_requests = fields.Str(validate=validate.Length(max=1000), metadata={"description": "Updated requests", "example": "Late checkout"})
    status = fields.Str(validate=validate.OneOf([s.value for s in BookingStatus]), metadata={"description": "Booking status", "example": "CANCELLED"})
