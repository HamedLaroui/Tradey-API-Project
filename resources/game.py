import uuid
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from sqlalchemy.exc import SQLAlchemyError

from schemas import GameSchema
from models import GameModel, UserModel
from db import db

blp = Blueprint("Games", "games", description="Operations on games")


@blp.route("/games/<string:username>")
class Game(MethodView):
    @jwt_required()
    @blp.response(200, GameSchema(many=True))
    def get(self, username):
        current_user = get_jwt_identity()
        if current_user != username:
            abort(401, message="You are not authorized to view this user's games.")
        try:
            user = UserModel.query.filter_by(username=username).one()
            user_games = GameModel.query.filter_by(user_id=user.user_id).all()
            return user_games
        except:
            abort(404, message=f"No games found.")


@blp.route("/games/<string:username>/<string:game_id>")
class Game(MethodView):
    @jwt_required()
    @blp.response(200, GameSchema)
    def delete(self, username, game_id):
        current_user = get_jwt_identity()
        if current_user != username:
            abort(401, message="You are not authorized to delete this game.")
        game = GameModel.query.filter_by(game_id=game_id).first()
        user = UserModel.query.filter_by(username=username).first()
        if user is None:
            abort(404, message="User not found.")
        if game is None:
            abort(404, message="Game not found.")
        db.session.delete(game)
        db.session.commit()
        return {"message": "Game deleted."}
    
    
@blp.route("/game/<string:game_id>")
class Game(MethodView):
    @blp.response(200, GameSchema)
    def get(self, game_id):
        game = GameModel.query.get(game_id)
        if game is None:
            abort(404, message="No games found.")
        return game
    

@blp.route("/games")
class Game(MethodView):
    @blp.response(200, GameSchema(many=True))
    def get(self):
        games = GameModel.query.all()
        if not games:
            abort(404, message=f"There are no games in the system yet.")
        return games

    @blp.arguments(GameSchema)
    @jwt_required()
    @blp.response(201, GameSchema)
    def post(self, game_data):
        username = game_data.get("username")
        current_user = get_jwt_identity()
        if current_user != username:
            abort(401, message="Please enter your own username")
        try:
            user = UserModel.query.filter_by(username=game_data.get("username")).one()
        except:
            abort(401, message="Invalid username")
        
        game_id = uuid.uuid4().hex
        game = GameModel(user_id=user.user_id, game_id = game_id, **game_data)
        try:
            db.session.add(game)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="Oops an error occured, please try again")
        return game
