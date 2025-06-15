# app/utils.py
import os
import re
import json
import hashlib
import mimetypes
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import logging
from pathlib import Path
import shutil
import zipfile
import tempfile
from werkzeug.utils import secure_filename

class FileUtils:
    """Utility functions for file operations"""
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get file extension from filename"""
        return os.path.splitext(filename)[1].lower()
    
    @staticmethod
    def get_file_size(filepath: str) -> int:
        """Get file size in bytes"""
        try:
            return os.path.getsize(filepath)
        except OSError:
            return 0
    
    @staticmethod
    def get_file_hash(filepath: str) -> str:
        """Generate MD5 hash of file"""
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""
    
    @staticmethod
    def ensure_directory(directory: str) -> bool:
        """Ensure directory exists, create if not"""
        try:
            os.makedirs(directory, exist_ok=True)
            return True
        except Exception as e:
            logging.error(f"Failed to create directory {directory}: {e}")
            return False
    
    @staticmethod
    def clean_filename(filename: str) -> str:
        """Clean filename for safe storage"""
        # Remove or replace problematic characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove multiple underscores
        filename = re.sub(r'_+', '_', filename)
        # Limit length
        name, ext = os.path.splitext(filename)
        if len(name) > 50:
            name = name[:50]
        return name + ext
    
    @staticmethod
    def get_mime_type(filepath: str) -> str:
        """Get MIME type of file"""
        mime_type, _ = mimetypes.guess_type(filepath)
        return mime_type or 'application/octet-stream'
    
    @staticmethod
    def create_zip_archive(files: List[str], output_path: str) -> bool:
        """Create ZIP archive from list of files"""
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in files:
                    if os.path.exists(file_path):
                        arcname = os.path.basename(file_path)
                        zipf.write(file_path, arcname)
            return True
        except Exception as e:
            logging.error(f"Failed to create ZIP archive: {e}")
            return False
    
    @staticmethod
    def cleanup_old_files(directory: str, max_age_days: int = 7) -> int:
        """Clean up files older than specified days"""
        if not os.path.exists(directory):
            return 0
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        deleted_count = 0
        
        try:
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if file_time < cutoff_date:
                        os.remove(filepath)
                        deleted_count += 1
        except Exception as e:
            logging.error(f"Error cleaning up files: {e}")
        
        return deleted_count

class TextUtils:
    """Utility functions for text processing"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove non-printable characters
        text = ''.join(char for char in text if char.isprintable() or char.isspace())
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def extract_email_addresses(text: str) -> List[str]:
        """Extract email addresses from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(email_pattern, text)
    
    @staticmethod
    def extract_phone_numbers(text: str) -> List[str]:
        """Extract phone numbers from text"""
        phone_patterns = [
            r'\b\d{3}-\d{3}-\d{4}\b',  # XXX-XXX-XXXX
            r'\b\(\d{3}\)\s*\d{3}-\d{4}\b',  # (XXX) XXX-XXXX
            r'\b\d{3}\.\d{3}\.\d{4}\b',  # XXX.XXX.XXXX
            r'\b\d{10}\b',  # XXXXXXXXXX
        ]
        
        phone_numbers = []
        for pattern in phone_patterns:
            phone_numbers.extend(re.findall(pattern, text))
        
        return list(set(phone_numbers))
    
    @staticmethod
    def extract_dates(text: str) -> List[str]:
        """Extract dates from text"""
        date_patterns = [
            r'\b\d{1,2}/\d{1,2}/\d{4}\b',  # MM/DD/YYYY
            r'\b\d{1,2}-\d{1,2}-\d{4}\b',  # MM-DD-YYYY
            r'\b\d{4}-\d{1,2}-\d{1,2}\b',  # YYYY-MM-DD
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b',  # Month DD, YYYY
        ]
        
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        
        return list(set(dates))
    
    @staticmethod
    def extract_currency_amounts(text: str) -> List[str]:
        """Extract currency amounts from text"""
        currency_patterns = [
            r'\$[\d,]+\.?\d*',  # $X,XXX.XX
            r'USD\s*[\d,]+\.?\d*',  # USD X,XXX.XX
            r'[\d,]+\.?\d*\s*(?:dollars?|USD)',  # X,XXX.XX dollars
        ]
        
        amounts = []
        for pattern in currency_patterns:
            amounts.extend(re.findall(pattern, text, re.IGNORECASE))
        
        return list(set(amounts))
    
    @staticmethod
    def split_into_sentences(text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting (can be improved with NLTK)
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text"""
        return len(text.split())
    
    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to maximum length"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix

class ValidationUtils:
    """Utility functions for validation"""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email address"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """Validate phone number"""
        # Remove all non-digit characters
        digits = re.sub(r'\D', '', phone)
        # Check if it's 10 or 11 digits (US format)
        return len(digits) in [10, 11]
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Validate URL"""
        pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
        return bool(re.match(pattern, url))
    
    @staticmethod
    def validate_file_upload(file, allowed_extensions: set, max_size_mb: int = 16) -> Dict[str, Any]:
        """Validate uploaded file"""
        result = {
            'valid': True,
            'errors': []
        }
        
        if not file or not file.filename:
            result['valid'] = False
            result['errors'].append('No file provided')
            return result
        
        # Check file extension
        ext = FileUtils.get_file_extension(file.filename)
        if ext not in allowed_extensions:
            result['valid'] = False
            result['errors'].append(f'Invalid file type. Allowed: {", ".join(allowed_extensions)}')
        
        # Check file size (approximate)
        if hasattr(file, 'content_length') and file.content_length:
            size_mb = file.content_length / (1024 * 1024)
            if size_mb > max_size_mb:
                result['valid'] = False
                result['errors'].append(f'File too large. Maximum size: {max_size_mb}MB')
        
        return result

