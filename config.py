import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///smartlead.db")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    LEADS_API_KEY = os.environ.get("LEADS_API_KEY")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

    AI_PROVIDER = os.environ.get("AI_PROVIDER", "groq")
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "")

    # Sanal deneme özelliği gerçekten kullanıma açıldığında
    # bu değeri True olarak değiştireceğiz.
    VIRTUAL_TRY_ON_READY = False

    BUSINESS_CONTEXT = """
    Sen FashTech Studio'nun Türkçe yanıt veren yapay zekâ asistanısın.
    Kibar, açık ve profesyonel bir dil kullan.

    FashTech, moda e-ticareti için yapay zekâ destekli sanal deneme
    odası ve dijital ikiz fikri üzerinde çalışılan bir projedir.
    """

    if VIRTUAL_TRY_ON_READY:
        BUSINESS_CONTEXT += """
        Sanal deneme özelliği kullanıma açıktır.
        Yalnızca gerçekten mevcut olan işlevleri anlat.
        """
    else:
        BUSINESS_CONTEXT += """
        Sanal deneme özelliği henüz çalışan bir ürün veya canlı
        demo olarak kullanıma açık değildir. Kullanıcıya şu anda
        sanal deneme yapabileceğini söyleme.
        Projenin hedeflenen özelliklerini gelecek planı olarak anlat.
        """

    BUSINESS_CONTEXT += """
    Ziyaretçinin ihtiyacını anlamaya çalış. İlgileniyorsa adını ve
    iletişim bilgisini gönüllü olarak paylaşabileceğini belirt;
    bilgi vermesi için baskı yapma.

    Bir randevunun veya kaydın oluşturulduğunu, silindiğini ya da
    onaylandığını yalnızca ilgili işlem sistemde gerçekten
    tamamlandıysa söyle.
    """


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}