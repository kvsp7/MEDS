from flask import Blueprint, request, jsonify
from backend.database import SessionLocal
from backend.services.inventory_service.models.batch import Batch
from backend.shared.utils.auth_middleware import token_required
from backend.shared.utils.role_middleware import role_required
from datetime import datetime

batch_bp = Blueprint("batch", __name__)

@batch_bp.route("/add", methods=["POST"])
@token_required
@role_required(["admin", "warehouse"])
def add_batch():
    data = request.json

    db = SessionLocal()

    new_batch = Batch(
        medicine_id=data.get("medicine_id"),
        batch_number=data.get("batch_number"),
        expiry_date=datetime.strptime(data.get("expiry_date"), "%Y-%m-%d"),
        quantity=data.get("quantity"),
        outlet_id=data.get("outlet_id")
    )

    db.add(new_batch)
    db.commit()
    db.close()

    return jsonify({"message": "Batch added"})

@batch_bp.route("/all", methods=["GET"])
@token_required
def get_all_batches():
    from backend.services.inventory_service.models.medicine import Medicine
    from backend.services.inventory_service.models.outlet import Outlet

    db = SessionLocal()
    batches = db.query(Batch).all()

    result = []
    for b in batches:
        med = db.query(Medicine).filter(Medicine.id == b.medicine_id).first()
        outlet = db.query(Outlet).filter(Outlet.id == b.outlet_id).first()
        result.append({
            "id": b.id,
            "medicine_id": b.medicine_id,
            "medicine_name": med.name if med else "Unknown",
            "batch_number": b.batch_number,
            "expiry_date": b.expiry_date.strftime("%Y-%m-%d") if b.expiry_date else "",
            "quantity": b.quantity,
            "outlet_id": b.outlet_id,
            "outlet_name": outlet.name if outlet else "Unknown"
        })

    db.close()
    return jsonify(result)