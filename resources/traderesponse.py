import uuid
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from schemas import TradeResponseSchema
from models import TradeResponseModel, TradeRequestModel, UserModel
from db import db
from sqlalchemy.exc import SQLAlchemyError
from resources.traderequest import send_email 

blp = Blueprint("TradeResponses", "traderesponses", description="Operations on trade responses")


@blp.route("/traderesponses/<string:username>/sent")
class TradeRequest(MethodView):
    @jwt_required()
    @blp.response(200, TradeResponseSchema(many=True))
    def get(self, username):
        current_user = get_jwt_identity()
        if current_user != username:
            abort(401, message="Please enter your own username to view these responses.")
        user = UserModel.query.filter_by(username=username).first()
        if user is None:
            abort(404, message="Username does not exist.")
        response = TradeResponseModel.query.filter_by(username=username).all()
        if not response:
            abort(404, message="No trade responses sent from this user yet.")
        return response


@blp.route("/traderesponses/<string:username>/received")
class TradeRequest(MethodView):
    @jwt_required()
    @blp.response(200, TradeResponseSchema(many=True))
    def get(self, username):
        current_user = get_jwt_identity()
        if current_user != username:
            abort(401, message="Please enter your own username to view these responses.")
        user = UserModel.query.filter_by(username=username).first()
        if user is None:
            abort(404, message="Username does not exist.")
        response = TradeResponseModel.query.filter_by(to=username).all()
        if not response:
            abort(404, message="No trade responses received for this user yet.")
        return response
   
    @blp.route("/traderesponses/<string:username>/received/<string:response_id>")
    class TradeRequest(MethodView):
      @jwt_required()
      @blp.response(200, TradeResponseSchema)
      def get(self, username, response_id):
        current_user = get_jwt_identity()
        if current_user != username:
            abort(401, message="You are not authorized to view this response.")
        user = UserModel.query.filter_by(username=username).first()
        if user is None:
            abort(404, message="Username does not exist.")
        response = TradeResponseModel.query.filter_by(response_id=response_id).first()
        if response is None:
            abort(404, message="Trade response not found.")
        if response.to != username:
            abort(401, message="This trade response does not belong to this user.")
        response.status = "Seen"
        db.session.commit()
        return response

@blp.route("/traderesponses")
class TradeResponse(MethodView):
    @blp.response(200, TradeResponseSchema(many=True))
    def get(self):
        response = TradeResponseModel.query.all()
        if not response:
            abort(404, message="No trade responses found.")
        return response

    @blp.arguments(TradeResponseSchema)
    @jwt_required()
    @blp.response(201, TradeResponseSchema)
    def post(self, response_data):
        username = response_data.get("username")
        request_id = response_data.get("request_id")
        current_user = get_jwt_identity()
        if current_user != username:
            abort(401, message="Please enter your own username to send a trade response.")
        try:
           user = UserModel.query.filter_by(username=username).one()
        except:
             abort(401, message="Invalid username.")
        try:
            request = TradeRequestModel.query.filter_by(request_id=request_id).one()
        except:
            abort(404, message="Trade request not found.")
        if username != request.to_username:
            abort(401, message="You are not authorized to respond to this trade request.")
        response_id = uuid.uuid4().hex
        response = TradeResponseModel(
          response_id=response_id,
          username=username,
          request_id=request_id,
          games_offered_titles=request.games_offered_titles,
          games_requested_titles=request.games_requested_titles,
          to = request.from_username,
          message=response_data.get("message"))
        from_user = UserModel.query.filter_by(username=request.from_username).one()
        from_user.trade_responses_notif += 1
        user.trade_requests_notif -= 1
        try:
          db.session.add(response)
          db.session.commit()
        except SQLAlchemyError:
            abort(500, message="Oops an error occured, please try again")
        from_email = from_user.email
        subject = "Trade Request Response"
        body = f"Your trade request with request_id: {request_id} has received a response from {username} in Tradey. Please check your account to review the response."
        send_email(from_email, subject, body)
        return response
