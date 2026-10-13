
import re

from flask import current_app
from app.database import add_lead, get_all_leads, delete_lead
from app.services.ai_service import ai_service
from app.services.lead_service import LeadService

DEFAULT_NAME = "FashTech Müşterisi"
DEFAULT_TOPIC = "Genel Bilgi / Seçim Yapılmadı"

TOPICS = {
    "1": "Sanal Deneme Odası Hakkında Bilgi",
    "2": "Dijital İkiz ve Entegrasyon",
    "3": "Demo Görüşmesi Talebi",
    "4": "Kayıt Silme Talebi",
}

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PHONE_PATTERN = re.compile(r"(?<!\d)0?(5\d{9})(?!\d)")

NAME_PATTERN = re.compile(
    r"^(?:(?:adım|ismim|benim adım)\s+)?"
    r"([A-Za-zÇĞİÖŞÜçğıöşü]+"
    r"(?:\s+[A-Za-zÇĞİÖŞÜçğıöşü]+){1,2})$",
    flags=re.IGNORECASE,
)


def new_chat_state():
    return {
        "name": DEFAULT_NAME,
        "topic": DEFAULT_TOPIC,
        "email": "",
        "appointment": "",
        "history": [],
        "saved_phone": "",
        "saved_action": "",
    }


def extract_name(message):
    message = message.strip().rstrip(".!?")
    match = NAME_PATTERN.fullmatch(message)
    return match.group(1).title() if match else None


def restore_state_from_history(state, history):
    for item in history:
        if item["role"] != "user":
            continue

        message = item["content"].strip()

        if message in TOPICS:
            state["topic"] = TOPICS[message]

        name_message = PHONE_PATTERN.sub("", message).strip()
        name = extract_name(name_message)

        if name:
            state["name"] = name

        email = EMAIL_PATTERN.search(message)
        if email:
            state["email"] = email.group(0)

    for item in history:
        if item["role"] != "assistant":
            continue

        content = item["content"]

        if "DEMO_TALEBI_KAYDEDILDI" in content:
            state["saved_action"] = "demo"

        if "SILME_TALEBI_KAYDEDILDI" in content:
            state["saved_action"] = "delete"


def set_last_assistant_message(history, response):
    if history and history[-1].get("role") == "assistant":
        history[-1]["content"] = response

    return history[-8:]

def build_chat_response(state, response):
    state["history"] = set_last_assistant_message(
        state["history"], response
    )

    return {
        "basari": True,
        "response": response,
        "cevap": response,
        "gecmis": state["history"],
    }

def is_valid_history(history):
    return (
        isinstance(history, list)
        and len(history) <= 8
        and all(
            isinstance(item, dict)
            and item.get("role") in ("user", "assistant")
            and isinstance(item.get("content"), str)
            and 0 < len(item["content"]) <= 4000
            for item in history
        )
    )

def validate_chat_message(data):
    if not isinstance(data, dict):
        return None, "Geçerli bir JSON isteği gönderin."

    message = data.get("mesaj", data.get("message", ""))

    if not isinstance(message, str):
        return None, "Mesaj metin olmalıdır."

    message = message.strip()

    if not message:
        return None, "Lütfen bir mesaj yazın."

    if len(message) > 2000:
        return None, "Mesajınız çok uzun."

    return message, None

def validate_lead_data(data):
    if not isinstance(data, dict):
        return None, "Geçerli bir JSON isteği gönderin."

    name = data.get("isim", data.get("name", ""))
    phone = data.get("telefon", data.get("phone", ""))
    message = data.get("mesaj", data.get("message", ""))

    if not isinstance(name, str) or not name.strip():
        return None, "Lütfen adınızı girin."

    if not isinstance(phone, str):
        return None, "Geçerli bir telefon numarası girin."

    phone_match = PHONE_PATTERN.fullmatch(phone.strip())

    if not phone_match:
        return None, "Geçerli bir telefon numarası girin."

    if not isinstance(message, str):
        return None, "Mesaj metin olmalıdır."

    name = name.strip()
    phone = phone_match.group(1)

    if len(name) > 100 or len(message) > 2000:
        return None, "Gönderilen bilgi çok uzun."

    return {
        "name": name,
        "phone": phone,
        "message": message.strip(),
    }, None


