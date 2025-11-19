from flask.views import MethodView
from flask_smorest import Blueprint
from flask import jsonify, g
from src.api.db import db
from src.api.services.contact_service import get_contact_info, update_contact_info
from src.api.auth import admin_required, token_required

blp = Blueprint('contacts', __name__, url_prefix='/api/v1/contacts', description='Contact information management')


@blp.route('/')
class ContactInfo(MethodView):
    
    def get(self):
        """Отримати контактну інформацію (публічний доступ)"""
        try:
            contact = get_contact_info(db)
            return jsonify({
                'id': contact.id,
                'hotel_name': contact.hotel_name,
                'address': contact.address,
                'phone': contact.phone,
                'email': contact.email,
                'schedule': contact.schedule,
                'description': contact.description
            }), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500
    
    @token_required
    @admin_required
    def put(self):
        """Оновити контактну інформацію (тільки для адміна)"""
        from flask import request
        try:
            data = request.get_json()
            contact = update_contact_info(db, data)
            return jsonify({
                'id': contact.id,
                'hotel_name': contact.hotel_name,
                'address': contact.address,
                'phone': contact.phone,
                'email': contact.email,
                'schedule': contact.schedule,
                'description': contact.description
            }), 200
        except Exception as e:
            return jsonify({'message': str(e)}), 500
