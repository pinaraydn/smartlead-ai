import requests

from config import Config


class AIServiceError(Exception):
    """Yapay zekâ servisinden yanıt alınamadığında kullanılır."""


class AIService:
    def __init__(self):
        self.api_key = Config.GROQ_API_KEY
        self.model = "openai/gpt-oss-20b"

    def sistem_talimati(self):
        return Config.BUSINESS_CONTEXT + """
SOHBET AKIŞI:
1. Kullanıcı henüz adını ve soyadını paylaşmadıysa yalnızca
   adını ve soyadını nazikçe sor. Seçenekleri henüz gösterme.

2. Kullanıcı yalnızca adını paylaşırsa sadece soyadını sor.
   Daha önce söylenen bilgileri ve FashTech'in özelliklerini
   tekrar anlatma.

3. Kullanıcı adını ve soyadını paylaştıktan sonra ismiyle selamla
   ve seçenekleri HER BİRİ AYRI SATIRDA olacak şekilde sun:

   1. Sanal Deneme Odası Hakkında Bilgi
   2. Dijital İkiz ve Entegrasyon
   3. Demo Görüşmesi Talebi
   4. Kayıt Silme Talebi

   Seçenekleri tek paragrafta, yan yana veya tirelerle yazma. 
   Seçeneklerden sonra bir satır ALTA İN. Kullanıcıdan bir seçenek seçmesini iste."Lütfen numara veya başlığı seçiniz." cümlesini ayrı bir satıra yaz.

4. Kullanıcı bir konu seçtiğinde yalnızca o konuyla ilgili yanıt ver.
   Seçenekleri yeniden listeleme; kullanıcı isterse tekrar göster.

5. Sanal deneme özelliğinin henüz kullanıma açık olmadığını,
   yalnızca kullanıcı bu özelliği sorduğunda veya konu bunu
   açıklamayı gerektirdiğinde belirt. Her yanıtta tekrarlama.

6. Kullanıcı demo görüşmesi isterse ihtiyacını ve tercih ettiği
   görüşme zamanını sor. İletişim bilgilerini gönüllü olarak
   paylaşabileceğini belirt; sonraki mesajlarda aynı isteği
   gereksiz yere tekrarlama.

7. Kullanıcının önceki mesajlarını dikkate al. Zaten verdiği
   bilgileri tekrar isteme ve daha önce açıkladığın konuları
   kullanıcı sormadıkça yeniden anlatma.

8. Sistemden işlem sonucu gelmedikçe randevu oluşturulduğunu,
   kayıt alındığını veya kayıt silindiğini iddia etme.

9. Kısa, doğal ve konuşmanın o anki aşamasına uygun yanıtlar ver.
   Yanıtlarında tablo veya dikey çizgi kullanma.

10. Kullanıcı adını ve soyadını paylaştıktan sonra seçenekleri
    göstermeden hemen önce yalnızca bir kez şu açıklamayı yap:
    "FashTech Studio henüz geliştirme aşamasındaki bir proje.
    Aşağıdaki başlıklardan birini seçerek planlanan özelliklerimiz
    hakkında bilgi alabilirsiniz."
    Bu açıklamayı sonraki mesajlarda gereksiz yere tekrarlama.

11. Sanal deneme odası, dijital ikiz ve entegrasyon özelliklerini
    mevcut ve çalışan hizmetler gibi anlatma. Henüz geliştirme
    aşamasında olduklarını belirt; "hedefliyoruz", "planlıyoruz",
    "amaçlıyoruz" gibi gelecek planını ifade eden sözcükler kullan.
    Gerçekte bulunmayan işlevler veya entegrasyonlar uydurma.
"""

    def groq_istegi(self, messages):
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1024,
                },
                timeout=30,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as error:
            raise AIServiceError("Yapay zekâ servisinden yanıt alınamadı.") from error

    def yanit_uret(self, mesaj, gecmis=None):
        history = list(gecmis or [])

        if not self.api_key:
            return (
                "Şu anda demo modundayım. Yapay zekâ bağlantısı henüz "
                "yapılandırılmadı; FashTech hakkında bilgi almak veya "
                "demo talebi bırakmak için iletişim formunu kullanabilirsiniz.",
                history,
            )

        messages = [
            {"role": "system", "content": self.sistem_talimati()},
            *history,
            {"role": "user", "content": mesaj},
        ]

        ai_response = self.groq_istegi(messages)

        history.append({"role": "user", "content": mesaj})
        history.append({"role": "assistant", "content": ai_response})

        return ai_response, history


ai_service = AIService()