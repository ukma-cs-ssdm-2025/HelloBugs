from marshmallow import Schema, fields, validate


class ReviewInSchema(Schema):
    """Schema for creating a new review"""
    room_id = fields.Integer(
        required=True,
        error_messages={
            'required': 'Необхідно обрати номер',
            'invalid': 'ID номера має бути числом'
        }
    )
    rating = fields.Integer(
        required=True,
        validate=validate.Range(min=1, max=5),
        error_messages={
            'required': 'Рейтинг є обов\'язковим',
            'invalid': 'Рейтинг має бути числом від 1 до 5'
        }
    )
    comment = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=1000),
        error_messages={
            'invalid': 'Коментар не може перевищувати 1000 символів'
        }
    )


class ReviewOutSchema(Schema):
    """Schema for review output"""
    review_id = fields.Integer(dump_only=True)
    user_id = fields.Integer(dump_only=True)
    room_id = fields.Integer(dump_only=True)
    rating = fields.Integer()
    comment = fields.String(allow_none=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    user = fields.Nested(
        {
            'first_name': fields.String(),
            'last_name': fields.String()
        },
        dump_only=True
    )
    room = fields.Nested(
        {
            'room_number': fields.String(),
            'room_type': fields.String()
        },
        dump_only=True
    )


class ReviewPatchSchema(Schema):
    """Schema for partial review update"""
    rating = fields.Integer(
        required=False,
        validate=validate.Range(min=1, max=5)
    )
    comment = fields.String(
        required=False,
        allow_none=True,
        validate=validate.Length(max=1000)
    )
    room_id = fields.Integer(required=False, allow_none=True)
