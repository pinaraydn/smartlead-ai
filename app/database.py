import sqlite3
from flask import g

DATABASE = 'smartlead.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db(app):
    with app.app_context():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                message TEXT,
                chat_summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.commit()

def add_lead(name, phone, message="", chat_summary=""):
    db = get_db()
    db.execute(
        'INSERT INTO leads (name, phone, message, chat_summary) VALUES (?, ?, ?, ?)',
        (name, phone, message, chat_summary)
    )
    db.commit()

def get_all_leads():
    db = get_db()
    cur = db.execute('SELECT * FROM leads ORDER BY created_at DESC')
    return [dict(row) for row in cur.fetchall()]
def delete_lead(lead_id):
    db = get_db()
    db.execute('DELETE FROM leads WHERE id = ?', (lead_id,))
    db.commit()