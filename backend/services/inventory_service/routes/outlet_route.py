from flask import Blueprint, request, jsonify
from backend.database import SessionLocal
from backend.services.inventory_service.models.outlet import Outlet
from backend.shared.utils.auth_middleware import token_required
from backend.shared.utils.role_middleware import role_required

outlet_bp = Blueprint("outlet", __name__)

@outlet_bp.route("/add", methods=["POST"])
@token_required
@role_required(["admin"])
def add_outlet():
    data = request.json

    db = SessionLocal()

    new_outlet = Outlet(
        name=data.get("name"),
        location=data.get("location"),
        type=data.get("type")
    )

    db.add(new_outlet)
    db.commit()

    return jsonify({"message": "Outlet created"})

def _ensure_default_outlets(db):
    outlets = db.query(Outlet).all()
    if not outlets:
        store_a = Outlet(name="Store A - Main Pharmacy", location="Central Avenue", type="Retail & Wholesale")
        store_b = Outlet(name="Store B - Downtown Branch", location="Downtown Medical Center", type="Retail Branch")
        db.add(store_a)
        db.add(store_b)
        db.commit()
        outlets = db.query(Outlet).all()
    return outlets

@outlet_bp.route("/public-list", methods=["GET"])
def public_outlets():
    db = SessionLocal()
    try:
        outlets = _ensure_default_outlets(db)
        result = [{"id": o.id, "name": o.name, "location": o.location, "type": o.type} for o in outlets]
        return jsonify(result)
    finally:
        db.close()

@outlet_bp.route("/all", methods=["GET"])
@token_required
def get_outlets():
    db = SessionLocal()
    try:
        outlets = _ensure_default_outlets(db)
        result = [{"id": o.id, "name": o.name, "location": o.location, "type": o.type} for o in outlets]
        return jsonify(result)
    finally:
        db.close()