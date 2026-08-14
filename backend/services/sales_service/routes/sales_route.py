from flask import Blueprint, request, jsonify
from backend.database import SessionLocal
from backend.services.sales_service.models.sale import Sale
from backend.services.inventory_service.models.batch import Batch
from backend.services.inventory_service.models.medicine import Medicine
from backend.shared.utils.auth_middleware import token_required
from backend.shared.utils.role_middleware import role_required
import datetime
from backend.shared.utils.logger import logger
from backend.shared.utils.audit import log_action
from backend.services.sales_service.models.invoice import Invoice
import uuid

sales_bp = Blueprint("sales", __name__)

@sales_bp.route("/sell", methods=["POST"])
@token_required
@role_required(["admin", "pharmacist"])
def sell_medicine():
    db = SessionLocal()
    try:
        #---FOR SAFE Json handling ass it can be None we avoid it
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        
        medicine_id = data.get("medicine_id")
        quantity_needed = data.get("quantity")
        if not isinstance(quantity_needed, int):
            return jsonify({"error": "Quantity must be an integer"}), 400
        outlet_id = data.get("outlet_id")

        if not medicine_id or not quantity_needed or not outlet_id:
            return jsonify({"error": "Missing required fields"}), 400 #-- check for missing fields

        if outlet_id == "all" or not isinstance(outlet_id, int):
            return jsonify({"error": "Cannot perform billing operation when 'All Outlets' is selected. Please select a specific outlet/store."}), 400

        if quantity_needed <= 0:
            return jsonify({"error": "Quantity must be greater than 0"}), 400
        

        # get batches sorted by earliest expiry (FIFO)
        batches = db.query(Batch)\
            .filter(
                Batch.medicine_id == medicine_id,
                Batch.outlet_id == outlet_id
            )\
            .with_for_update()\
            .order_by(Batch.expiry_date).all()

        total_price = 0
        remaining_qty = quantity_needed

        medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()

        if not medicine:
            return jsonify({"error": "Medicine not found"}), 404

        for batch in batches:
            #--- skip expired batches
            if batch.expiry_date < datetime.datetime.utcnow().date():
                continue
            if remaining_qty <= 0:
                break

            if batch.quantity == 0:
                continue

            if batch.quantity >= remaining_qty:
                batch.quantity -= remaining_qty
                total_price += remaining_qty * medicine.price
                remaining_qty = 0
            else:
                total_price += batch.quantity * medicine.price
                remaining_qty -= batch.quantity
                batch.quantity = 0

        if remaining_qty > 0:
            return jsonify({"error": "Not enough stock"}), 400
        
        customer_id = data.get("customer_id")

        sale = Sale(
            medicine_id=medicine_id,
            quantity=quantity_needed,
            total_price=total_price,
            outlet_id=outlet_id,
            timestamp=datetime.datetime.utcnow(),
            customer_id = data.get("customer_id")
        )
        db.add(sale)
        db.commit()
        invoice_number = f"INV-{uuid.uuid4().hex[:8]}"

        invoice = Invoice(
            invoice_number=invoice_number,
            sale_id=sale.id
        )

        db.add(invoice)
        db.commit()

        #-----------------store sales in log file-----------------
        user = request.user
        user_id = request.user.get("user_id")

        log_action(
            user_id=user_id,
            action="SALE",
            entity="Medicine",
            entity_id=medicine_id,
            description=f"Sold {quantity_needed} units from outlet {outlet_id}"
        )
        
        logger.info(f"User {user_id} made sale - Medicine ID: {medicine_id}, Quantity: {quantity_needed}, Outlet: {outlet_id}")
        profit = total_price - (quantity_needed * medicine.cost_price)
        log_action(
            user_id=user_id,
            action="INVOICE_CREATED",
            entity="Invoice",
            entity_id=invoice.id,
            description=f"Invoice {invoice_number} created"
        )
                
        return jsonify({
            "message": "Sale completed",
            "invoice": {
                "invoice_id": invoice_number,
                "medicine_id": medicine_id,
                "medicine_name": medicine.name,
                "quantity": quantity_needed,
                "price_per_unit": medicine.price,
                "total_price": total_price,
                "profit": profit,
                "remaining_stock": sum(b.quantity for b in batches),
                "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            }
        })
    except Exception as e:
        logger.exception(f"Error during sale - Medicine ID: {medicine_id}, Outlet: {outlet_id}")
        db.rollback()
        return jsonify({"error": "An error occurred during the sale process"}), 500
    
    finally:
        db.close()

@sales_bp.route("/all", methods=["GET"])
@token_required
def get_all_sales():
    from backend.services.sales_service.models.sale import Sale
    from backend.services.inventory_service.models.medicine import Medicine
    from backend.services.inventory_service.models.outlet import Outlet
    from backend.services.sales_service.models.customer import Customer
    from backend.services.sales_service.models.invoice import Invoice

    raw_outlet = request.args.get("outlet_id")
    outlet_id = int(raw_outlet) if raw_outlet and str(raw_outlet).isdigit() else None

    db = SessionLocal()
    query = db.query(Sale)
    if outlet_id:
        query = query.filter(Sale.outlet_id == outlet_id)
        
    sales = query.order_by(Sale.timestamp.desc()).all()

    result = []
    for s in sales:
        med = db.query(Medicine).filter(Medicine.id == s.medicine_id).first()
        outlet = db.query(Outlet).filter(Outlet.id == s.outlet_id).first()
        customer = db.query(Customer).filter(Customer.id == s.customer_id).first() if s.customer_id else None
        invoice = db.query(Invoice).filter(Invoice.sale_id == s.id).first()

        result.append({
            "id": s.id,
            "medicine_id": s.medicine_id,
            "medicine_name": med.name if med else "Unknown",
            "quantity": s.quantity,
            "total_price": s.total_price,
            "outlet_id": s.outlet_id,
            "outlet_name": outlet.name if outlet else "Unknown",
            "customer_name": customer.name if customer else "Walk-in",
            "invoice_number": invoice.invoice_number if invoice else f"INV-{s.id}",
            "timestamp": s.timestamp.strftime("%Y-%m-%d %H:%M:%S") if s.timestamp else ""
        })

    db.close()
    return jsonify(result)