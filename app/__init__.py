import os

from flask_cors import CORS
from flask import Flask

from config import config_by_name
from app.database import init_db
from app.routes import api_bp, pages_bp


def create_app():
    app = Flask(__name__)

    # Yerelde geliştirme, Render'da üretim ayarlarını kullan.
    environment = os.environ.get("APP_ENV", "development")
    selected_config = config_by_name.get(
        environment,
        config_by_name["production"],
    )
    app.config.from_object(selected_config)
    origins = app.config.get("CORS_ORIGINS", "")
    origins = [origin.strip() for origin in origins.split(",") if origin.strip()]

    CORS(
        app,
        origins=origins,
        methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key"]
    )
    
    init_db(app)

    # API adresleri /api ile başlar; sayfa adresleri ayrı kalır.
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(pages_bp)

    return app