import os
from groq import Groq
from config import Config

client = Groq(api_key=Config.GROQ_API_KEY)

# Sohbet geçmişini saklayacağımız liste (oturum hafızası)
conversation_history = [
    {
       "role": "system",
        "content": """Sen FashTech Studio'nun profesyonel ve satış odaklı yapay zeka asistanısın. 
Şirketimiz e-ticaret markaları için 3D sanal deneme odası (Virtual Fitting Room) ve dijital ikiz çözümleri sunar.

KESİN AKIŞ KURALLARI:
1. Kullanıcı adını ve soyadını yazdığında, onu ismiyle selamla ve hemen şu 4 seçeneği alt alta sun:
   "Sayın [Kullanıcının Adı Soyadı], hangi konuda bilgi almak istersiniz? Lütfen bir numara seçin:
   
   1. 3D Sanal Deneme Odası (Virtual Fitting Room) Hakkında Bilgi
   2. Dijital İkiz Çözümleri ve Entegrasyon
   3. Demo ve Randevu Talebi Oluşturma
   4. Randevu / Kayıt Silme Talebi"

2. SEÇİM YAPILDIĞINDA:
   - Kullanıcı özellikle "3" (Demo ve Randevu) seçerse, ilgili bilgiyi verdikten sonra mutlaka **"Görüşmek istediğiniz gün ve saati (Örn: Yarın saat 14:00) yazar mısınız?"** diye sor ve ardından telefon ile e-posta iste.

3. BİLGİLER ALINDIĞINDA: Kullanıcı telefon ve e-postasını paylaştığında bir daha isteme, kayıt alındığını belirt.
4. Asla dikey çizgi (|) veya tablo kullanma, seçenekleri alt alta yaz."""
    }
]

def ask_fashtech_ai(user_message):
    try:
        conversation_history.append({"role": "user", "content": user_message})

        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=conversation_history,
            temperature=0.7,
            max_tokens=1024
        )
        
        ai_response = completion.choices[0].message.content
        
        conversation_history.append({"role": "assistant", "content": ai_response})

        return ai_response
    except Exception as e:
        return f"Bir hata oluştu: {str(e)}"

def reset_ai_history():
    global conversation_history
    # Sayfa yenilendiğinde önceki konuşmaları siler, sadece sistem kurallarını bırakır
    conversation_history = [conversation_history[0]]