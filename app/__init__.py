
import os
from datetime import timedelta

from flask import Flask
from flask_cors import CORS

from config import config_by_name
from app.database import init_db
from app.routes import api_bp, pages_bp

# Kullanıcı kayıt ve giriş sistemi
from app.controllers.auth import auth_bp, init_auth_db


def create_app():
    app = Flask(__name__)

    environment = os.environ.get("APP_ENV", "development")
    selected_config = config_by_name.get(
        environment,
        config_by_name["production"],
    )

    app.config.from_object(selected_config)

    # Kullanıcı oturum ayarları
    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        raise RuntimeError("SECRET_KEY tanımlanmalıdır.")

    app.config["SECRET_KEY"] = secret_key
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = (
        environment != "development"
    )
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(
        hours=2
    )

    origins = app.config.get("CORS_ORIGINS", "")
    origins = [
        origin.strip()
        for origin in origins.split(",")
        if origin.strip()
    ]

    CORS(
        app,
        origins=origins,
        methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key"],
    )

    # Mevcut veritabanı
    init_db(app)

    # Kullanıcı veritabanı
    init_auth_db()

    # Mevcut API ve sayfalar
    app.register_blueprint(api_bp, url_prefix="/api")
    app.register_blueprint(pages_bp)

    # Yeni kayıt ve giriş API'leri
    app.register_blueprint(auth_bp)

    return app
