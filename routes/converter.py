from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from repositories.layout_repository import LayoutRepository
from repositories.history_repository import HistoryRepository
from services.converter_service import ConverterService
from services.ai_service import AIService, AIIntegrationDisabledError
from utilities.validation import validate_schema
from models.schemas import ConvertTextSchema
from configuration.config import Config, logger

converter_bp = Blueprint("converter", __name__)
layout_repo = LayoutRepository()
history_repo = HistoryRepository()

# Hardcoded fail-safe default layout
DEFAULT_EN_AR_MAPPING = {
    "q": "ض", "w": "ص", "e": "ث", "r": "ق", "t": "ف", "y": "غ", "u": "ع", "i": "ه", "o": "خ", "p": "ح", "[": "ج", "]": "د",
    "a": "ش", "s": "س", "d": "ي", "f": " ب", "g": "ل", "h": "ا", "j": "ت", "k": "ن", "l": "م", ";": "ك", "'": "ط",
    "z": "ئ", "x": "ء", "c": "ؤ", "v": "ر", "b": "لا", "n": "ى", "m": "ة", ",": "و", ".": "ز", "/": "ظ",
    "Q": "َ", "W": "ً", "E": "ُ", "R": "ٌ", "T": "لإ", "Y": "إ", "U": "`", "I": "ـ", "O": "x", "P": "؛", "{": "ج", "}": "د",
    "A": "ِ", "S": "ٍ", "D": "[", "F": "]", "G": "لأ", "H": "أ", "J": "ـ", "K": "،", "L": "/", ":": "ك", "\"": "ط",
    "Z": "~", "X": "ْ", "C": "}", "V": "{", "B": "لآ", "N": "آ", "M": "’", "<": ",", ">": ".", "?": "؟"
}

DEFAULT_AR_EN_MAPPING = {v: k for k, v in DEFAULT_EN_AR_MAPPING.items()}

@converter_bp.route("/config", methods=["GET"])
def get_converter_config():
    """
    Returns AI config metadata so the front-end SPA can adapt layout options.
    """
    return jsonify({
        "ai_enabled": Config.AI_ENABLED,
        "available_models": AIService.get_available_models(),
        "google_client_id": Config.GOOGLE_CLIENT_ID,
        "google_redirect_uri": Config.GOOGLE_REDIRECT_URI
    })

@converter_bp.route("/convert", methods=["POST"])
@jwt_required(optional=True)
@validate_schema(ConvertTextSchema)
def convert():
    user_id = get_jwt_identity()
    data: ConvertTextSchema = g.validated_data

    # 1. Resolve Layout Mapping
    if data.layout_id == "default_en_ar":
        layout_name = "English to Arabic (PC Default)"
        mapping = DEFAULT_EN_AR_MAPPING
    elif data.layout_id == "default_ar_en":
        layout_name = "Arabic to English (PC Default)"
        mapping = DEFAULT_AR_EN_MAPPING
    else:
        # Load from Database (checks private owned or public marketplace layouts)
        layout = None
        if user_id:
            layout = layout_repo.get_user_layout(data.layout_id, user_id)
            
        if not layout:
            # Fallback to check published marketplace collections
            layout = layout_repo.published_collection.find_one({"layout_id": data.layout_id})
            if layout:
                layout_name = layout["name"]
                mapping = layout["mapping"]
            else:
                return jsonify({"error": "Selected keyboard layout not found or access denied."}), 404
        else:
            layout_name = layout["name"]
            mapping = layout["mapping"]

    # 2. Execute Layout Conversion
    converted_text = ConverterService.convert_text(data.text, mapping)

    # 3. Handle Optional AI Enhancements (Modes 2, 3, 4)
    ai_enhanced_text = None
    ai_error = None
    
    if data.mode > 1:
        if not Config.AI_ENABLED:
            ai_error = "AI correction skipped because AI integration is disabled on this server instance."
        else:
            # Build AI properties
            preferred_model = Config.DEFAULT_AI_MODEL
            temp = 0.3
            prompt_prefix = ""
            
            if data.ai_settings:
                preferred_model = data.ai_settings.preferred_model
                if preferred_model in ("meta-llama/llama-3-8b-instruct:free", "google/gemma-2-9b-it:free", "nvidia/nemotron-3-ultra-550b-a55b:free"):
                    preferred_model = "meta-llama/llama-3.3-70b-instruct:free"
                temp = data.ai_settings.temperature
                prompt_prefix = data.ai_settings.prompt_prefix
                
            try:
                ai_enhanced_text = AIService.enhance_text(
                    text=converted_text,
                    mode=data.mode,
                    model=preferred_model,
                    temperature=temp,
                    custom_prompt_prefix=prompt_prefix
                )
            except AIIntegrationDisabledError as e:
                ai_error = str(e)
            except Exception as e:
                logger.error(f"AI correction execution failed: {e}")
                ai_error = f"AI correction error: {str(e)}"

    # 4. Save to Conversion History if authenticated
    if user_id:
        try:
            history_repo.log_conversion(
                user_id=user_id,
                original_text=data.text,
                converted_text=converted_text,
                layout_id=data.layout_id,
                layout_name=layout_name,
                mode=data.mode,
                ai_enhanced_text=ai_enhanced_text
            )
        except Exception as e:
            logger.error(f"Failed to log conversion history: {e}")

    # 5. Formulate response payload
    return jsonify({
        "original_text": data.text,
        "converted_text": converted_text,
        "ai_enhanced_text": ai_enhanced_text,
        "ai_error": ai_error,
        "layout_id": data.layout_id,
        "layout_name": layout_name,
        "mode": data.mode,
        "direction": "rtl" if ConverterService.detect_rtl(converted_text) else "ltr"
    })
