#auth.py
from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from app import app

# Define Blueprint and API for authentication
auth_bp = Blueprint('auth', __name__)
api_auth = Api(auth_bp)

# RegisterResource class for user registration
class RegisterResource(Resource):
    def post(self):
        data = request.get_json()  # Get JSON data from the request

        # Check if the user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({"message": "Email already registered"}), 400

        # Hash the password before storing it
        hashed_password = generate_password_hash(data['password'])

        # Create a new User instance
        user = User(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            password_digest=hashed_password,
            role=data['role']
        )

        # Add the user to the database
        db.session.add(user)
        db.session.commit()

        return jsonify({"message": "User registered successfully"}), 201

# LoginResource class for user login
class LoginResource(Resource):
    def post(self):
        data = request.get_json()  # Get JSON data from the request

        # Find the user by email
        user = User.query.filter_by(email=data['email']).first()

        # If user exists and password is correct, generate JWT token
        if user and check_password_hash(user.password_digest, data['password']):
            token = create_access_token(identity={'user_id': user.id, 'role': user.role})
            return jsonify({"token": token}), 200

        # If credentials are invalid, return an error message
        return jsonify({"message": "Invalid credentials"}), 401

# Add the resources to the API
api_auth.add_resource(RegisterResource, '/register')
api_auth.add_resource(LoginResource, '/login')

# Register Blueprint for auth
app.register_blueprint(auth_bp)
