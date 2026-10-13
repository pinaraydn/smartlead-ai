
import hmac
import secrets
from functools import wraps

from flask import (
    abort,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.database import delete_lead, get_all_leads


def index():
    return render_template("index.html")


def health():
    return jsonify({
        "status": "ok",
        "basari": True,
    })


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("flask_admin_authenticated"):
            return redirect(url_for("pages.dashboard_login"))

        return view(*args, **kwargs)

    return wrapped_view


def admin_csrf_token():
    token = session.get("flask_admin_csrf_token")

    if not token:
        token = secrets.token_hex(32)
        session["flask_admin_csrf_token"] = token

    return token


def valid_admin_csrf_token():
    expected = session.get("flask_admin_csrf_token", "")
    provided = request.form.get("csrf_token", "")

    return bool(
        expected
        and provided
        and hmac.compare_digest(expected, provided)
    )


def dashboard_login():
    if session.get("flask_admin_authenticated"):
        return redirect(url_for("pages.dashboard"))

    if request.method == "GET":
        return render_template(
            "dashboard_login.html",
            error=None,
            csrf_token=admin_csrf_token(),
        )

    if not valid_admin_csrf_token():
        abort(403)

    expected_password = current_app.config.get("ADMIN_PASSWORD")
    entered_password = request.form.get("password", "")

    if not expected_password:
        current_app.logger.error(
            "ADMIN_PASSWORD ortam değişkeni tanımlanmamış."
        )
        return render_template(
            "dashboard_login.html",
            error="Yönetici girişi henüz yapılandırılmamış.",
            csrf_token=admin_csrf_token(),
        ), 503

    if not hmac.compare_digest(
        entered_password.encode("utf-8"),
        expected_password.encode("utf-8"),
    ):
        return render_template(
            "dashboard_login.html",
            error="Şifre hatalı.",
            csrf_token=admin_csrf_token(),
        ), 401

    session.clear()
    session["flask_admin_authenticated"] = True
    session["flask_admin_csrf_token"] = secrets.token_hex(32)

    return redirect(url_for("pages.dashboard"))


@admin_required
def dashboard():
    try:
        leads = get_all_leads()
    except Exception:
        current_app.logger.exception(
            "Flask yönetim panelinde kayıtlar alınamadı."
        )
        return "Müşteri kayıtları şu anda yüklenemiyor.", 500

    response = current_app.make_response(
        render_template(
            "dashboard.html",
            leads=leads,
            csrf_token=admin_csrf_token(),
        )
    )

    response.headers["Cache-Control"] = "no-store"
    return response


@admin_required
def dashboard_delete(lead_id):
    if not valid_admin_csrf_token():
        abort(403)

    try:
        delete_lead(lead_id)
    except Exception:
        current_app.logger.exception(
            "Flask yönetim panelinde kayıt silinemedi."
        )
        return "Kayıt silinemedi.", 500

    return redirect(url_for("pages.dashboard"))


@admin_required
def dashboard_logout():
    if not valid_admin_csrf_token():
        abort(403)

    session.clear()
    return redirect(url_for("pages.dashboard_login"))
