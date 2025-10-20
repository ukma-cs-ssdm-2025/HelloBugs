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

    booking_code = fields.Str(required=True, metadata={"description": "Unique booking code", "example": "BK001ABC"})
    user_id = fields.Int(allow_none=True, metadata={"description": "Registered user ID (null for guest)", "example": 1})
    room_id = fields.Int(required=True, metadata={"description": "Booked room ID", "example": 1})
    check_in_date = fields.Date(required=True, metadata={"description": "Check-in date", "example": "2025-10-15"})
    check_out_date = fields.Date(required=True, metadata={"description": "Check-out date", "example": "2025-10-18"})
    special_requests = fields.Str(allow_none=True, metadata={"description": "Guest's special requests", "example": "Late check-in"})
    status = fields.Str(required=True, attribute="status.value", metadata={"description": "Booking status", "example": "ACTIVE"})
    created_at = fields.DateTime(dump_only=True, metadata={"description": "Created at", "example": "2025-10-06T19:27:00Z"})
    updated_at = fields.DateTime(dump_only=True, metadata={"description": "Updated at", "example": "2025-10-07T10:15:00Z"})

# for create/update input
class BookingInSchema(Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    user_id = fields.Int(allow_none=True, load_default=None,
                         metadata={"description": "User ID (optional - will be taken from JWT token if authenticated)",
                                   "example": 1})
    room_id = fields.Int(required=True, validate=validate.Range(min=1),
                         metadata={"description": "Room ID", "example": 1})
    check_in_date = fields.Date(required=True, metadata={"description": "Check-in date", "example": "2025-10-15"})
    check_out_date = fields.Date(required=True, metadata={"description": "Check-out date", "example": "2025-10-18"})
    special_requests = fields.Str(allow_none=True, validate=validate.Length(max=1000),
                                  metadata={"description": "Special requests", "example": "Extra towels"})

    # Додаємо поля для гостя (якщо не залогінений)
    email = fields.Email(allow_none=True, metadata={"description": "Guest email (required if not authenticated)",
                                                    "example": "guest@example.com"})
    first_name = fields.Str(allow_none=True, validate=validate.Length(min=1),
                            metadata={"description": "Guest first name", "example": "John"})
    last_name = fields.Str(allow_none=True, validate=validate.Length(min=1),
                           metadata={"description": "Guest last name", "example": "Doe"})
    phone = fields.Str(allow_none=True, validate=validate.Regexp(r'^\+?[\d\s\-\(\)]+$'),
                       metadata={"description": "Guest phone", "example": "+380501234567"})

    @validates_schema
    def validate_booking_data(self, data):
        if data.get("check_out_date") and data.get("check_in_date"):
            if data["check_out_date"] <= data["check_in_date"]:
                raise ValidationError("Check-out date must be after check-in date")

        user_id = data.get('user_id')
        email = data.get('email')

        # Якщо немає ні user_id ні email - помилка
        if not user_id and not email:
            raise ValidationError("Either user_id (for authenticated users) or email (for guests) must be provided")

        # Якщо email передано - перевірити обов'язкові поля гостя
        if email and not user_id:
            if not data.get('first_name'):
                raise ValidationError("First name is required for guest bookings")
            if not data.get('last_name'):
                raise ValidationError("Last name is required for guest bookings")
            if not data.get('phone'):
                raise ValidationError("Phone is required for guest bookings")


# for PATCH (partial update)
class BookingPatchSchema(Schema):
    class Meta:
        unknown = EXCLUDE
        ordered = True

    room_id = fields.Int(validate=validate.Range(min=1), metadata={"description": "Room ID", "example": 2})
    check_in_date = fields.Date(metadata={"description": "New check-in date", "example": "2025-10-16"})
    check_out_date = fields.Date(metadata={"description": "New check-out date", "example": "2025-10-19"})
    special_requests = fields.Str(validate=validate.Length(max=1000), metadata={"description": "Updated requests", "example": "Late checkout"})
    status = fields.Str(validate=validate.OneOf([s.value for s in BookingStatus]), metadata={"description": "Booking status", "example": "CANCELLED"})
