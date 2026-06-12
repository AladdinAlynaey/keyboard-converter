from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from repositories.layout_repository import LayoutRepository
from repositories.user_repository import UserRepository
from utilities.validation import validate_schema
from models.schemas import LayoutCreateSchema, LayoutUpdateSchema
from configuration.config import logger
import json
import datetime

layouts_bp = Blueprint("layouts", __name__)
layout_repo = LayoutRepository()
user_repo = UserRepository()

@layouts_bp.route("", methods=["GET"])
@jwt_required()
def get_layouts():
    user_id = get_jwt_identity()
    user_layouts = layout_repo.get_user_layouts(user_id)
    return jsonify(user_layouts)

@layouts_bp.route("", methods=["POST"])
@jwt_required()
@validate_schema(LayoutCreateSchema)
def create_layout():
    user_id = get_jwt_identity()
    data: LayoutCreateSchema = g.validated_data
    
    # Check duplicate name for the same user
    existing = layout_repo.find_one({"user_id": user_id, "name": data.name})
    if existing:
        return jsonify({"error": f"A layout named '{data.name}' already exists."}), 400
        
    layout_data = data.model_dump()
    user = user_repo.get_by_id(user_id)
    layout_data["creator_name"] = user.get("name", "Anonymous")
    
    layout_id = layout_repo.create_layout(user_id, layout_data)
    return jsonify({"message": "Layout created successfully", "id": layout_id}), 201

@layouts_bp.route("/<id>", methods=["GET"])
@jwt_required()
def get_layout(id):
    user_id = get_jwt_identity()
    layout = layout_repo.get_user_layout(id, user_id)
    if not layout:
        return jsonify({"error": "Layout not found or access denied"}), 404
    return jsonify(layout)

@layouts_bp.route("/<id>", methods=["PUT"])
@jwt_required()
@validate_schema(LayoutUpdateSchema)
def update_layout(id):
    user_id = get_jwt_identity()
    data: LayoutUpdateSchema = g.validated_data
    
    layout = layout_repo.get_user_layout(id, user_id)
    if not layout:
        return jsonify({"error": "Layout not found or access denied"}), 404
        
    # Prevent duplicate names
    if data.name and data.name != layout["name"]:
        existing = layout_repo.find_one({"user_id": user_id, "name": data.name})
        if existing:
            return jsonify({"error": f"A layout named '{data.name}' already exists."}), 400
            
    success = layout_repo.update_layout(id, user_id, data.model_dump(exclude_unset=True))
    if not success:
        return jsonify({"error": "Failed to update layout details"}), 500
        
    return jsonify({"message": "Layout updated successfully"})

@layouts_bp.route("/<id>", methods=["DELETE"])
@jwt_required()
def delete_layout(id):
    user_id = get_jwt_identity()
    layout = layout_repo.get_user_layout(id, user_id)
    if not layout:
        return jsonify({"error": "Layout not found or access denied"}), 404
        
    success = layout_repo.delete_layout(id, user_id)
    if not success:
        return jsonify({"error": "Failed to delete layout"}), 500
        
    return jsonify({"message": "Layout deleted successfully"})

@layouts_bp.route("/<id>/duplicate", methods=["POST"])
@jwt_required()
def duplicate_layout(id):
    user_id = get_jwt_identity()
    body = request.get_json(silent=True) or {}
    new_name = body.get("name")
    
    if not new_name or not new_name.strip():
        return jsonify({"error": "Duplicate name is required"}), 400
        
    # Check if target name exists
    existing = layout_repo.find_one({"user_id": user_id, "name": new_name})
    if existing:
        return jsonify({"error": f"A layout named '{new_name}' already exists."}), 400
        
    new_id = layout_repo.duplicate_layout(id, user_id, new_name.strip())
    if not new_id:
        return jsonify({"error": "Failed to duplicate layout"}), 500
        
    return jsonify({"message": "Layout duplicated successfully", "id": new_id}), 201

