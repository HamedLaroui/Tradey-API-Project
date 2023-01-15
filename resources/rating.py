import uuid
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from schemas import RatingSchema
from sqlalchemy.exc import SQLAlchemyError

from models import RatingModel, UserModel, TradeResponseModel
from db import db

blp = Blueprint("Ratings", "ratings", description="Operations on ratings")


@blp.route("/ratings/<string:rating_id>")
class Rating(MethodView):
    @blp.response(200, RatingSchema)
    def get(self, rating_id):
        try:
            rating = RatingModel.query.filter_by(rating_id=rating_id).one()
            return rating
        except:
            abort(404, message="Rating not found.")

    def delete(self, rating_id):
        rating = RatingModel.query.filter_by(rating_id=rating_id).first()
        if rating is None:
            abort(404, message="Rating not found.")
        db.session.delete(rating)
        db.session.commit()
        return {"message": "Rating deleted."}

@blp.route("/ratings")
class TradeRequest(MethodView):
    @blp.response(200, RatingSchema(many=True))
    def get(self):
        rating = RatingModel.query.all()
        if not rating:
            abort(404, message="No trade requests found.")
        return rating


    @blp.arguments(RatingSchema)
    @blp.response(201, RatingSchema)
    def post(self, rating_data):
        response_id = rating_data.get("response_id")
        user = UserModel.query.filter_by(username=rating_data["username"]).first()
        if not user:
            abort(401, message="Invalid username.")
        response = TradeResponseModel.query.get(response_id)
        if not response:
            abort(404, message="Trade response not found.")
        if user.username != response.username and user.username != response.to:
            abort(401, message="You are not authorized to rate this trade.")
        rating_id = uuid.uuid4().hex
        rating = RatingModel(**rating_data, rating_id=rating_id)
        try:
          db.session.add(rating)
          db.session.commit()
        except SQLAlchemyError:
            abort(500, message="Oops an error occured, please try again")
        return rating

