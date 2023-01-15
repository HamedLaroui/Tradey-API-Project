from db import db
from datetime import datetime
import pytz
from sqlalchemy_jsonfield import JSONField



class UserModel(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.String(40), primary_key=True)
    full_name = db.Column(db.String(40), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(40), unique=True, nullable=False)
    location = db.Column(db.String(50), nullable=False)
    trade_requests_notif = db.Column(db.Integer, default=0)
    trade_responses_notif = db.Column(db.Integer, default=0)
    verif_code = db.Column(db.Integer)
    message = db.Column(db.String(50), default="A verification code is sent to your email for login")
    
    games = db.relationship("GameModel", back_populates="user", lazy="dynamic")
    #requests = db.relationship("TradeRequestModel", back_populates="user", lazy="dynamic")
    #responses = db.relationship("TradeResponseModel", back_populates="user", lazy="dynamic")
    #ratings = db.relationship("RatingModel", back_populates="user", lazy="dynamic")
    


class GameModel(db.Model):
    __tablename__ = "games"

    username = db.Column(db.String(20), unique=False, nullable=False)
    game_id = db.Column(db.String(40), primary_key=True)
    title = db.Column(db.String(50), unique=False, nullable=False)
    platform = db.Column(db.String(20), unique=False, nullable=False)
    year_of_purchase = db.Column(db.Integer, unique=False, nullable=False)
    condition = db.Column(db.String(20), unique=False, nullable=False)
    
    user_id = db.Column(db.String, db.ForeignKey("users.user_id"), unique=False, nullable=False)
    user = db.relationship("UserModel", back_populates="games")
    #ratings = db.relationship("RatingModel", back_populates="game", lazy="dynamic")
    
    
class TradeRequestModel(db.Model):
    __tablename__ = "trade_requests"

    request_id = db.Column(db.String(40), primary_key=True)
    from_username = db.Column(db.String(20), nullable=False)
    to_username = db.Column(db.String(20), nullable=False)
    games_offered = db.Column(JSONField, nullable=False)
    games_requested = db.Column(JSONField, nullable=False)
    games_offered_titles = db.Column(JSONField, nullable=False)
    games_requested_titles = db.Column(JSONField, nullable=False)
    message = db.Column(db.String(100))
    status = db.Column(db.String(10), default="Pending")
    date_time = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Africa/Tunis')), nullable=False)
    
    
class TradeResponseModel(db.Model):
    __tablename__ = "trade_responses"

    response_id = db.Column(db.String(40), primary_key=True)
    username = db.Column(db.String(20), unique=False, nullable=False)
    request_id = db.Column(db.String(60), db.ForeignKey("trade_requests.request_id"))
    games_offered_titles = db.Column(JSONField, nullable=False)
    games_requested_titles = db.Column(JSONField, nullable=False)
    to = db.Column(db.String(40), unique=False, nullable=False)
    message = db.Column(db.Boolean, nullable=False)
    status = db.Column(db.String(10), default="Sent")
    date_time = db.Column(db.DateTime, default=datetime.now(pytz.timezone("Africa/Tunis")), nullable=False)

    #request = db.relationship("TradeRequestModel", back_populates="responses")


class RatingModel(db.Model):
    __tablename__ = "ratings"

    rating_id = db.Column(db.String(40), primary_key=True)
    username = db.Column(db.String(20), unique=False, nullable=False)
    value = db.Column(db.Integer, unique=False, nullable=False)
    response_id = db.Column(db.String(40), db.ForeignKey("trade_responses.response_id"), nullable=True)
    message = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(10), nullable=False, default="Thank you for your review")
    date_time = db.Column(db.DateTime, default=datetime.now(pytz.timezone('Africa/Tunis')), nullable=False)






