from flask import Flask, render_template, jsonify
from flask_smorest import Api
from flask_cors import CORS
from datetime import timedelta
from src.api.routes.users import blp as users_blp
from src.api.routes.rooms import blp as rooms_blp
from src.api.routes.bookings import blp as bookings_blp
from src.api.routes.auth_routes import blp as auth_blp
from src.api.auth import login_required_web, admin_required
import os
from dotenv import load_dotenv
from src.api.db import create_tables

# Load environment variables
load_dotenv()

# Set up logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR) 

template_dir = os.path.join(PARENT_DIR, 'templates')
static_dir = os.path.join(PARENT_DIR, 'static')

app = Flask(__name__, 
            template_folder=template_dir,
            static_folder=static_dir)

# Configuration
app.config["API_TITLE"] = "Hotel Reservation API"
app.config["API_VERSION"] = "1.0"
app.config["API_PREFIX"] = "/api/v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_JSON_PATH"] = "openapi.json"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/api-docs"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
app.config["JWT_SECRET_KEY"] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)

# Enable CORS
CORS(app)

try:
    # Initialize API
    api = Api(app)
    
    # Register blueprints
    api.register_blueprint(users_blp)
    api.register_blueprint(rooms_blp)
    api.register_blueprint(bookings_blp)
    api.register_blueprint(auth_blp)
    
    logger.info("API routes registered successfully")
    
except Exception as e:
    logger.error(f"Error initializing API: {str(e)}")
    raise

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server Error: {str(error)}")
    return jsonify({'message': 'Internal server error'}), 500


@app.route('/')
def index():
    """Головна сторінка"""
    return render_template('index.html')

@app.route('/rooms')
def rooms_page():
    """Каталог номерів"""
    return render_template('rooms.html')

@app.route('/login')
def login_page():
    """Вхід в систему"""
    return render_template('login.html')

@app.route('/register')
def register_page():
    """Реєстрація в системі"""
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Вихід з системи"""
    # Clear any server-side session data if needed
    return render_template('index.html')

@app.route('/profile')
def profile():
    """Профіль користувача"""
    return render_template('profile.html')

@app.route('/admin')
@login_required_web
@admin_required
def admin_panel():
    """Адмін панель"""
    from flask import g
    return render_template('admin.html', user=g.current_user)

@app.route('/booking')
def bookings_page():
    """Бронювання"""
    return render_template('bookings.html')

@app.route('/booking/create')
def booking_create():
    """Форма створення бронювання"""
    return render_template('booking_create.html')

if __name__ == "__main__":
    # Create tables if they don't exist
    create_tables()
    app.run(port=3000, debug=True)
