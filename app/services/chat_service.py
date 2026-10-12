
import re


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

        name = extract_name(message)
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

        name = extract_name(message)

        if name and not phone_match and not email_match:
            self.state["name"] = name

        return phone_match

    def update_appointment(self, message, phone_match):
        time_keywords = (
            "saat", "bugün", "yarın", "pazartesi",
            "salı", "çarşamba", "perşembe", "cuma",
            "cumartesi", "pazar", "sabah", "akşam",
            "öğleden"
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
