import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-secret-key')
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///smartlead.db')
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    
    BUSINESS_CONTEXT = """You are the AI assistant for FashTech Studio. 
    Explain that we offer AI-powered virtual fitting room and digital twin solutions for e-commerce brands. 
    Be polite, professional, and persuasive. Always respond in Turkish.
    Ask about the customers' needs, introduce our system, and guide them to leave their contact information (name, phone number) to work with us."""