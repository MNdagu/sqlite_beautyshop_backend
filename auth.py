#auth.py

from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource, reqparse
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt,
    get_jwt_identity,
    JWTManager
)
from models import db, User, Cart
from marshmallow import Schema, fields
from datetime import timedelta, datetime

# Define Blueprint and API for authentication
auth_bp = Blueprint('auth', __name__)
api_auth = Api(auth_bp)

# Token blacklist for handling logout
BLACKLIST = set()

# Initialize JWT Manager (to be done in the main app)
jwt = JWTManager()

user_parser = reqparse.RequestParser()
user_parser.add_argument('first_name', type=str, required=True, help='First name is required')
user_parser.add_argument('last_name', type=str, required=True, help='Last name is required')
user_parser.add_argument('email', type=str, required=True, help='Email is required')
user_parser.add_argument('password', type=str, required=True, help='Password is required')
user_parser.add_argument('role', type=str, required=True, help="Role is required ('admin' or 'customer')")


# Callback function to check if a token is blacklisted
@jwt.token_in_blocklist_loader
def check_if_token_in_blacklist(jwt_header, jwt_payload):
    jti = jwt_payload["jti"]
    return jti in BLACKLIST

# RegisterResource class for user registration
class RegisterResource(Resource):
    def post(self):
        data = user_parser.parse_args()
        
        # Validate role
        if data['role'] not in ['admin', 'customer']:
            return {"message": "Role must be either 'admin' or 'customer'"}, 400


        # Check if the user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return {"message": "Email already registered"}, 400

        # Hash the password before storing it
        hashed_password = generate_password_hash(data['password'])

        try:
            user = User(
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
                password_digest=hashed_password,
                role=data['role']
            )

            db.session.add(user)
            db.session.commit()
            
            cart = Cart(
                user_id=user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.session.add(cart)
            db.session.commit()

            return {"message": "User registered successfully, and a cart has been created!"}, 201
        except Exception as e:
            # Log the error for debugging
            print(f"Error registering user: {str(e)}")
            db.session.rollback()
            return {"message": "An error occurred during registration"}, 500

# LoginResource class for user login
class LoginResource(Resource):
    def post(self):
        data = request.get_json()

        # Find the user by email
        user = User.query.filter_by(email=data['email']).first()

        # If user exists and password is correct, generate JWT tokens
        if user and check_password_hash(user.password_digest, data['password']):
            access_token = create_access_token(identity={'user_id': user.id, 'role': user.role.name})
            refresh_token = create_refresh_token(identity={'user_id': user.id, 'role': user.role.name})
            return {"access_token": access_token, "refresh_token": refresh_token}, 200

        return {"message": "Invalid credentials"}, 401

# TokenRefreshResource class to refresh the access token
class TokenRefreshResource(Resource):
    @jwt_required(refresh=True)
    def post(self):
        # Get the identity from the refresh token
        identity = get_jwt_identity()
        # Generate a new access token using the identity
        new_access_token = create_access_token(identity=identity)
        return {"access_token": new_access_token}, 200

# LogoutResource class for user logout
class LogoutResource(Resource):
    @jwt_required()
    def post(self):
        # Get the unique identifier for the token
        jti = get_jwt()["jti"]
        
        # Add the token's jti to the blacklist to invalidate it
        BLACKLIST.add(jti)
        
        return {"message": "Successfully logged out"}, 200

# Add the resources to the API
api_auth.add_resource(RegisterResource, '/register')
api_auth.add_resource(LoginResource, '/login')
api_auth.add_resource(TokenRefreshResource, '/refresh')
api_auth.add_resource(LogoutResource, '/logout')
