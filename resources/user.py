import uuid
import random
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask.views import MethodView
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import SQLAlchemyError

from schemas import UserSchema, UserUpdateSchema, LoginSchema
from models import UserModel
from db import db
from resources.traderequest import send_email


blp = Blueprint("Users", "users", description="Operations on users' accounts")


@blp.route("/users/<string:username>")
class User(MethodView):
    @jwt_required()
    @blp.response(200, UserSchema)
    def get(self, username):
        current_user = get_jwt_identity()
        if current_user != username:
            abort(401, message="You are not authorized to view this user's information.")
        try:
            user = UserModel.query.filter_by(username=username).one()
        except: abort(404, message=f"User not found.")
        return user
    
    @jwt_required()
    def delete(self, username):
        current_user = get_jwt_identity()
        if current_user != username:
            abort(401, message="You are not authorized to delete this user's account.")
        user = UserModel.query.filter_by(username=username).first_or_404()
        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted."} 

  
    
@blp.route("/users")
class User(MethodView):
    @blp.response(200, UserSchema(many=True))
    def get(self):                           #Unaccessable to normal users
        users = UserModel.query.all()
        if not users:
            abort(404, message=f"There are no users in the system.")
        return users

    @blp.arguments(UserSchema)
    @blp.response(201, UserSchema)
    def post(self, user_data):
       existing_user = UserModel.query.filter((UserModel.email == user_data["email"]) | (UserModel.username == user_data["username"])).first()
       if existing_user is not None:
          if existing_user.email == user_data["email"] and existing_user.username == user_data["username"]:
              abort(400, message=f"Email and username already in use.")
          elif existing_user.username == user_data["username"]:
              abort(400, message=f"Username already in use.")
          elif existing_user.email == user_data["email"]:
              abort(400, message=f"Email already in use.")

       user_id = uuid.uuid4().hex
       password = user_data["password"]
       hashed_password = pbkdf2_sha256.hash(password)
       verif_code = random.randint(10000, 99999)

       user = UserModel(
          user_id = user_id,
          full_name = user_data["full_name"],
          username=user_data["username"],
          password= hashed_password,
          email=user_data["email"],
          verif_code = verif_code,
          message = "A verification code was sent to the email address entered, Please continue to login.",
          location = user_data["location"])
       try:
            db.session.add(user)
            db.session.commit()
            email = user_data["email"]
            subject = "Tradey Account Registration"
            body = f"Greetings, \n Please confirm your account by logging in using the specified credentials and this verification code {verif_code}."
            send_email(email, subject, body)
       except SQLAlchemyError:
            abort(500, message="Oops an error occured, please try again")
       return user
    
    @blp.route("/login")
    class Login(MethodView):
      @blp.arguments(LoginSchema)
      @blp.response(200, LoginSchema)
      def post(self, login_data):
        username = login_data.get("username")
        password = login_data.get("password")
        verif_code = login_data.get("verif_code")
        try:
            user = UserModel.query.filter_by(username=username).one()
            if not pbkdf2_sha256.verify(password, user.password):
               abort(401, message="Invalid username or password.")
        except: abort(401, message="Invalid username or password.")
        try:
            if verif_code!= user.verif_code:
                abort(401, message="Invalid verification code.")
        except:
            abort(401, message="Invalid verification code.")
        access_token = create_access_token(identity=username)
        return {**login_data, "access_token": access_token}







