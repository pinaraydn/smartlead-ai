
import os
import sqlite3
from datetime import timedelta
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__)

DB_PATH = os.environ.get("AUTH_DB_PATH", "users.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_auth_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isim TEXT NOT NULL,
                soyad TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)

@auth_bp.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}

    isim = str(data.get("isim") or "").strip()
    soyad = str(data.get("soyad") or "").strip()
    email = str(data.get("email") or "").strip().lower()
    password = str(data.get("password") or "")

    if not all([isim, soyad, email, password]):
        return jsonify(error="Tüm alanları doldurun."), 400

    if "@" not in email or len(password) < 8:
        return jsonify(error="E-posta geçersiz veya şifre 8 karakterden kısa."), 400

    try:
        with get_db() as conn:
            conn.execute(
                """INSERT INTO users
                   (isim, soyad, email, password_hash)
                   VALUES (?, ?, ?, ?)""",
                (isim, soyad, email, generate_password_hash(password))
            )
    except sqlite3.IntegrityError:
        return jsonify(error="Bu e-posta zaten kayıtlı."), 409

    return jsonify(message="Kayıt başarılı!"), 201

@auth_bp.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}
    email = str(data.get("email") or "").strip().lower()
    password = str(data.get("password") or "")

    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

    if not user or not check_password_hash(
        user["password_hash"], password
    ):
        return jsonify(error="E-posta veya şifre hatalı."), 401

    session.clear()
    session["user_id"] = user["id"]

    return jsonify(
        message="Giriş başarılı!",
        isim=user["isim"]
    )

@auth_bp.get("/api/me")
def me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify(error="Giriş yapmalısınız."), 401

    with get_db() as conn:
        user = conn.execute(
            "SELECT id, isim, soyad, email FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

    if not user:
        return jsonify(error="Kullanıcı bulunamadı."), 401

    return jsonify(dict(user))

@auth_bp.post("/api/logout")
def logout():
    session.clear()
    return jsonify(message="Çıkış yapıldı.")