class ChatService:
    """Sohbet durumunu ve mesaj bilgilerini yönetir."""

    def __init__(self, state):
        self.state = state

    def update_message_info(self, message):
        email_match = EMAIL_PATTERN.search(message)
        phone_match = PHONE_PATTERN.search(message)

        if email_match:
            self.state["email"] = email_match.group(0)

        if message in TOPICS:
            self.state["topic"] = TOPICS[message]
            self.state["saved_action"] = ""
            self.state["saved_phone"] = ""

        name_message = PHONE_PATTERN.sub("", message).strip()
        name = extract_name(name_message)

        if name and not email_match:
            self.state["name"] = name

        return phone_match

    def update_appointment(self, message, phone_match):
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
            self.state["topic"] == "Demo Görüşmesi Talebi"
            and not phone_match
            and not EMAIL_PATTERN.search(message)
            and message not in TOPICS
            and any(
                word in message.lower()
                for word in time_keywords
            )
        ):
            self.state["appointment"] = message

    @staticmethod
    def is_invalid_phone(phone):
        invalid_numbers = {
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

        return len(set(phone)) == 1 or phone in invalid_numbers

    def handle_demo_request(self, phone):
        if self.state["name"] == DEFAULT_NAME:
            return (
                "Demo talebinizi kaydedebilmem için önce adınızı "
                "ve soyadınızı yazar mısınız?"
            )

        if (
            self.state.get("saved_action") == "demo"
            and self.state.get("saved_phone") == phone
        ):
            return "Demo talebiniz daha önce kaydedildi."

        try:
            add_lead(
                name=self.state["name"],
                phone=phone,
                message=(
                    "Yapay zekâ asistanı üzerinden demo talebi. "
                    f"Konu: {self.state['topic']}"
                ),
                chat_summary=(
                    f"Konu: {self.state['topic']} | "
                    f"Randevu tercihi: {self.state['appointment']} | "
                    f"E-posta: "
                    f"{self.state['email'] or 'Belirtilmedi'}"
                ),
            )

            self.state["saved_phone"] = phone
            self.state["saved_action"] = "demo"

            return (
                "DEMO_TALEBI_KAYDEDILDI\n"
                "Demo talebinizi kaydettik. "
                "Bu bir görüşme veya randevu onayı değildir."
            )

        except Exception:
            current_app.logger.exception(
                "Demo talebi oluşturulamadı"
            )
            return (
                "Bilgilerinizi şu anda kaydedemedik. "
                "Lütfen daha sonra tekrar deneyin."
            )

    def handle_delete_request(self, phone):
        if self.state["name"] == DEFAULT_NAME:
            return (
                "Silme talebinizi iletebilmem için önce adınızı "
                "ve soyadınızı yazar mısınız?"
            )

        if (
            self.state.get("saved_action") == "delete"
            and self.state.get("saved_phone") == phone
        ):
            return (
                "Silme talebiniz daha önce iletildi. "
                "Kaydınız henüz silinmedi."
            )

        try:
            add_lead(
                name=self.state["name"],
                phone=phone,
                message=(
                    "KAYIT SİLME TALEBİ — "
                    "Yapay zekâ asistanı üzerinden iletildi. "
                    "Mevcut müşteri kaydı otomatik silinmedi."
                ),
                chat_summary=(
                    f"Talepte bulunan: {self.state['name']} | "
                    f"Telefon: {phone} | "
                    "Yetkili tarafından incelenmesi gerekiyor."
                ),
            )

            self.state["saved_phone"] = phone
            self.state["saved_action"] = "delete"

            return (
                "SILME_TALEBI_KAYDEDILDI\n"
                "Kayıt silme talebinizi inceleme için ilettim. "
                "Kaydınız henüz silinmedi. "
                "Bu işlem kimlik doğrulaması veya silme onayı değildir."
            )

        except Exception:
            current_app.logger.exception(
                "Kayıt silme talebi oluşturulamadı"
            )
            return (
                "Silme talebinizi şu anda iletemedim. "
                "Lütfen daha sonra tekrar deneyin."
            )

    def handle_response(self, message, phone_match, ai_response):
        if message == "4":
            if self.state["name"] != DEFAULT_NAME:
                return (
                    "Kayıt silme talebinizi iletmek için kayıtta "
                    "kullandığınız telefon numaranızı paylaşın. "
                    "Talebiniz incelenmek üzere iletilecek; "
                    "kaydınız otomatik olarak silinmeyecektir."
                )

            return (
                "Kayıt silme talebinizi iletmek için adınızı, "
                "soyadınızı ve kayıtta kullandığınız telefon "
                "numaranızı paylaşın. Talebiniz incelenmek üzere "
                "iletilecek; kaydınız otomatik olarak silinmeyecektir."
            )

        if message == "3":
            if self.state["name"] != DEFAULT_NAME:
                return (
                    "Demo görüşmesi talebiniz için telefon numaranızı "
                    "paylaşabilirsiniz. İsterseniz görüşme için "
                    "uygun olduğunuz zamanı da belirtin."
                )

            return (
                "Demo görüşmesi talebiniz için adınızı, soyadınızı "
                "ve telefon numaranızı paylaşabilirsiniz. "
                "İsterseniz görüşme için uygun olduğunuz zamanı da belirtin."
            )

        if phone_match:
            phone = phone_match.group(1)

            if self.is_invalid_phone(phone):
                return (
                    "Telefon numaranız geçersiz görünüyor. "
                    "Lütfen 5 ile başlayan 10 haneli numaranızı kontrol edin."
                )

            if self.state["topic"] == "Kayıt Silme Talebi":
                return self.handle_delete_request(phone)

            if self.state["topic"] == "Demo Görüşmesi Talebi":
                return self.handle_demo_request(phone)

            return (
                "Demo talebi oluşturmak için 3 numaralı, "
                "kayıt silme talebi iletmek için 4 numaralı "
                "seçeneği seçebilirsiniz."
            )

        return ai_response

    def process_message(self, message, history=None):
        if history is not None:
            self.state["history"] = history
            restore_state_from_history(self.state, history)

        phone_match = self.update_message_info(message)
        self.update_appointment(message, phone_match)

        ai_response, updated_history = ai_service.yanit_uret(
            message,
            self.state.get("history", []),
        )

        self.state["history"] = updated_history[-8:]

        return self.handle_response(
            message,
            phone_match,
            ai_response,
        )
