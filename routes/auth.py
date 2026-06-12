from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies,
    jwt_required, get_jwt_identity, get_jwt
)
from repositories.user_repository import UserRepository
from repositories.history_repository import HistoryRepository
from services.auth_service import AuthService
from services.mail_service import MailService
from utilities.validation import validate_schema
from models.schemas import (
    UserRegisterSchema, UserLoginSchema, 
    PasswordResetRequestSchema, PasswordResetConfirmSchema, 
    ProfileUpdateSchema, AIConverterSettingsSchema
)
from configuration.config import Config, logger
import secrets
import datetime

auth_bp = Blueprint("auth", __name__)
user_repo = UserRepository()
history_repo = HistoryRepository()
auth_service = AuthService()

@auth_bp.route("/register", methods=["POST"])
@validate_schema(UserRegisterSchema)
def register():
    data: UserRegisterSchema = g.validated_data
    existing_user = user_repo.get_by_email(data.email)
    if existing_user:
        return jsonify({"error": "A user with this email address already exists"}), 400

    hashed_pw = AuthService.hash_password(data.password)
    user = user_repo.create_user(email=data.email, password_hash=hashed_pw)
    
    # Generate verification token
    verification_token = secrets.token_urlsafe(32)
    user_repo.set_verification_token(user["id"], verification_token)

    # Dispatch email
    origin_url = request.headers.get("Origin") or f"http://{request.host}"
    mail_success = MailService.send_verification_email(user["email"], verification_token, origin_url)
    
    msg = "User registered successfully. Please check your email to verify your account."
    if not mail_success and Config.DEBUG:
        msg = "User registered. Verification email simulated (please check backend logs for link)."
        
    return jsonify({
        "message": msg,
        "user_id": user["id"]
    }), 201

@auth_bp.route("/login", methods=["POST"])
@validate_schema(UserLoginSchema)
def login():
    data: UserLoginSchema = g.validated_data
    user = user_repo.get_by_email(data.email)
    
    if not user or not user["password_hash"] or not AuthService.verify_password(data.password, user["password_hash"]):
        return jsonify({"error": "Invalid email address or password"}), 401

    # Generate tokens
    access_token = create_access_token(identity=user["id"])
    
    # Optional remember me: adjust refresh token lifetime
    if data.remember_me:
        refresh_expires = datetime.timedelta(days=30)
    else:
        refresh_expires = datetime.timedelta(days=Config.JWT_REFRESH_TOKEN_EXPIRES_DAYS)
        
    refresh_token = create_refresh_token(identity=user["id"], expires_delta=refresh_expires)

    # Track session JTI for revocation
    from flask_jwt_extended import decode_token
    decoded_refresh = decode_token(refresh_token)
    refresh_jti = decoded_refresh["jti"]
    refresh_exp = decoded_refresh["exp"] - decoded_refresh["iat"]
    auth_service.register_session(user["id"], refresh_jti, refresh_exp)

    # Prepare response
    response = jsonify({
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "is_verified": user["is_verified"],
            "ai_settings": user.get("ai_settings", {}),
            "profile_picture": user.get("profile_picture")
        }
    })
    
    # Store tokens in secure HttpOnly cookies
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    return response

@auth_bp.route("/logout", methods=["POST"])
@jwt_required(refresh=True, optional=True)
def logout():
    response = jsonify({"message": "Logout successful"})
    unset_jwt_cookies(response)
    
    # Revoke session token
    try:
        jwt_data = get_jwt()
        if jwt_data and "jti" in jwt_data:
            auth_service.revoke_session(jwt_data["jti"])
    except Exception:
        pass
        
    return response

@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    # Check if session is revoked
    jwt_data = get_jwt()
    if jwt_data and auth_service.is_session_revoked(jwt_data["jti"]):
        response = jsonify({"error": "Session has expired or been revoked"})
        unset_jwt_cookies(response)
        return response, 401

    # Generate new access token
    access_token = create_access_token(identity=user_id)
    response = jsonify({"message": "Token refreshed successfully"})
    set_access_cookies(response, access_token)
    return response

@auth_bp.route("/verify-email", methods=["GET"])
def verify_email():
    token = request.args.get("token")
    if not token:
        return jsonify({"error": "Missing verification token"}), 400
        
    user = user_repo.verify_email(token)
    if not user:
        return jsonify({"error": "Invalid or expired verification token"}), 400
        
    return jsonify({"message": "Email verified successfully!", "email": user["email"]})

