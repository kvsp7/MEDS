from backend.database import SessionLocal
from backend.services.sales_service.models.sale import Sale

try:
    import pandas as pd
    from sklearn.ensemble import IsolationForest
    HAS_ML = True
except ImportError:
    HAS_ML = False

def detect_anomalies():
    db = SessionLocal()

    sales = db.query(Sale).all()

    if len(sales) < 5:
        db.close()
        return {
            "total_records": len(sales),
            "anomalies_found": 0,
            "anomaly_data": [],
            "message": "Baseline transaction count under threshold (<5)"
        }

    if not HAS_ML:
        # Heuristic anomaly check: quantity > 50 or price > 2000
        anomalies = [s for s in sales if s.quantity > 50 or s.total_price > 2000]
        db.close()
        return {
            "total_records": len(sales),
            "anomalies_found": len(anomalies),
            "anomaly_data": [{"quantity": a.quantity, "price": a.total_price} for a in anomalies]
        }

    data = []
    for s in sales:
        data.append([s.quantity, s.total_price])

    df = pd.DataFrame(data, columns=["quantity", "price"])

    model = IsolationForest(contamination=0.1)
    df["anomaly"] = model.fit_predict(df)

    anomalies = df[df["anomaly"] == -1]

    db.close()

    return {
        "total_records": len(df),
        "anomalies_found": len(anomalies),
        "anomaly_data": anomalies.to_dict(orient="records")
    }