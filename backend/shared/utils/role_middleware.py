from functools import wraps
from flask import jsonify, request

allowed_roles=['admin','warehouse']

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):

            user = request.user  # from JWT middleware

            if user["role"] not in allowed_roles:
                return jsonify({"error": "Access denied"}), 403

            return f(*args, **kwargs)

        return wrapper
    return decorator