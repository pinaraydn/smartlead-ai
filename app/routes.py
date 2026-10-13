
from flask import Blueprint

from app.controllers import api_controller
from app.controllers import page_controller


api_bp = Blueprint("api", __name__)
pages_bp = Blueprint("pages", __name__)


# ============================================================
# CHAT API
# ============================================================

api_bp.add_url_rule(
    "/chat",
    endpoint="chat",
    view_func=api_controller.chat,
    methods=["POST"],
)

api_bp.add_url_rule(
    "/sohbet",
    endpoint="sohbet",
    view_func=api_controller.chat,
    methods=["POST"],
)

api_bp.add_url_rule(
    "/reset",
    endpoint="reset_chat",
    view_func=api_controller.reset_chat,
    methods=["POST"],
)


# ============================================================
# MUSTERI KAYIT API
# ============================================================

api_bp.add_url_rule(
    "/leads",
    endpoint="create_lead",
    view_func=api_controller.create_lead,
    methods=["POST"],
)

api_bp.add_url_rule(
    "/leads",
    endpoint="list_leads",
    view_func=api_controller.list_leads,
    methods=["GET"],
)

api_bp.add_url_rule(
    "/leads/<int:lead_id>",
    endpoint="remove_lead",
    view_func=api_controller.remove_lead,
    methods=["DELETE"],
)


# ============================================================
# GENEL SAYFALAR
# ============================================================

pages_bp.add_url_rule(
    "/",
    endpoint="index",
    view_func=page_controller.index,
    methods=["GET"],
)

pages_bp.add_url_rule(
    "/health",
    endpoint="health",
    view_func=page_controller.health,
    methods=["GET"],
)


# ============================================================
# YONETIM PANELI
# ============================================================

pages_bp.add_url_rule(
    "/dashboard/login",
    endpoint="dashboard_login",
    view_func=page_controller.dashboard_login,
    methods=["GET", "POST"],
)

pages_bp.add_url_rule(
    "/dashboard",
    endpoint="dashboard",
    view_func=page_controller.dashboard,
    methods=["GET"],
)

pages_bp.add_url_rule(
    "/dashboard/delete/<int:lead_id>",
    endpoint="dashboard_delete",
    view_func=page_controller.dashboard_delete,
    methods=["POST"],
)

pages_bp.add_url_rule(
    "/dashboard/logout",
    endpoint="dashboard_logout",
    view_func=page_controller.dashboard_logout,
    methods=["POST"],
)
