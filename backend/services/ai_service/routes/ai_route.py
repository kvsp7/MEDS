from flask import Blueprint, jsonify
from backend.shared.utils.auth_middleware import token_required
from backend.shared.utils.role_middleware import role_required
from backend.services.ai_service.modules.demand_prediction import predict_demand
from backend.services.ai_service.modules.anomaly_detection import detect_anomalies
from flask import request
from backend.services.ai_service.modules.chat_engine import process_query
from backend.services.ai_service.modules.replenishment import get_replenishment


ai_bp = Blueprint("ai", __name__)

@ai_bp.route("/predict/<int:medicine_id>", methods=["GET"])
@token_required
@role_required(["admin", "warehouse"])
def demand_prediction(medicine_id):
    result = predict_demand(medicine_id)
    return jsonify(result)


@ai_bp.route("/anomalies", methods=["GET"])
@token_required
@role_required(["admin", "finance"])
def anomalies():
    result = detect_anomalies()
    return jsonify(result)

@ai_bp.route("/chat", methods=["POST"])
@token_required
def chat():
    data = request.json
    user_query = data.get("query")

    response = process_query(user_query)

    return {"response": response}


@ai_bp.route("/replenishment", methods=["GET"])
@token_required
@role_required(["admin", "warehouse"])
def replenishment():
    result = get_replenishment()
    return jsonify(result)


