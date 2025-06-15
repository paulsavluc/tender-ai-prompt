# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    UPLOAD_FOLDER = 'uploads'
    OUTPUT_FOLDER = 'outputs'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'xlsx', 'txt'}
    
    # Vector Database
    VECTOR_DB_PATH = './vector_db'
    
    # AI Settings
    AI_MODEL = 'gpt-4'
    AI_TEMPERATURE = 0.7
    MAX_TOKENS = 2000
