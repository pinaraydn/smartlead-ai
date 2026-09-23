from groq import Groq
from config import Config

client = Groq(api_key=Config.GROQ_API_KEY)

SYSTEM_MESSAGE = Config.BUSINESS_CONTEXT + """
SOHBET AKIŞI:
1. Kullanıcı adını ve soyadını paylaştığında ismiyle selamla ve
   şu seçenekleri alt alta sun:
   1. Sanal Deneme Odası Hakkında Bilgi
   2. Dijital İkiz ve Entegrasyon
   3. Demo Görüşmesi Talebi
   4. Kayıt Silme Talebi

2. Kullanıcı demo görüşmesi isterse ihtiyacını ve tercih ettiği
   görüşme zamanını sor. İletişim bilgilerini gönüllü olarak
   paylaşabileceğini belirt.

3. Kullanıcı iletişim bilgilerini zaten paylaştıysa tekrar isteme.

4. Sistemden işlem sonucu gelmedikçe randevu oluşturulduğunu,
   kayıt alındığını veya kayıt silindiğini iddia etme.

5. Yanıtlarında tablo veya dikey çizgi kullanma.
"""


def ask_fashtech_ai(user_message, conversation_history=None):
    """
    conversation_history: Yalnızca bu ziyaretçiye ait önceki mesajlar.
    Güncellenmiş geçmişi yanıtla birlikte döndürür.
    """
    history = list(conversation_history or [])
    messages = [
        {"role": "system", "content": SYSTEM_MESSAGE},
        *history,
        {"role": "user", "content": user_message},
    ]

    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        temperature=0.7,
        max_tokens=1024,
    )

    ai_response = completion.choices[0].message.content or ""
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": ai_response})

    return ai_response, history