
# FashTech Studio | SmartLead AI

## Proje Hakkında

FashTech Studio, yapay zekâ destekli bir moda teknolojisi platformu olarak planlanmaktadır. Dijital ikiz ve sanal kıyafet deneme gibi özellikler projenin gelecek hedefleri arasındadır.

Bu proje kapsamında geliştirilen **SmartLead AI MVP**, kullanıcılarla sohbet eden, müşteri taleplerini kaydeden ve bu taleplerin yönetilmesini sağlayan çalışan bir prototiptir.

## Geliştirilen Özellikler

- Groq API destekli yapay zekâ sohbet asistanı
- Demo görüşmesi ve kayıt silme taleplerinin alınması
- Müşteri bilgilerinin SQLite veritabanına kaydedilmesi
- Kayıtları görüntüleme, arama ve silme özelliklerine sahip Flask yönetim paneli
- Wix Studio üzerinde oluşturulan ayrı yönetim paneli
- Wix arayüzü ile Flask backend arasında API bağlantısı

**Not:** Kayıt silme talebi, müşteri kaydını otomatik olarak silmez; talep yönetici incelemesine iletilir.

## Kullanılan Teknolojiler

| Teknoloji | Kullanım |
| --- | --- |
| Python & Flask | Backend ve API |
| Wix Studio | Web arayüzü |
| Groq API | Yapay zekâ sohbet asistanı |
| SQLite | Müşteri kayıtları |
| Render | Backend yayını |
| GitHub | Kaynak kod yönetimi |

## Canlı Bağlantılar

- **Wix sitesi:** https://aydinpinar2005.wixstudio.com/fashtech-studio
- **Flask backend:** https://smartlead-ai-d6ue.onrender.com/
- **Flask yönetim paneli:** https://smartlead-ai-d6ue.onrender.com/dashboard

Yönetim panellerine erişim yetkilendirme gerektirir.

## Yerel Kurulum

```bash
git clone https://github.com/pinaraydn/smartlead-ai.git
cd smartlead-ai
python -m venv venv
```

Windows PowerShell'de sanal ortamı etkinleştirin:

```powershell
.\venv\Scripts\Activate.ps1
```

Bağımlılıkları yükleyin:

```bash
pip install -r requirements.txt
```

Projenin ana klasöründe `.env` dosyası oluşturup gerekli API anahtarını ve yönetici şifresini tanımlayın. **Gerçek anahtarları ve şifreleri GitHub'a yüklemeyin.**

Uygulamayı başlatın:

```bash
python run.py
```

## Proje Durumu

SmartLead AI MVP'nin sohbet asistanı, kayıt sistemi ve iki yönetim paneli geliştirilmiştir. Dijital ikiz ve sanal kıyafet deneme özellikleri ilerleyen aşamalar için planlanmaktadır.