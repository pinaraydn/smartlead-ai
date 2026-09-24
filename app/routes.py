import hmac
import re

from flask import (
    Blueprint,
    current_app,
    jsonify,
    render_template,
    request,
    session,
)

from app.database import add_lead, get_all_leads, delete_lead
from app.services.ai_service import AIServiceError, ai_service


pages_bp = Blueprint("pages", __name__)
api_bp = Blueprint("api", __name__)

DEFAULT_NAME = "FashTech Müşterisi"
DEFAULT_TOPIC = "Genel Bilgi / Seçim Yapılmadı"

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)
PHONE_PATTERN = re.compile(r"(?<!\d)0?(5\d{9})(?!\d)")


def new_chat_state():
    return {
        "name": DEFAULT_NAME,
        "topic": DEFAULT_TOPIC,
        "email": "",
        "appointment": "",
        "history": [],
        "saved_phone": "",
    }


def api_error(message, status_code):
    return jsonify({
        "basari": False,
        "error": message,
        "response": message,
    }), status_code


def valid_leads_api_key():
    expected_key = current_app.config.get("LEADS_API_KEY")
    provided_key = request.headers.get("X-API-Key", "")

    return bool(
        expected_key
        and hmac.compare_digest(provided_key, expected_key)
    )


@pages_bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@pages_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "basari": True})


# Eski Flask yönetim paneli kapalı kalır.
@pages_bp.route("/dashboard", methods=["GET"])
@pages_bp.route("/dashboard/delete/<int:lead_id>", methods=["POST"])
def dashboard_temporarily_disabled(lead_id=None):
    return api_error(
        "Yönetim paneli güvenli erişim kurulana kadar kapalı.",
        403,
    )


@api_bp.route("/chat", methods=["POST"])
@api_bp.route("/sohbet", methods=["POST"])
def chat():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return api_error("Geçerli bir JSON isteği gönderin.", 400)

    user_message = data.get("mesaj", data.get("message", ""))

    if not isinstance(user_message, str):
        return api_error("Mesaj metin olmalıdır.", 400)

    user_message = user_message.strip()

    if not user_message:
        return api_error("Lütfen bir mesaj yazın.", 400)

    if len(user_message) > 2000:
        return api_error("Mesajınız çok uzun.", 400)

    state = session.get("chat_state") or new_chat_state()

    # Wix konuşma geçmişini her istekte ayrıca gönderebilir.
    if "gecmis" in data:
        incoming_history = data["gecmis"]

        if not isinstance(incoming_history, list) or len(incoming_history) > 8:
            return api_error("Geçersiz sohbet geçmişi.", 400)

        valid_history = all(
            isinstance(item, dict)
            and item.get("role") in ("user", "assistant")
            and isinstance(item.get("content"), str)
            and 0 < len(item["content"]) <= 4000
            for item in incoming_history
        )

        if not valid_history:
            return api_error("Geçersiz sohbet geçmişi.", 400)

        state["history"] = incoming_history

    email_match = EMAIL_PATTERN.search(user_message)
    phone_match = PHONE_PATTERN.search(user_message)

    if email_match:
        state["email"] = email_match.group(0)

    topics = {
        "1": "Sanal Deneme Odası Hakkında Bilgi",
        "2": "Dijital İkiz ve Entegrasyon",
        "3": "Demo Görüşmesi Talebi",
        "4": "Kayıt Silme Talebi",
    }

    if user_message in topics:
        state["topic"] = topics[user_message]

    lower_message = user_message.lower()

    time_keywords = (
        "saat",
        "bugün",
        "yarın",
        "pazartesi",
        "salı",
        "çarşamba",
        "perşembe",
        "cuma",
        "cumartesi",
        "pazar",
        "sabah",
        "akşam",
        "öğleden",
    )

    if (
        not phone_match
        and not email_match
        and user_message not in topics
        and any(word in lower_message for word in time_keywords)
    ):
        state["appointment"] = user_message

    name_match = re.search(
        r"^(?:adım|ismim|benim adım)\s+"
        r"([A-Za-zÇĞİÖŞÜçğıöşü]+(?:\s+[A-Za-zÇĞİÖŞÜçğıöşü]+){0,2})$",
        user_message,
        flags=re.IGNORECASE,
    )

    if name_match:
        state["name"] = name_match.group(1).title()

    try:
        ai_response, updated_history = ai_service.yanit_uret(
            user_message,
            state.get("history", []),
        )
    except AIServiceError:
        current_app.logger.exception("AI yanıtı alınamadı")
        return api_error(
            "Şu anda yanıt veremiyorum. Lütfen biraz sonra tekrar deneyin.",
            503,
        )

    state["history"] = updated_history[-8:]

    if phone_match:
        phone = phone_match.group(1)

        invalid_phone = (
            len(set(phone)) == 1
            or phone in {
                "5000000000",
                "5111111111",
                "5222222222",
                "5333333333",
                "5444444444",
                "5555555555",
                "5666666666",
                "5777777777",
                "5888888888",
                "5999999999",
            }
        )

        if invalid_phone:
            ai_response = (
                "Telefon numaranız geçersiz görünüyor. "
                "Lütfen 5 ile başlayan 10 haneli numaranızı kontrol edin."
            )

        elif state["name"] == DEFAULT_NAME:
            ai_response = (
                "Demo talebinizi kaydedebilmem için önce adınızı ve soyadınızı "
                "yazar mısınız? Örneğin: Adım Pınar Aydın"
            )

        elif state.get("saved_phone") != phone:
            try:
                add_lead(
                    name=state["name"],
                    phone=phone,
                    message=(
                        "Yapay zekâ asistanı üzerinden iletişim talebi. "
                        f"Konu: {state['topic']}"
                    ),
                    chat_summary=(
                        f"Konu: {state['topic']} | "
                        f"Randevu tercihi: {state['appointment']} | "
                        f"E-posta: {state['email'] or 'Belirtilmedi'}"
                    ),
                )
                state["saved_phone"] = phone
                ai_response = (
                    "İletişim bilgilerinizi aldık. "
                    "Bu bir görüşme veya randevu onayı değildir."
                )
            except Exception:
                current_app.logger.exception("Müşteri kaydı oluşturulamadı")
                ai_response = (
                    "Bilgilerinizi şu anda kaydedemedik. "
                    "Lütfen daha sonra tekrar deneyin."
                )

    session["chat_state"] = state

    return jsonify({
        "basari": True,
        "response": ai_response,
        "cevap": ai_response,
        "gecmis": state["history"],
    })