@auth_bp.route("/resend-verification", methods=["POST"])
@jwt_required()
def resend_verification():
    user_id = get_jwt_identity()
    user = user_repo.get_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    if user.get("is_verified", False):
        return jsonify({"message": "Account is already verified"}), 200
        
    # Generate verification token
    verification_token = secrets.token_urlsafe(32)
    user_repo.set_verification_token(user["id"], verification_token)

    # Dispatch email
    origin_url = request.headers.get("Origin") or f"http://{request.host}"
    mail_success = MailService.send_verification_email(user["email"], verification_token, origin_url)
    
    msg = "Verification email resent successfully. Please check your email inbox."
    if not mail_success and Config.DEBUG:
        msg = "Verification email simulated (please check backend logs for link)."
        
    return jsonify({"message": msg}), 200

@auth_bp.route("/reset-password/request", methods=["POST"])
@validate_schema(PasswordResetRequestSchema)
def reset_password_request():
    data: PasswordResetRequestSchema = g.validated_data
    user = user_repo.get_by_email(data.email)
    
    # To prevent account enumeration, return a generic success message even if the email doesn't exist
    if user:
        reset_token = secrets.token_urlsafe(32)
        user_repo.set_password_reset_token(user["id"], reset_token)
        origin_url = request.headers.get("Origin") or f"http://{request.host}"
        MailService.send_password_reset_email(user["email"], reset_token, origin_url)
        
    return jsonify({"message": "If this email is registered, you will receive a password reset link shortly."})

@auth_bp.route("/reset-password/confirm", methods=["POST"])
@validate_schema(PasswordResetConfirmSchema)
def reset_password_confirm():
    data: PasswordResetConfirmSchema = g.validated_data
    hashed_pw = AuthService.hash_password(data.new_password)
    user = user_repo.reset_password(data.token, hashed_pw)
    
    if not user:
        return jsonify({"error": "Invalid or expired reset token"}), 400
        
    # Invalidate all user sessions upon password reset for security
    auth_service.revoke_all_user_sessions(user["id"])
    return jsonify({"message": "Password reset completed successfully. Please login with your new password."})

@auth_bp.route("/google", methods=["POST"])
def google_oauth():
    body = request.get_json() or {}
    code = body.get("code")
    if not code:
        return jsonify({"error": "Missing authorization code"}), 400
        
    profile = auth_service.verify_google_code(code)
    if not profile:
        return jsonify({"error": "Failed to authenticate with Google OAuth"}), 400
        
    email = profile.get("email")
    google_id = profile.get("sub")
    name = profile.get("name")
    
    if not email or not google_id:
        return jsonify({"error": "Google profile missing mandatory fields"}), 400
        
    # Find or create user
    user = user_repo.get_by_google_id(google_id)
    if not user:
        # Check if email exists already but google_id not set
        user = user_repo.get_by_email(email)
        if user:
            # Link accounts
            user_repo.update(user["id"], {"google_id": google_id, "is_verified": True})
            user = user_repo.get_by_id(user["id"])
        else:
            user = user_repo.create_user(email=email, google_id=google_id, name=name)
            
    # Authenticate user session
    access_token = create_access_token(identity=user["id"])
    refresh_token = create_refresh_token(identity=user["id"])
    
    from flask_jwt_extended import decode_token
    decoded_refresh = decode_token(refresh_token)
    refresh_jti = decoded_refresh["jti"]
    refresh_exp = decoded_refresh["exp"] - decoded_refresh["iat"]
    auth_service.register_session(user["id"], refresh_jti, refresh_exp)

    response = jsonify({
        "message": "Login successful via Google",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "is_verified": user["is_verified"],
            "ai_settings": user.get("ai_settings", {}),
            "profile_picture": user.get("profile_picture")
        }
    })
    
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    return response

@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = user_repo.get_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    return jsonify({
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "is_verified": user["is_verified"],
            "ai_settings": user.get("ai_settings", {}),
            "profile_picture": user.get("profile_picture")
        }
    })

