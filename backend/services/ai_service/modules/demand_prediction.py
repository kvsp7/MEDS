import datetime
from backend.database import SessionLocal
from backend.services.sales_service.models.sale import Sale

try:
    import pandas as pd
    from sklearn.linear_model import LinearRegression
    HAS_ML = True
except ImportError:
    HAS_ML = False

def predict_demand(medicine_id):
    db = SessionLocal()

    sales = db.query(Sale)\
        .filter(Sale.medicine_id == medicine_id)\
        .order_by(Sale.timestamp).all()

    if len(sales) < 3:
        db.close()
        return {"predicted_demand": 15, "message": "Low baseline historical sales; projected demand fallback applied"}

    if not HAS_ML:
        avg_qty = sum(s.quantity for s in sales) / len(sales)
        db.close()
        return {"predicted_demand": max(5, round(avg_qty * 1.2))}

    # create time index (0,1,2,3...)
    data = []
    for i, s in enumerate(sales):
        data.append([i, s.timestamp.day, s.quantity])

    df = pd.DataFrame(data, columns=["time_index", "day", "quantity"])

    X = df[["time_index", "day"]]
    y = df["quantity"]

    model = LinearRegression()
    model.fit(X, y)

    next_step = [[
        len(df),
        datetime.datetime.utcnow().day
    ]]
    prediction = model.predict(next_step)[0]

    db.close()

    return {"predicted_demand": max(0, round(prediction))}