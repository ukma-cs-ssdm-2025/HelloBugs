from flask import Flask, render_template, jsonify
from flask_smorest import Api
from flask_cors import CORS
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()
from src.api.routes.users import blp as users_blp
from src.api.routes.rooms import blp as rooms_blp
from src.api.routes.rooms import amenities_blp
from src.api.routes.bookings import blp as bookings_blp
from src.api.routes.auth_routes import blp as auth_blp
from src.api.routes.contacts import blp as contacts_blp
from src.api.routes.reviews import blp as reviews_blp
from src.api.auth import login_required_web, admin_required
import os
import traceback
from src.api.db import create_tables, db
from src.api.scheduler import init_scheduler, shutdown_scheduler
import atexit

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

SECRET_KEY = os.getenv('SECRET_KEY')
app.config["JWT_SECRET_KEY"] = SECRET_KEY
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)

try:
      scheduler = init_scheduler()
      logger.info("Scheduler initialized")
      atexit.register(shutdown_scheduler)
except Exception as e:
      logger.error(f"Scheduler failed: {e}")

# Security headers
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers[
        'Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "style-src-elem 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:"
        )

    if os.getenv('RAILWAY_ENVIRONMENT') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response


env = os.getenv('RAILWAY_ENVIRONMENT', 'development')
if env == 'development':
    CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'], supports_credentials=True)
    logger.info("CORS configured for development")
else:
    CORS(app, origins=[
        'https://hellobugs-hotel-staging.up.railway.app',
        'https://hellobugs-hotel-production.up.railway.app'
    ])
    logger.info(f"CORS configured for {env}")

try:
    # Initialize API
    api = Api(app)

    # Register blueprints
    api.register_blueprint(users_blp)
    api.register_blueprint(rooms_blp)
    api.register_blueprint(amenities_blp)
    api.register_blueprint(bookings_blp)
    api.register_blueprint(auth_blp)
    api.register_blueprint(contacts_blp)
    api.register_blueprint(reviews_blp)

    logger.info("API routes registered successfully")

except Exception as e:
    logger.error(f"Error initializing API: {str(e)}")
    raise

@app.teardown_appcontext
def shutdown_session(exception=None):
    db.remove()

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error("Internal server error")
    logger.error(traceback.format_exc())
    print(f"FULL TRACEBACK:\n{traceback.format_exc()}")
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

@app.route('/admin/stats')
@login_required_web
@admin_required
def admin_stats_page():
    """Сторінка статистики з фільтрами"""
    return render_template('admin_stats.html')

@app.route('/bookings')
def bookings_page():
    """Бронювання"""
    return render_template('bookings.html')

@app.route('/booking/create')
def booking_create():
    """Форма створення бронювання"""
    return render_template('booking_create.html')

@app.route('/booking/details')
def booking_details():
    """Деталі бронювання"""
    return render_template('booking_details.html')

@app.route('/users')
@login_required_web
@admin_required
def users_page():
    """Сторінка з користувачами для Admin"""
    return render_template('users.html')

@app.route('/contacts')
def contacts_page():
    """Сторінка контактів"""
    return render_template('contacts.html')

@app.route('/reviews')
def reviews_page():
    """Сторінка відгуків"""
    return render_template('reviews.html')

@app.route('/reviews/create')
def reviews_create():
    """Форма створення відгуку"""
    return render_template('review_create.html')


if __name__ == "__main__":
    create_tables()
    app.run(port=3000, debug=os.getenv('RAILWAY_ENVIRONMENT') == 'development')