@auth_bp.route("/profile", methods=["PUT"])
@jwt_required()
@validate_schema(ProfileUpdateSchema)
def update_profile():
    user_id = get_jwt_identity()
    data: ProfileUpdateSchema = g.validated_data
    
    user = user_repo.get_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    update_data = {}
    if data.name:
        update_data["name"] = data.name
        
    if data.new_password:
        if not data.current_password or not user["password_hash"] or not AuthService.verify_password(data.current_password, user["password_hash"]):
            return jsonify({"error": "Invalid current password"}), 400
        update_data["password_hash"] = AuthService.hash_password(data.new_password)
        
    if not update_data:
        return jsonify({"message": "No profile updates requested"})
        
    success = user_repo.update_profile(user_id, **update_data)
    if not success:
        return jsonify({"error": "Failed to update profile settings"}), 500
        
    # Invalidate all user sessions upon password change for security
    if "password_hash" in update_data:
        auth_service.revoke_all_user_sessions(user_id)
        
    return jsonify({"message": "Profile updated successfully"})

@auth_bp.route("/ai-settings", methods=["PUT"])
@jwt_required()
@validate_schema(AIConverterSettingsSchema)
def update_ai_settings():
    user_id = get_jwt_identity()
    data: AIConverterSettingsSchema = g.validated_data
    
    success = user_repo.update_ai_settings(user_id, data.model_dump())
    if not success:
        return jsonify({"error": "Failed to save AI preferences"}), 500
        
    return jsonify({"message": "AI settings saved successfully"})

@auth_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_user_stats():
    user_id = get_jwt_identity()
    stats = history_repo.get_conversion_statistics(user_id)
    layouts_count = user_repo.db["layouts"].count_documents({"user_id": user_id})
    stats["layouts_count"] = layouts_count
    return jsonify(stats)

@auth_bp.route("/profile/avatar", methods=["POST"])
@jwt_required()
def upload_avatar():
    import os
    import uuid
    
    user_id = get_jwt_identity()
    user = user_repo.get_by_id(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if "avatar" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["avatar"]
    if file.filename == "":
        return jsonify({"error": "No file selected for uploading"}), 400

    # Validate file size (max 2MB)
    file.seek(0, os.SEEK_END)
    file_length = file.tell()
    if file_length > 2 * 1024 * 1024:
        return jsonify({"error": "File size exceeds the 2MB limit"}), 400

    # Reset file pointer to read magic bytes
    file.seek(0)
    header = file.read(12)
    file.seek(0)

    # Magic byte signatures definition
    ALLOWED_MAGIC_BYTES = {
        b"\xff\xd8\xff": "image/jpeg",
        b"\x89PNG\r\n\x1a\n": "image/png",
        b"GIF87a": "image/gif",
        b"GIF89a": "image/gif",
        b"RIFF": "image/webp"
    }

    # Match magic bytes
    matched_type = None
    for prefix, mime_type in ALLOWED_MAGIC_BYTES.items():
        if header.startswith(prefix):
            if mime_type == "image/webp":
                if len(header) >= 12 and header[8:12] == b"WEBP":
                    matched_type = "image/webp"
            else:
                matched_type = mime_type
            break

    if not matched_type:
        return jsonify({"error": "Invalid file type. Only JPEG, PNG, GIF, and WEBP images are allowed."}), 400

    # Determine extension
    ext = ".jpg"
    if matched_type == "image/png":
        ext = ".png"
    elif matched_type == "image/gif":
        ext = ".gif"
    elif matched_type == "image/webp":
        ext = ".webp"

    # Define upload path
    upload_dir = os.path.join(os.getcwd(), "static", "uploads", "avatars")
    os.makedirs(upload_dir, exist_ok=True)

    # Delete old avatar file if it exists
    old_avatar = user.get("profile_picture")
    if old_avatar and old_avatar.startswith("/static/uploads/avatars/"):
        old_filename = os.path.basename(old_avatar)
        old_file_path = os.path.join(upload_dir, old_filename)
        if os.path.exists(old_file_path):
            try:
                os.remove(old_file_path)
            except Exception:
                pass

    # Save new avatar file
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)

    # Update database
    new_avatar_url = f"/static/uploads/avatars/{filename}"
    user_repo.update(user_id, {"profile_picture": new_avatar_url})

    return jsonify({
        "message": "Profile picture updated successfully",
        "profile_picture": new_avatar_url
    })
