#jwt_helpers.py

from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from functools import wraps
from models import User  # Adjust the import based on your project structure

def generate_token(user_id, role):
    return create_access_token(identity={"user_id": user_id, "role": role})

def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user = get_jwt_identity()
        user = User.query.get(current_user['user_id'])
        if user and user.is_admin:  # Ensure you have an 'is_admin' attribute or similar in your User model
            return fn(*args, **kwargs)
        else:
            return {"message": "Admin access required"}, 403
    return wrapper
