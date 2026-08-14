from flask import Blueprint, request, jsonify
from backend.database import SessionLocal
from backend.services.auth_service.models.user import User
import bcrypt
import jwt
import datetime
from backend.shared.utils.logger import logger

from backend.services.inventory_service.models.outlet import Outlet

auth = Blueprint("auth", __name__)

# REGISTER
@auth.route("/register", methods=["POST"])
def register():
    data = request.json or {}

    username = data.get("username")
    password = data.get("password")
    role = data.get("role") or "admin"
    raw_outlet = data.get("outlet_id")
    outlet_id = int(raw_outlet) if raw_outlet and str(raw_outlet).isdigit() else None

    db = SessionLocal()
    try:
        # check if user exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            return jsonify({"error": "User already exists"}), 400

        # hash password
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        new_user = User(
            username=username,
            password=hashed_pw.decode('utf-8'),
            role=role,
            outlet_id=outlet_id
        )

        db.add(new_user)
        db.commit()
        logger.info(f"New user registered: {username} for outlet: {outlet_id}")

        return jsonify({"message": "User registered successfully"})
    finally:
        db.close()

# LOGIN
SECRET_KEY = "supersecretkey"

@auth.route("/login", methods=["POST"])
def login():
    data = request.json or {}

    username = data.get("username")
    password = data.get("password")
    selected_outlet_raw = data.get("outlet_id")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()

        if not user:
            return jsonify({"error": "User not found, please register"}), 404

        if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return jsonify({"error": "Invalid password"}), 401

        # Determine effective active outlet
        active_outlet_id = None
        if user.role == "admin":
            if selected_outlet_raw and str(selected_outlet_raw).isdigit():
                active_outlet_id = int(selected_outlet_raw)
            else:
                active_outlet_id = user.outlet_id
        else:
            active_outlet_id = user.outlet_id

        outlet_name = "All Outlets"
        if active_outlet_id:
            outlet = db.query(Outlet).filter(Outlet.id == active_outlet_id).first()
            if outlet:
                outlet_name = outlet.name

        token = jwt.encode({
            "user_id": user.id,
            "role": user.role,
            "outlet_id": active_outlet_id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        }, SECRET_KEY, algorithm="HS256")

        logger.info(f"User logged in: {username} (Outlet: {outlet_name})")

        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "outlet_id": active_outlet_id,
                "outlet_name": outlet_name
            }
        })
    finally:
        db.close()

