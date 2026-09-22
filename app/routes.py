from flask import Blueprint, render_template, request, jsonify
from app.ai_service import ask_fashtech_ai, reset_ai_history
from app.database import get_db, add_lead, delete_lead
import re

main_bp = Blueprint('main', __name__)

active_user_name = "FashTech Müşterisi"
active_topic = "Genel Bilgi / Seçim Yapılmadı"
active_email = "Belirtilmedi"
active_appointment = "Belirtilmedi" 

@main_bp.route('/')
def index():
    global active_user_name, active_topic, active_email, active_appointment
    active_user_name = "FashTech Müşterisi"
    active_topic = "Genel Bilgi / Seçim Yapılmadı"
    active_email = "Belirtilmedi"
    active_appointment = "Belirtilmedi"
    return render_template('index.html')

@main_bp.route('/api/chat', methods=['POST'])
def chat():
    global active_user_name, active_topic, active_email, active_appointment
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'response': 'Lütfen bir mesaj yazın.'}), 400

    digits_only = "".join(filter(str.isdigit, user_message))
    is_phone_attempt = '5' in user_message and len(digits_only) >= 7

    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match_email = re.search(email_pattern, user_message)

    if match_email:
        active_email = match_email.group(0)

    if not is_phone_attempt and not match_email and not digits_only and user_message not in ['1', '2', '3', '4']:
        lower_msg = user_message.lower()
        if any(keyword in lower_msg for keyword in ['saat', 'bugün', 'yarın', 'pazartesi', 'salı', 'çarşamba', 'perşembe', 'cuma', 'cumartesi', 'pazar', 'sabah', 'akşam', 'öğleden', ':']):
            active_appointment = user_message

    if user_message == '1':
        active_topic = "3D Sanal Deneme Odası Hakkında Bilgi"
    elif user_message == '2':
        active_topic = "Dijital İkiz Çözümleri ve Entegrasyon"
    elif user_message == '3':
        active_topic = "Demo ve Randevu Talebi"
    elif user_message == '4':
        active_topic = "Randevu / Kayıt Silme Talebi"
    elif not is_phone_attempt and not match_email and not digits_only and len(user_message) < 40:
        lower_msg = user_message.lower()
        if lower_msg not in ['selam', 'merhaba', 'evet', 'hayır']:
            active_user_name = user_message.title()

    valid_pattern = r'\b(?:0?5[0-9]{9})(?!\d)\b'
    match_valid = re.search(valid_pattern, user_message)

    ai_response = ask_fashtech_ai(user_message)

    if is_phone_attempt:
        if match_valid:
            phone = match_valid.group(0)
            if len(phone) == 11 and phone.startswith('0'):
                phone = phone[1:]

            if len(set(phone)) == 1 or phone in ["5111111111", "5222222222", "5333333333", "5444444444", "5555555555", "5666666666", "5777777777", "5888888888", "5999999999", "5000000000"]:
                ai_response = "Girdiğiniz telefon numarası geçersiz görünüyor. Lütfen başında 0 olmadan, 5 ile başlayan ve tam 10 haneli geçerli bir telefon numarası girin."
            else:
                try:
                    lead_name = active_user_name if active_user_name != "FashTech Müşterisi" else "FashTech Müşterisi"
                    
                    summary_text = f"Konu: {active_topic} | Randevu: {active_appointment} | Tel: {phone} | Mail: {active_email}"
                    
                    add_lead(
                        name=lead_name,
                        phone=phone,
                        message=user_message,
                        chat_summary=summary_text
                    )
                except Exception as e:
                    print("Veritabanı kayıt hatası:", e)
        else:
            ai_response = "Telefon numaranızı eksik veya hatalı girdiniz. Lütfen başında 0 olmadan, 5 ile başlayan ve tam 10 haneli olacak şekilde tekrar girin."

    elif '@' in user_message or 'gmail' in user_message.lower() or 'hotmail' in user_message.lower() or 'outlook' in user_message.lower():
        if not match_email:
            ai_response = "E-posta adresiniz eksik veya hatalı görünüyor. Lütfen @gmail.com veya @hotmail.com gibi geçerli bir uzantıyla tam olarak yazın."

    return jsonify({'response': ai_response})

@main_bp.route('/api/reset', methods=['POST'])
def reset_chat():
    global active_user_name, active_topic, active_email, active_appointment
    active_user_name = "FashTech Müşterisi"
    active_topic = "Genel Bilgi / Seçim Yapılmadı"
    active_email = "Belirtilmedi"
    active_appointment = "Belirtilmedi"
    reset_ai_history()
    return jsonify({"status": "success", "message": "Oturum ve yapay zeka hafızası sıfırlandı."})

@main_bp.route('/dashboard')
def dashboard():
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, name, phone, chat_summary FROM leads ORDER BY id DESC")
        leads = cursor.fetchall()
    except Exception as e:
        print("Veritabanı okuma hatası:", e)
        leads = []
        
    return render_template('dashboard.html', leads=leads)

@main_bp.route('/dashboard/delete/<int:lead_id>', methods=['POST'])
def remove_lead(lead_id):
    try:
        delete_lead(lead_id)
    except Exception as e:
        print("Silme hatası:", e)
    return jsonify({"status": "success"})