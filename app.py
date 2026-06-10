import os
from flask import Flask, jsonify, render_template, send_from_directory
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import datetime

# Import configurations and services
from configuration.config import Config, logger
from configuration.db import get_db
from services.mail_service import MailService
from services.auth_service import AuthService
from middleware.security_headers import init_security_headers

# Import routes
from routes.auth import auth_bp
from routes.layouts import layouts_bp
from routes.converter import converter_bp
from routes.marketplace import marketplace_bp
from routes.history import history_bp
from routes.docs import docs_bp

def create_app() -> Flask:
    app = Flask(
        __name__, 
        template_folder="templates", 
        static_folder="static", 
        static_url_path="/static"
    )

    # Apply configuration settings
    app.config["SECRET_KEY"] = Config.get_flask_secret()
    
    # Configure JWT
    app.config["JWT_SECRET_KEY"] = Config.get_jwt_secret()
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    app.config["JWT_COOKIE_SECURE"] = Config.FLASK_ENV == "production"
    app.config["JWT_COOKIE_CSRF_PROTECT"] = True
    app.config["JWT_ACCESS_CSRF_HEADER_NAME"] = "X-CSRF-Token"
    app.config["JWT_REFRESH_CSRF_HEADER_NAME"] = "X-CSRF-Token"
    app.config["JWT_COOKIE_SAMESITE"] = "Lax"
    
    # Cookie directories paths
    app.config["JWT_ACCESS_COOKIE_PATH"] = "/api/"
    app.config["JWT_REFRESH_COOKIE_PATH"] = "/api/auth/refresh"
    
    # Expiration lifespans
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = datetime.timedelta(minutes=Config.JWT_ACCESS_TOKEN_EXPIRES_MINUTES)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = datetime.timedelta(days=Config.JWT_REFRESH_TOKEN_EXPIRES_DAYS)

    # Initialize Services
    MailService.init_app(app)
    init_security_headers(app)
    
    # Force database connection check
    try:
        get_db()
    except Exception as e:
        logger.error(f"Could not connect to MongoDB database: {e}")

    # Set up JWT Manager and blocklist callbacks
    jwt = JWTManager(app)
    auth_service = AuthService()

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload) -> bool:
        # We check refresh tokens (stored in sessions) for active states
        # Access tokens have short lifespans (15m) and are not individually revoked in DB for performance
        token_type = jwt_payload.get("type")
        if token_type == "refresh":
            jti = jwt_payload.get("jti")
            return auth_service.is_session_revoked(jti)
        return False

    @jwt.revoked_token_loader
    @jwt.expired_token_loader
    def expired_revoked_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Your session has expired. Please log in again."}), 401

    @jwt.unauthorized_loader
    def unauthorized_callback(err_str):
        return jsonify({"error": "Authentication credentials are required.", "details": err_str}), 401

    # Configure CORS - Restrict in production
    if Config.FLASK_ENV == "production":
        CORS(app, supports_credentials=True, origins=[]) # Nginx handles proxy
    else:
        CORS(app, supports_credentials=True, origins=[
            "http://127.0.0.1:5454", "http://localhost:5454",
            "http://127.0.0.1:5173", "http://localhost:5173"
        ])

    # Configure Rate Limiter (Flask-Limiter)
    # Uses Memory storage by default, can be extended to use Redis or Mongo
    default_limits = ["50000 per day", "2000 per hour"] if Config.FLASK_ENV == "development" else ["200 per day", "50 per hour"]
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=default_limits,
        storage_uri="memory://"
    )

    # Apply specific rate limits to sensitive routes
    # (Registration and logins get restricted to prevent brute force attacks)
    limiter.limit("5 per minute")(auth_bp)

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(layouts_bp, url_prefix="/api/layouts")
    app.register_blueprint(converter_bp, url_prefix="/api/converter")
    app.register_blueprint(marketplace_bp, url_prefix="/api/marketplace")
    app.register_blueprint(history_bp, url_prefix="/api/history")
    app.register_blueprint(docs_bp, url_prefix="/api/docs")

    # Serve Vanilla SPA Web Application routes
    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def index(path):
        # Serve the single-page application index
        # Any URL route not matching /api is captured and routed client-side
        if path.startswith("api/") or path.startswith("static/"):
            return jsonify({"error": "Not found"}), 404
        return render_template("index.html")

    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def handle_internal_error(e):
        logger.error(f"Unhandled Server Error: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

    return app

app = create_app()

if __name__ == "__main__":
    # In testing, listen strictly on local loopback as per guidelines
    host = "127.0.0.1" if Config.FLASK_ENV == "development" else "0.0.0.0"
    app.run(host=host, port=5454)
