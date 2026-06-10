import os
import secrets
import logging
from dotenv import load_dotenv

# Load variables from .env file
load_dotenv()

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
)
logger = logging.getLogger("SmartKeyboardConverter")

class Config:
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = FLASK_ENV == "development"
    TESTING = False

    # Database
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/")
    MONGO_DB = os.getenv("MONGO_DB", "keyboard_converter")

    # SMTP configuration
    SMTP_SERVER = os.getenv("SMTP_SERVER", os.getenv("SMTP_HOST", "localhost"))
    SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "False").lower() in ("true", "1", "yes")
    SMTP_USE_SSL = os.getenv("SMTP_USE_SSL", "False").lower() in ("true", "1", "yes")
    SMTP_SENDER = os.getenv("SMTP_SENDER", os.getenv("SMTP_FROM_EMAIL", "noreply@smartkeyboardconverter.local"))
    SMTP_SENDER_NAME = os.getenv("SMTP_FROM_NAME", "Smart Keyboard Converter AI")

    # Google OAuth configuration
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "")

    # AI Configuration
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    DEFAULT_AI_MODEL = os.getenv("DEFAULT_AI_MODEL", "meta-llama/llama-3-8b-instruct:free")
    
    # Check if AI is explicitly disabled or if the key is missing
    AI_ENABLED = os.getenv("AI_ENABLED", "True").lower() in ("true", "1", "yes")
    if not OPENROUTER_API_KEY:
        AI_ENABLED = False

    # Get Secrets with Multi-tiered Fallback for Local Dev
    @classmethod
    def get_flask_secret(cls):
        secret = os.getenv("FLASK_SECRET_KEY")
        if secret:
            return secret
        
        # Check if local file contains the secret
        secret_file = "flask_secret.txt"
        if os.path.exists(secret_file):
            with open(secret_file, "r") as f:
                return f.read().strip()
                
        if cls.FLASK_ENV == "production":
            raise RuntimeError("FLASK_SECRET_KEY must be set in production environment!")
            
        logger.warning("Generating ephemeral FLASK_SECRET_KEY. Session states will reset on restart!")
        new_secret = secrets.token_hex(32)
        try:
            with open(secret_file, "w") as f:
                f.write(new_secret)
        except Exception as e:
            logger.error(f"Failed to write ephemeral secret file: {e}")
        return new_secret

    @classmethod
    def get_jwt_secret(cls):
        secret = os.getenv("JWT_SECRET_KEY")
        if secret:
            return secret
            
        secret_file = "jwt_secret.txt"
        if os.path.exists(secret_file):
            with open(secret_file, "r") as f:
                return f.read().strip()
                
        if cls.FLASK_ENV == "production":
            raise RuntimeError("JWT_SECRET_KEY must be set in production environment!")
            
        logger.warning("Generating ephemeral JWT_SECRET_KEY. Token signatures will reset on restart!")
        new_secret = secrets.token_hex(32)
        try:
            with open(secret_file, "w") as f:
                f.write(new_secret)
        except Exception as e:
            logger.error(f"Failed to write ephemeral secret file: {e}")
        return new_secret

    # Expiry configurations
    JWT_ACCESS_TOKEN_EXPIRES_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "15"))
    JWT_REFRESH_TOKEN_EXPIRES_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES_DAYS", "7"))
