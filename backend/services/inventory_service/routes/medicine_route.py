from flask import Blueprint, request, jsonify
from backend.database import SessionLocal
from backend.services.inventory_service.models.medicine import Medicine
from backend.shared.utils.auth_middleware import token_required
from backend.shared.utils.role_middleware import role_required


medicine_bp = Blueprint("medicine", __name__)

# ADD MEDICINE
@medicine_bp.route("/add", methods=["POST"])
@token_required
def add_medicine():
    data = request.json

    db = SessionLocal()

    new_med = Medicine(
        name=data.get("name"),
        description=data.get("description"),
        price=data.get("price"),
        cost_price=data.get("cost_price"),
        category=data.get("category")
    )

    db.add(new_med)
    db.commit()
    db.close()

    return jsonify({"message": "Medicine added"})

# GET ALL MEDICINES
@medicine_bp.route("/all", methods=["GET"])
@token_required
def get_all_medicines():
    db = SessionLocal()
    meds = db.query(Medicine).all()

    result = []
    for m in meds:
        result.append({
            "id": m.id,
            "name": m.name,
            "description": m.description,
            "price": m.price,
            "cost_price": m.cost_price,
            "category": m.category
        })

    db.close()
    return jsonify(result)