from backend.database import SessionLocal
from backend.services.inventory_service.models.batch import Batch
from backend.services.inventory_service.models.medicine import Medicine
from backend.services.inventory_service.models.outlet import Outlet
from backend.services.ai_service.modules.demand_prediction import predict_demand

def get_replenishment():
    db = SessionLocal()

    medicines = db.query(Medicine).all()
    outlets = db.query(Outlet).all()
    suggestions = []

    for outlet in outlets:
        for med in medicines:
            batches = db.query(Batch).filter(
                Batch.medicine_id == med.id,
                Batch.outlet_id == outlet.id
            ).all()
            
            outlet_stock = sum(b.quantity for b in batches)
            
            prediction = predict_demand(med.id)
            if isinstance(prediction, dict) and "predicted_demand" in prediction:
                predicted = prediction["predicted_demand"]
            else:
                predicted = 10

            if outlet_stock < max(10, predicted):
                reorder = max(5, max(10, predicted) - outlet_stock)
                msg = f"hi. admin the store {outlet.name} in {outlet.location or 'Main Branch'} has low stock in {med.name} {outlet_stock} quantity left"
                suggestions.append({
                    "medicine": med.name,
                    "outlet_id": outlet.id,
                    "outlet_name": outlet.name,
                    "outlet_location": outlet.location or "Main Branch",
                    "current_stock": outlet_stock,
                    "predicted_demand": predicted,
                    "suggested_reorder": reorder,
                    "message": msg
                })

    db.close()
    return suggestions