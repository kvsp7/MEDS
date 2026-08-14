from flask import Blueprint, request, jsonify
from backend.database import SessionLocal
from backend.services.sales_service.models.customer import Customer
from backend.shared.utils.auth_middleware import token_required
from backend.shared.utils.role_middleware import role_required

customer_bp = Blueprint("customer", __name__)

@customer_bp.route("/add", methods=["POST"])
@token_required
@role_required(["admin", "pharmacist"])
def add_customer():
    data = request.json
    db = SessionLocal()

    customer = Customer(
        name=data.get("name"),
        type=data.get("type"),
        contact=data.get("contact")
    )

    db.add(customer)
    db.commit()
    db.close()

    return jsonify({"message": "Customer added"})

@customer_bp.route("/all", methods=["GET"])
@token_required
def get_customers():
    db = SessionLocal()

    customers = db.query(Customer).all()

    result = []
    for c in customers:
        result.append({
            "id": c.id,
            "name": c.name,
            "type": c.type,
            "contact": c.contact
        })

    db.close()

    return jsonify(result)