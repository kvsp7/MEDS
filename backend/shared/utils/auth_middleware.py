from functools import wraps
from flask import request, jsonify
import jwt

SECRET_KEY = "supersecretkey"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # get token from header
        if "Authorization" in request.headers:
            token = request.headers["Authorization"].split(" ")[1]

        if not token:
            return jsonify({"error": "Token is missing"}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user = data  # attach user info
        except:
            return jsonify({"error": "Invalid or expired token"}), 401

        return f(*args, **kwargs)

    return decorated