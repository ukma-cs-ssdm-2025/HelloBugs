from flask import Flask
from flask_smorest import Api
from src.api.routes.users import blp as users_blp
from src.api.routes.rooms import blp as rooms_blp
from src.api.routes.bookings import blp as bookings_blp


app = Flask(__name__)
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

if __name__ == "__main__":
    app.run(port=3000, debug=True)
