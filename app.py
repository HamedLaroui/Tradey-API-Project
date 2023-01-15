import os
from flask import Flask
from flask_smorest import Api
from flask_jwt_extended import JWTManager
from db import db

import models
from resources.user import blp as UserBlueprint
from resources.game import blp as GameBlueprint
from resources.traderequest import blp as TradeRequestBlueprint
from resources.traderesponse import blp as TradeResponseBlueprint
from resources.rating import blp as RatingBlueprint

def create_app(db_url=None):
    app = Flask(__name__)

    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "Tradey REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url or os.getenv("DATABASE_URL", "sqlite:///data.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)

    api = Api(app)
    jwt = JWTManager(app)
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
       return {"message": "The token has expired."}
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
       return {"message": "Invalid access token."}
    @jwt.unauthorized_loader
    def missing_token_callback(error):
       return{"message": "Access token required."}
    with app.app_context():
        #db.drop_all()
        db.create_all()

    api.register_blueprint(UserBlueprint)
    api.register_blueprint(GameBlueprint)
    api.register_blueprint(TradeRequestBlueprint)
    api.register_blueprint(TradeResponseBlueprint)
    api.register_blueprint(RatingBlueprint)
    
    return app
