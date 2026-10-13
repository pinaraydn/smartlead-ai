
import hmac

from flask import current_app, jsonify, request, session

from app.services.ai_service import AIServiceError
from app.services.chat_service import (
    ChatService,
    build_chat_response,
    is_valid_history,
    new_chat_state,
    validate_chat_message,
    validate_lead_data,
)
from app.services.lead_service import LeadService


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


def chat():
    data = request.get_json(silent=True)

    user_message, error = validate_chat_message(data)

    if error:
        return api_error(error, 400)

    history = None

    if "gecmis" in data:
        history = data["gecmis"]

        if not is_valid_history(history):
            return api_error("Geçersiz sohbet geçmişi.", 400)

    state = session.get("chat_state") or new_chat_state()
    chat_service = ChatService(state)

    try:
        response = chat_service.process_message(
            user_message,
            history,
        )
    except AIServiceError:
        current_app.logger.exception("AI yanıtı alınamadı")
        return api_error(
            "Şu anda yanıt veremiyorum. "
            "Lütfen biraz sonra tekrar deneyin.",
            503,
        )

    result = build_chat_response(state, response)
    session["chat_state"] = state

    return jsonify(result)


def reset_chat():
    session.pop("chat_state", None)

    return jsonify({
        "basari": True,
        "status": "success",
        "message": "Bu ziyaretçinin sohbeti sıfırlandı.",
    })


def create_lead():
    data = request.get_json(silent=True)
    lead_data, error = validate_lead_data(data)

    if error:
        return api_error(error, 400)

    try:
        LeadService.create(lead_data)
    except Exception:
        current_app.logger.exception(
            "Müşteri kaydı oluşturulamadı"
        )
        return api_error(
            "Bilgileriniz şu anda kaydedilemiyor. "
            "Lütfen tekrar deneyin.",
            500,
        )

    return jsonify({
        "basari": True,
        "message": "İletişim bilgileriniz kaydedildi.",
    }), 201


def list_leads():
    if not valid_leads_api_key():
        return api_error("Yetkisiz erişim.", 403)

    try:
        leads = LeadService.get_all()
    except Exception:
        current_app.logger.exception("Müşteri kayıtları alınamadı")
        return api_error("Kayıtlar şu anda alınamıyor.", 500)

    return jsonify({
        "basari": True,
        "leads": leads,
    })


def remove_lead(lead_id):
    if not valid_leads_api_key():
        return api_error("Yetkisiz erişim.", 403)

    try:
        LeadService.delete(lead_id)
    except Exception:
        current_app.logger.exception("Müşteri kaydı silinemedi")
        return api_error("Kayıt silinemedi.", 500)

    return jsonify({
        "basari": True,
        "message": "Kayıt silindi.",
    })