class DataUtils:
    """Utility functions for data processing"""
    
    @staticmethod
    def safe_json_loads(json_string: str, default: Any = None) -> Any:
        """Safely load JSON string"""
        try:
            return json.loads(json_string)
        except (json.JSONDecodeError, TypeError):
            return default
    
    @staticmethod
    def safe_json_dumps(data: Any, default: str = "{}") -> str:
        """Safely dump data to JSON string"""
        try:
            return json.dumps(data, ensure_ascii=False, indent=2)
        except (TypeError, ValueError):
            return default
    
    @staticmethod
    def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        """Flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(DataUtils.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    @staticmethod
    def merge_dicts(*dicts: Dict) -> Dict:
        """Merge multiple dictionaries"""
        result = {}
        for d in dicts:
            if isinstance(d, dict):
                result.update(d)
        return result
    
    @staticmethod
    def filter_dict_by_keys(d: Dict, keys: List[str]) -> Dict:
        """Filter dictionary by keeping only specified keys"""
        return {k: v for k, v in d.items() if k in keys}
    
    @staticmethod
    def remove_empty_values(d: Dict) -> Dict:
        """Remove empty values from dictionary"""
        return {k: v for k, v in d.items() if v not in [None, '', [], {}]}

class LoggingUtils:
    """Utility functions for logging"""
    
    @staticmethod
    def setup_logging(log_file: str = 'app.log', level: int = logging.INFO) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger('tender_automation')
        logger.setLevel(level)
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    @staticmethod
    def log_function_call(func_name: str, args: tuple = (), kwargs: Dict = None):
        """Log function call with parameters"""
        logger = logging.getLogger('tender_automation')
        kwargs_str = f", kwargs={kwargs}" if kwargs else ""
        logger.debug(f"Calling {func_name}(args={args}{kwargs_str})")

class SecurityUtils:
    """Utility functions for security"""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for security"""
        # Remove path traversal attempts
        filename = os.path.basename(filename)
        # Remove dangerous characters
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext
        return filename
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate secure session ID"""
        import secrets
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return hashlib.sha256(password.encode()).hexdigest() == hashed

class TemplateUtils:
    """Utility functions for template processing"""
    
    @staticmethod
    def find_placeholders(text: str) -> List[str]:
        """Find all placeholders in text"""
        patterns = [
            r'\{\{([^}]+)\}\}',  # {{placeholder}}
            r'\[([^\]]+)\]',     # [placeholder]
            r'<([^>]+)>',        # <placeholder>
            r'%([^%]+)%',        # %placeholder%
        ]
        
        placeholders = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            placeholders.extend(matches)
        
        return list(set(placeholders))
    
    @staticmethod
    def replace_placeholders(text: str, replacements: Dict[str, str]) -> str:
        """Replace placeholders in text with values"""
        for placeholder, value in replacements.items():
            patterns = [
                f'{{{{{placeholder}}}}}',  # {{placeholder}}
                f'[{placeholder}]',        # [placeholder]
                f'<{placeholder}>',        # <placeholder>
                f'%{placeholder}%',        # %placeholder%
            ]
            
            for pattern in patterns:
                text = text.replace(pattern, str(value))
        
        return text
    
    @staticmethod
    def extract_template_variables(template_path: str) -> List[str]:
        """Extract all template variables from file"""
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return TemplateUtils.find_placeholders(content)
        except Exception as e:
            logging.error(f"Error extracting template variables: {e}")
            return []

class PerformanceUtils:
    """Utility functions for performance monitoring"""
    
    @staticmethod
    def time_function(func):
        """Decorator to time function execution"""
        import time
        from functools import wraps
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            logger = logging.getLogger('tender_automation')
            logger.debug(f"{func.__name__} executed in {end_time - start_time:.2f} seconds")
            
            return result
        return wrapper
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get current memory usage"""
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
            'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
            'percent': process.memory_percent()
        }

class ConfigUtils:
    """Utility functions for configuration management"""
    
    @staticmethod
    def load_config_from_file(config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading config from {config_path}: {e}")
            return {}
    
    @staticmethod
    def save_config_to_file(config: Dict[str, Any], config_path: str) -> bool:
        """Save configuration to JSON file"""
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Error saving config to {config_path}: {e}")
            return False
    
    @staticmethod
    def get_env_var(var_name: str, default: Any = None, var_type: type = str) -> Any:
        """Get environment variable with type conversion"""
        value = os.environ.get(var_name, default)
        
        if value is None:
            return default
        
        try:
            if var_type == bool:
                return value.lower() in ['true', '1', 'yes', 'on']
            elif var_type == int:
                return int(value)
            elif var_type == float:
                return float(value)
            else:
                return var_type(value)
        except (ValueError, TypeError):
            return default

# Export commonly used utilities
__all__ = [
    'FileUtils',
    'TextUtils', 
    'ValidationUtils',
    'DataUtils',
    'LoggingUtils',
    'SecurityUtils',
    'TemplateUtils',
    'PerformanceUtils',
    'ConfigUtils'
]