@layouts_bp.route("/<id>/publish", methods=["POST"])
@jwt_required()
def publish_layout(id):
    user_id = get_jwt_identity()
    user = user_repo.get_by_id(user_id)
    
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    if not user.get("is_verified", False):
        return jsonify({"error": "You must verify your email address before publishing layouts to the marketplace"}), 403

    body = request.get_json(silent=True) or {}
    tags = body.get("tags", [])
    if not isinstance(tags, list):
        return jsonify({"error": "Tags must be a list of strings"}), 400

    # Sanitize tags
    tags = [str(t).strip()[:20] for t in tags if t][:5]

    # Retrieve user's layout to check its mapping configuration
    layout = layout_repo.get_user_layout(id, user_id)
    if not layout:
        return jsonify({"error": "Layout not found or access denied"}), 404

    current_mapping = layout.get("mapping")
    if not current_mapping:
        return jsonify({"error": "Layout has no mapping configuration"}), 400

    # Compare against system default layouts
    from routes.converter import DEFAULT_EN_AR_MAPPING, DEFAULT_AR_EN_MAPPING
    sorted_current = dict(sorted(current_mapping.items()))
    sorted_default_en_ar = dict(sorted(DEFAULT_EN_AR_MAPPING.items()))
    sorted_default_ar_en = dict(sorted(DEFAULT_AR_EN_MAPPING.items()))

    if sorted_current == sorted_default_en_ar or sorted_current == sorted_default_ar_en:
        return jsonify({"error": "Failed to publish: This layout configuration matches a system default layout."}), 400

    # Compare against all other published layouts in the database (excluding itself) using Python order-independent matching
    is_duplicate = False
    for pub in layout_repo.published_collection.find():
        if pub.get("layout_id") == id:
            continue
        pub_mapping = pub.get("mapping")
        if pub_mapping and dict(sorted(pub_mapping.items())) == sorted_current:
            is_duplicate = True
            break

    if is_duplicate:
        return jsonify({"error": "Failed to publish: This layout configuration is identical to another already published layout."}), 400

    success = layout_repo.publish_layout(id, user_id, tags)
    if not success:
        return jsonify({"error": "Layout not found or access denied"}), 404
        
    return jsonify({"message": "Layout published to marketplace successfully"})

@layouts_bp.route("/<id>/unpublish", methods=["POST"])
@jwt_required()
def unpublish_layout(id):
    user_id = get_jwt_identity()
    success = layout_repo.unpublish_layout(id, user_id)
    if not success:
        return jsonify({"error": "Layout not found, access denied, or not currently published"}), 404
        
    return jsonify({"message": "Layout removed from marketplace successfully"})

@layouts_bp.route("/<id>/export", methods=["GET"])
@jwt_required()
def export_layout(id):
    user_id = get_jwt_identity()
    user = user_repo.get_by_id(user_id)
    if not user or not user.get("is_verified", False):
        return jsonify({"error": "You must verify your email address before exporting layouts"}), 403

    layout = layout_repo.get_user_layout(id, user_id)
    if not layout:
        # Check if they are exporting a public layout they don't own
        layout = layout_repo.published_collection.find_one({"layout_id": id})
        if layout:
            layout["id"] = str(layout["_id"])
            del layout["_id"]
        else:
            return jsonify({"error": "Layout not found or access denied"}), 404
            
    # Structure export package
    export_data = {
        "name": layout["name"],
        "description": layout.get("description", ""),
        "language": layout["language"],
        "direction": layout.get("direction", "ltr"),
        "mapping": layout["mapping"]
    }
    
    return jsonify(export_data)

@layouts_bp.route("/import", methods=["POST"])
@jwt_required()
def import_layout():
    user_id = get_jwt_identity()
    body = request.get_json(silent=True) or {}
    layout_json = body.get("layout_json")
    
    if not layout_json:
        return jsonify({"error": "Import payload layout_json is required"}), 400
        
    try:
        if isinstance(layout_json, str):
            parsed = json.loads(layout_json)
        else:
            parsed = layout_json
            
        # Validate schema using schema class instantiation
        validated = LayoutCreateSchema(**parsed)
    except Exception as e:
        return jsonify({"error": f"Import failed: Invalid layout JSON structure. details: {str(e)}"}), 400
        
    # Check duplicate name
    existing = layout_repo.find_one({"user_id": user_id, "name": validated.name})
    name_to_use = validated.name
    if existing:
        name_to_use = f"{validated.name} (Imported)"
        # Check imported suffix duplicate
        suffix_check = layout_repo.find_one({"user_id": user_id, "name": name_to_use})
        if suffix_check:
            name_to_use = f"{validated.name} (Imported {datetime.datetime.utcnow().strftime('%Y%m%d%H%M')})"
            
    layout_data = validated.model_dump()
    layout_data["name"] = name_to_use
    layout_data["is_public"] = False
    user = user_repo.get_by_id(user_id)
    layout_data["creator_name"] = user.get("name", "Anonymous")
    
    layout_id = layout_repo.create_layout(user_id, layout_data)
    return jsonify({"message": "Layout imported successfully", "id": layout_id, "name": name_to_use}), 201
