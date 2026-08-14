from flask import Blueprint, jsonify, request
from backend.database import SessionLocal
from backend.services.sales_service.models.sale import Sale
from backend.services.inventory_service.models.medicine import Medicine
from sqlalchemy import func
from backend.shared.utils.auth_middleware import token_required
from backend.shared.utils.role_middleware import role_required
from backend.services.inventory_service.models.outlet import Outlet


report_bp = Blueprint("report", __name__)

def _get_requested_outlet_id():
    raw = request.args.get("outlet_id")
    if raw and str(raw).isdigit():
        return int(raw)
    return None

@report_bp.route("/revenue", methods=["GET"])
@token_required
@role_required(["admin", "finance", "pharmacist", "warehouse"])
def total_revenue():
    db = SessionLocal()
    try:
        outlet_id = _get_requested_outlet_id()
        query = db.query(func.sum(Sale.total_price))
        if outlet_id:
            query = query.filter(Sale.outlet_id == outlet_id)
        revenue = query.scalar()
        return jsonify({
            "total_revenue": revenue or 0
        })
    finally:
        db.close()

@report_bp.route("/top-medicines", methods=["GET"])
@token_required
@role_required(["admin", "finance", "pharmacist", "warehouse"])
def top_medicines():
    db = SessionLocal()
    try:
        outlet_id = _get_requested_outlet_id()
        query = db.query(
            Sale.medicine_id,
            func.sum(Sale.quantity).label("total_sold")
        )
        if outlet_id:
            query = query.filter(Sale.outlet_id == outlet_id)
            
        results = query.group_by(Sale.medicine_id)\
         .order_by(func.sum(Sale.quantity).desc())\
         .limit(5).all()

        data = []
        for r in results:
            med = db.query(Medicine).filter(Medicine.id == r.medicine_id).first()
            data.append({
                "medicine_name": med.name if med else "Unknown",
                "quantity_sold": r.total_sold
            })

        return jsonify(data)
    finally:
        db.close()

@report_bp.route("/sales-count", methods=["GET"])
@token_required
@role_required(["admin", "finance", "pharmacist", "warehouse"])
def sales_count():
    db = SessionLocal()
    try:
        outlet_id = _get_requested_outlet_id()
        query = db.query(func.count(Sale.id))
        if outlet_id:
            query = query.filter(Sale.outlet_id == outlet_id)
        count = query.scalar()
        return jsonify({
            "total_sales": count or 0
        })
    finally:
        db.close()

@report_bp.route("/profit", methods=["GET"])
@token_required
@role_required(["admin", "finance", "pharmacist", "warehouse"])
def total_profit():
    db = SessionLocal()
    try:
        outlet_id = _get_requested_outlet_id()
        query = db.query(Sale)
        if outlet_id:
            query = query.filter(Sale.outlet_id == outlet_id)
        sales = query.all()
        
        total_profit = 0
        for s in sales:
            med = db.query(Medicine).filter(Medicine.id == s.medicine_id).first()
            if med:
                total_profit += s.total_price - (s.quantity * (med.cost_price or 0))

        return jsonify({"total_profit": total_profit})
    finally:
        db.close()

@report_bp.route("/outlet-performance", methods=["GET"])
@token_required
@role_required(["admin", "finance", "pharmacist", "warehouse"])
def outlet_performance():
    db = SessionLocal()
    try:
        outlet_id = _get_requested_outlet_id()
        
        outlet_query = db.query(Outlet)
        if outlet_id:
            outlet_query = outlet_query.filter(Outlet.id == outlet_id)
        outlets = outlet_query.all()
        
        data = []
        for o in outlets:
            sales = db.query(Sale).filter(Sale.outlet_id == o.id).all()
            total_rev = sum(s.total_price for s in sales)
            total_sales_count = len(sales)
            
            total_cost = 0
            med_sales_counter = {}
            for s in sales:
                med = db.query(Medicine).filter(Medicine.id == s.medicine_id).first()
                if med:
                    total_cost += s.quantity * (med.cost_price or 0)
                    med_sales_counter[med.name] = med_sales_counter.get(med.name, 0) + s.quantity
            
            net_profit = total_rev - total_cost
            margin = ((net_profit / total_rev) * 100) if total_rev > 0 else 0
            
            top_med_name = "N/A"
            top_med_qty = 0
            if med_sales_counter:
                top_med_name = max(med_sales_counter, key=med_sales_counter.get)
                top_med_qty = med_sales_counter[top_med_name]
                
            data.append({
                "outlet_id": o.id,
                "outlet_name": o.name,
                "location": o.location or "N/A",
                "type": o.type or "Retail",
                "total_revenue": round(total_rev, 2),
                "total_cost": round(total_cost, 2),
                "total_profit": round(net_profit, 2),
                "profit_margin": round(margin, 1),
                "total_sales": total_sales_count,
                "top_medicine": top_med_name,
                "top_medicine_qty": top_med_qty
            })
            
        data.sort(key=lambda x: x["total_revenue"], reverse=True)
        return jsonify(data)
    finally:
        db.close()

@report_bp.route("/fast-moving", methods=["GET"])
@token_required
@role_required(["admin", "finance", "pharmacist", "warehouse"])
def fast_moving_items():
    db = SessionLocal()
    try:
        outlet_id = _get_requested_outlet_id()
        query = db.query(
            Sale.medicine_id,
            func.sum(Sale.quantity).label("total_sold")
        )
        if outlet_id:
            query = query.filter(Sale.outlet_id == outlet_id)
            
        results = query.group_by(Sale.medicine_id)\
         .order_by(func.sum(Sale.quantity).desc())\
         .limit(5)\
         .all()

        data = []
        for r in results:
            med = db.query(Medicine).filter(Medicine.id == r.medicine_id).first()
            data.append({
                "medicine_id": r.medicine_id,
                "medicine_name": med.name if med else "Unknown",
                "total_sold": r.total_sold
            })

        return jsonify(data)
    finally:
        db.close()