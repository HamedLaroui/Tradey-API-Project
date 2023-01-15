import os
import uuid
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from schemas import TradeRequestSchema
from models import TradeRequestModel, UserModel, GameModel
from db import db
from sqlalchemy.exc import SQLAlchemyError
import smtplib
from email.mime.text import MIMEText


def send_email(to_email, subject, body):
    
    sender_email =  os.environ.get('SENDER_EMAIL') 
    app_password = os.environ.get('APP_PASSWORD')
    server = os.environ.get('SERVER')
    port = os.environ.get('PORT')

    recipient_email = to_email

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email

    smtp = smtplib.SMTP(server, port)
    smtp.starttls()
    smtp.login(sender_email, app_password)
    smtp.send_message(msg)
    smtp.quit()



blp = Blueprint("TradeRequests", "traderequests", description="Operations on trade requests")


@blp.route("/traderequests/<string:username>/sent")
class TradeRequest(MethodView):
    @jwt_required()
    @blp.response(200, TradeRequestSchema(many=True))
    def get(self, username):
        current_user = get_jwt_identity()
        if current_user != username:
            abort(401, message="You are not authorized to view these requests.")
        user = UserModel.query.filter_by(username=username).first()
        if not user:
            abort(404, message="Username does not exist.")

        request = TradeRequestModel.query.filter(TradeRequestModel.from_username == username).all()

        if not request:
           abort(404, message="No trade requests sent from this user yet.")
        
        return request
    
    
@blp.route("/traderequests/<string:username>/received")
class TradeRequest(MethodView):
    @jwt_required()
    @blp.response(200, TradeRequestSchema(many=True))
    def get(self, username):
        current_user = get_jwt_identity()
        if current_user != username:
            abort(401, message="You are not authorized to view these requests.")
        user = UserModel.query.filter_by(username=username).first()
        if not user:
            abort(404, message="Username does not exist.")
        request = TradeRequestModel.query.filter_by(to_username=username).all()
        if not request:
            abort(404, message="No trade requests received for this user yet.")
        return request
    
@blp.route("/traderequests/<string:username>/received/<string:request_id>")
class TradeRequest(MethodView):
    @jwt_required()
    @blp.response(200, TradeRequestSchema)
    def get(self, username, request_id):
        current_user = get_jwt_identity()
        if current_user != username:
            abort(401, message="You are not authorized to view these requests.")
        user = UserModel.query.filter_by(username=username).first()
        if user is None:
            abort(404, message="Username does not exist.")
        request = TradeRequestModel.query.filter_by(request_id=request_id, to_username=username).first()
        if request is None:
            abort(404, message="Trade request not found.")
        request.status = "Seen"
        db.session.commit()
        return request
    
@blp.route("/traderequests/<string:username>/<string:request_id>")
class TradeRequest(MethodView):
    @jwt_required()
    @blp.response(200, TradeRequestSchema)
    def delete(self, username, request_id):
        current_user = get_jwt_identity()
        if current_user != username:
            abort(401, message="You are not authorized to delete this request.")
        user = UserModel.query.filter_by(username=username).first()
        if user is None:
            abort(404, message="Username does not exist.")
        request = TradeRequestModel.query.filter_by(request_id=request_id).first()
        if request is None:
            abort(404, message="Trade request not found.")
        db.session.delete(request)
        db.session.commit()
        return {"message": "Trade request deleted."}


@blp.route("/traderequests")
class TradeRequest(MethodView):
    @blp.response(200, TradeRequestSchema(many=True))
    def get(self):
        request = TradeRequestModel.query.all()
        if not request:
            abort(404, message="No trade requests found.")
        return request

    @blp.arguments(TradeRequestSchema)
    @jwt_required()
    @blp.response(201, TradeRequestSchema)
    def post(self, request_data):
        from_username = request_data.get("from_username")
        to_username = request_data.get("to_username")
        games_offered = request_data.get("games_offered")
        games_requested = request_data.get("games_requested")
        current_user = get_jwt_identity()
        if current_user != from_username:
            abort(401, message="Please enter your own username to send a trade request.")
        try:
            user = UserModel.query.filter_by(username=from_username).one()
            if user is None:
                abort(401, message="Invalid username.")
        except:
            abort(401, message="Invalid username or password.")
        try:
            to_user = UserModel.query.filter_by(username=to_username).one()
        except:
            abort(404, message="The username you are trying to send a request to does not exist.")
        if from_username == to_username:
            abort(400, message="From and to usernames cannot be the same.")
        for game_id in games_offered:
            game = GameModel.query.filter_by(game_id=game_id).first()
            if game is None:
                abort(404, message="One or more games offered not found.")
            if game.user.username != from_username:
                abort(401, message="One or more games offered do not belong to you.")
        for game_id in games_requested:
            game = GameModel.query.filter_by(game_id=game_id).first()
            if game is None:
                abort(404, message="One or more games requested not found.")
            if game.user.username != to_username:
                abort(401, message="One or more games requested do not belong to the requested user.") 
        request_id = uuid.uuid4().hex
        games_offered_titles = []
        for game_id in games_offered:
            game = GameModel.query.filter_by(game_id=game_id).first()
            if game:
                games_offered_titles.append(game.title)
        games_requested_titles = []
        for game_id in games_requested:
            game = GameModel.query.filter_by(game_id=game_id).first()
            if game:
               games_requested_titles.append(game.title)
        request = TradeRequestModel(
            request_id = request_id,
            from_username=from_username,
            to_username=to_username,
            games_offered=games_offered,
            games_requested=games_requested,
            games_offered_titles=games_offered_titles,
            games_requested_titles=games_requested_titles)
        to_user = UserModel.query.filter_by(username=to_username).one()
        to_user.trade_requests_notif += 1
        try:
            db.session.add(request)
            db.session.commit()
        except SQLAlchemyError:
            abort(500, message="Oops an error occured, please try again")
        to_email = to_user.email
        subject = "Transfer Request"
        body = f"Howdy partner,\n You have received a transfer request with request_id: {request_id} from {from_username} in Tradey. \n Please check your account to review the request."
        send_email(to_email, subject, body)
        return request
