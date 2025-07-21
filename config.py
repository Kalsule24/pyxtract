import os

class Config:
    # Secret key for session security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'

    # Folder where uploaded files will be saved
    UPLOAD_FOLDER = 'uploads'

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {
        'txt', 'pdf', 'docx', 'pptx', 'xlsx', 'csv', 'json'
    }

    # Max file size: 16 MB
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # in bytes

    # API keys (store securely in environment variables for production)
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or 'your-openai-api-key'
    CLOUD_CONVERT_API_KEY = os.environ.get('CLOUD_CONVERT_API_KEY') or 'your-cloudconvert-api-key'
    APYLAYER_API_KEY = os.environ.get('APYLAYER_API_KEY') or 'your-apilayer-key'
