import os
import sys

# Ensure workspace root is in python path
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if workspace_root not in sys.path:
    sys.path.insert(0, workspace_root)

from flask import Flask, request, send_from_directory
from flask_cors import CORS
from backend.database import engine, Base
from backend.services.auth_service.models.user import User
from backend.services.auth_service.routes.auth import auth
from backend.shared.utils.auth_middleware import token_required
from backend.shared.utils.role_middleware import role_required
from backend.services.inventory_service.models.medicine import Medicine
from backend.services.inventory_service.models.batch import Batch
from backend.services.inventory_service.routes.medicine_route import medicine_bp
from backend.services.inventory_service.routes.batch_route import batch_bp
from backend.services.sales_service.models.sale import Sale
from backend.services.sales_service.routes.sales_route import sales_bp
from backend.services.sales_service.routes.report_route import report_bp
from backend.services.ai_service.routes.ai_route import ai_bp
from backend.services.inventory_service.models.outlet import Outlet
from backend.services.inventory_service.routes.outlet_route import outlet_bp
from backend.shared.models.audit_log import AuditLog
from backend.services.sales_service.models.customer import Customer
from backend.services.sales_service.routes.customer_route import customer_bp
from backend.services.sales_service.models.invoice import Invoice

frontend_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
app = Flask(__name__, static_folder=frontend_folder, static_url_path="")
CORS(app)

Base.metadata.create_all(bind=engine)

# register routes
app.register_blueprint(auth, url_prefix="/auth")

@app.route("/")
def home():
    if os.path.exists(os.path.join(frontend_folder, "index.html")):
        return send_from_directory(frontend_folder, "index.html")
    return "Backend is running! Frontend index.html not found."




@app.route("/protected")
@token_required
def protected():
    return {
        "message": "You accessed a protected route",
        "user": request.user
    }


@app.route("/admin-only")
@token_required
@role_required(["admin"])
def admin_route():
    return {"message": "Welcome Admin!"}


app.register_blueprint(medicine_bp, url_prefix="/medicine")


app.register_blueprint(batch_bp, url_prefix="/batch")


app.register_blueprint(sales_bp, url_prefix="/sales")


app.register_blueprint(report_bp, url_prefix="/report")

app.register_blueprint(ai_bp, url_prefix="/ai")

app.register_blueprint(outlet_bp, url_prefix="/outlet")

app.register_blueprint(customer_bp, url_prefix="/customer")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)