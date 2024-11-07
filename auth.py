from flask import Blueprint, request
from flask_restful import Api, Resource
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from models import db, User
from marshmallow import Schema, fields

# Define Blueprint and API for authentication
auth_bp = Blueprint('auth', __name__)
api_auth = Api(auth_bp)


# class UserSchema(Schema):
#     id = fields.Int(dump_only=True)
#     first_name = fields.Str(required=True)
#     last_name = fields.Str(required=True)
#     email = fields.Email(required=True)
#     role = fields.Str(required=True)
#     created_at = fields.DateTime(dump_only=True)
#     updated_at = fields.DateTime(dump_only=True)


# RegisterResource class for user registration
class RegisterResource(Resource):
    def post(self):
        data = request.get_json()

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

            return {"message": "User registered successfully"}, 201
        except Exception as e:
            # Log the error for debugging
            print(f"Error registering user: {str(e)}")
            return {"message": "An error occurred during registration"}, 500


# LoginResource class for user login
class LoginResource(Resource):
    def post(self):
        data = request.get_json()

        # Find the user by email
        user = User.query.filter_by(email=data['email']).first()

        # If user exists and password is correct, generate JWT token
        if user and check_password_hash(user.password_digest, data['password']):
            token = create_access_token(identity={'user_id': user.id, 'role': user.role.name})  # Convert Enum to string
            return {"token": token}, 200

        # If credentials are invalid, return an error message
        return {"message": "Invalid credentials"}, 401



# Add the resources to the API
api_auth.add_resource(RegisterResource, '/register')
api_auth.add_resource(LoginResource, '/login')
