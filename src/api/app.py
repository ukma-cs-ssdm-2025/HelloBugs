from flask import Flask, render_template
from flask_smorest import Api
from flask_cors import CORS
from src.api.routes.users import blp as users_blp
from src.api.routes.rooms import blp as rooms_blp
from src.api.routes.bookings import blp as bookings_blp
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR) 

template_dir = os.path.join(PARENT_DIR, 'templates')
static_dir = os.path.join(PARENT_DIR, 'static')

app = Flask(__name__, 
            template_folder=template_dir,
            static_folder=static_dir)

CORS(app)
app.config["API_TITLE"] = "Hotel Reservation API"
app.config["API_VERSION"] = "1.0"
app.config["API_PREFIX"] = "/api/v1"
app.config["OPENAPI_VERSION"] = "3.0.3"
app.config["OPENAPI_URL_PREFIX"] = "/"
app.config["OPENAPI_JSON_PATH"] = "openapi.json"
app.config["OPENAPI_SWAGGER_UI_PATH"] = "/api-docs"
app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

api = Api(app)

api.register_blueprint(users_blp)
api.register_blueprint(rooms_blp)
api.register_blueprint(bookings_blp)


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

if __name__ == "__main__":
    app.run(port=3000, debug=True)