@api_bp.route("/reset", methods=["POST"])
def reset_chat():
    session.pop("chat_state", None)

    return jsonify({
        "basari": True,
        "status": "success",
        "message": "Bu ziyaretçinin sohbeti sıfırlandı.",
    })


@api_bp.route("/leads", methods=["POST"])
def create_lead():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return api_error("Geçerli bir JSON isteği gönderin.", 400)

    name = data.get("isim", data.get("name", ""))
    phone = data.get("telefon", data.get("phone", ""))
    message = data.get("mesaj", data.get("message", ""))

    if not isinstance(name, str) or not name.strip():
        return api_error("Lütfen adınızı girin.", 400)

    if not isinstance(phone, str) or not PHONE_PATTERN.fullmatch(phone.strip()):
        return api_error("Geçerli bir telefon numarası girin.", 400)

    if not isinstance(message, str):
        return api_error("Mesaj metin olmalıdır.", 400)

    name = name.strip()
    phone = PHONE_PATTERN.fullmatch(phone.strip()).group(1)

    if len(name) > 100 or len(message) > 2000:
        return api_error("Gönderilen bilgi çok uzun.", 400)

    try:
        add_lead(
            name=name,
            phone=phone,
            message=message.strip(),
        )
    except Exception:
        current_app.logger.exception("Müşteri kaydı oluşturulamadı")
        return api_error(
            "Bilgileriniz şu anda kaydedilemiyor. Lütfen tekrar deneyin.",
            500,
        )

    return jsonify({
        "basari": True,
        "message": "İletişim bilgileriniz kaydedildi.",
    }), 201


@api_bp.route("/leads", methods=["GET"])
def list_leads():
    if not valid_leads_api_key():
        return api_error("Yetkisiz erişim.", 403)

    try:
        leads = get_all_leads()
    except Exception:
        current_app.logger.exception("Müşteri kayıtları alınamadı")
        return api_error("Kayıtlar şu anda alınamıyor.", 500)

    return jsonify({
        "basari": True,
        "leads": leads,
    })


@api_bp.route("/leads/<int:lead_id>", methods=["DELETE"])
def remove_lead(lead_id):
    if not valid_leads_api_key():
        return api_error("Yetkisiz erişim.", 403)

    try:
        delete_lead(lead_id)
    except Exception:
        current_app.logger.exception("Müşteri kaydı silinemedi")
        return api_error("Kayıt silinemedi.", 500)

    return jsonify({
        "basari": True,
        "message": "Kayıt silindi.",
    })