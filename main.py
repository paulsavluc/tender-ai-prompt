# main.py
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, flash
import os
import json
from werkzeug.utils import secure_filename
from config import Config
from app.document_processor import DocumentProcessor
from app.ai_generator import AIResponseGenerator
from app.document_filler import DocumentFiller
from app.vector_store import VectorStore
import tempfile
import uuid

app = Flask(__name__)
app.config.from_object(Config)

# Initialize components
vector_store = VectorStore(app.config['VECTOR_DB_PATH'])
document_processor = DocumentProcessor()
ai_generator = AIResponseGenerator(app.config['OPENAI_API_KEY'], vector_store)
document_filler = DocumentFiller()

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    try:
        # Check if files are present
        if 'template' not in request.files:
            return jsonify({'error': 'No template file provided'}), 400
        
        template_file = request.files['template']
        reference_files = request.files.getlist('references')
        
        if template_file.filename == '':
            return jsonify({'error': 'No template file selected'}), 400
        
        if not allowed_file(template_file.filename):
            return jsonify({'error': 'Invalid template file format'}), 400
        
        # Save template file
        template_filename = secure_filename(template_file.filename)
        template_path = os.path.join(app.config['
