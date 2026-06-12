from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from repositories.layout_repository import LayoutRepository
from repositories.user_repository import UserRepository
from utilities.validation import validate_schema
from models.schemas import CommentCreateSchema, RatingCreateSchema
from configuration.config import logger

marketplace_bp = Blueprint("marketplace", __name__)
layout_repo = LayoutRepository()
user_repo = UserRepository()

@marketplace_bp.route("", methods=["GET"])
@jwt_required()
def browse_marketplace():
    user_id = get_jwt_identity()
    user = user_repo.get_by_id(user_id)
    if not user or not user.get("is_verified", False):
        return jsonify({"error": "You must verify your email address to browse the marketplace."}), 403

    query = request.args.get("q", "")
    language = request.args.get("language", "")
    sort_by = request.args.get("sort_by", "likes")
    limit = int(request.args.get("limit", 12))
    skip = int(request.args.get("skip", 0))

    layouts = layout_repo.search_marketplace(
        query=query,
        language=language,
        sort_by=sort_by,
        limit=limit,
        skip=skip
    )

    # Attach whether it is a favorite of the user
    for layout in layouts:
        layout["is_favorite"] = layout_repo.is_favorite(user_id, layout["layout_id"])

    return jsonify(layouts)

@marketplace_bp.route("/<layout_id>/favorite", methods=["POST"])
@jwt_required()
def toggle_favorite(layout_id):
    user_id = get_jwt_identity()
    
    # Verify the layout exists in the marketplace or layouts
    exists = layout_repo.published_collection.find_one({"layout_id": layout_id}) or layout_repo.get_by_id(layout_id)
    if not exists:
        return jsonify({"error": "Target layout not found."}), 404
        
    result = layout_repo.toggle_favorite(user_id, layout_id)
    return jsonify(result)

@marketplace_bp.route("/<layout_id>/download", methods=["POST"])
def record_download(layout_id):
    # Verify the layout exists in the marketplace
    exists = layout_repo.published_collection.find_one({"layout_id": layout_id})
    if not exists:
        return jsonify({"error": "Target layout not found in marketplace."}), 404
        
    layout_repo.increment_downloads(layout_id)
    return jsonify({"message": "Download count incremented"})

@marketplace_bp.route("/<layout_id>/comments", methods=["GET"])
def get_comments(layout_id):
    comments = layout_repo.get_layout_comments(layout_id)
    return jsonify(comments)

@marketplace_bp.route("/<layout_id>/comments", methods=["POST"])
@jwt_required()
@validate_schema(CommentCreateSchema)
def post_comment(layout_id):
    user_id = get_jwt_identity()
    data: CommentCreateSchema = g.validated_data

    # Check if user is verified
    user = user_repo.get_by_id(user_id)
    if not user.get("is_verified", False):
        return jsonify({"error": "You must verify your email address to write comments."}), 403

    # Verify layout exists in marketplace
    exists = layout_repo.published_collection.find_one({"layout_id": layout_id})
    if not exists:
        return jsonify({"error": "Target layout not found."}), 404

    comment = layout_repo.add_comment(
        layout_id=layout_id,
        user_id=user_id,
        creator_name=user.get("name", "Anonymous"),
        content=data.content
    )
    return jsonify(comment), 201

@marketplace_bp.route("/comments/<comment_id>", methods=["DELETE"])
@jwt_required()
def delete_comment(comment_id):
    user_id = get_jwt_identity()
    success = layout_repo.delete_comment(comment_id, user_id)
    if not success:
        return jsonify({"error": "Comment not found or access denied."}), 404
    return jsonify({"message": "Comment deleted successfully"})

@marketplace_bp.route("/<layout_id>/rate", methods=["POST"])
@jwt_required()
@validate_schema(RatingCreateSchema)
def submit_rating(layout_id):
    user_id = get_jwt_identity()
    data: RatingCreateSchema = g.validated_data

    # Check if user is verified
    user = user_repo.get_by_id(user_id)
    if not user.get("is_verified", False):
        return jsonify({"error": "You must verify your email address to submit ratings."}), 403

    # Verify layout exists in marketplace
    exists = layout_repo.published_collection.find_one({"layout_id": layout_id})
    if not exists:
        return jsonify({"error": "Target layout not found."}), 404

    layout_repo.add_rating(layout_id, user_id, data.rating)
    stats = layout_repo.get_layout_rating_stats(layout_id)
    return jsonify({
        "message": "Rating submitted successfully.",
        "average_rating": stats["average"],
        "ratings_count": stats["count"]
    })

@marketplace_bp.route("/<layout_id>/my-rating", methods=["GET"])
@jwt_required()
def get_my_rating(layout_id):
    user_id = get_jwt_identity()
    rating = layout_repo.get_user_rating_for_layout(layout_id, user_id)
    return jsonify({"rating": rating})

@marketplace_bp.route("/<layout_id>", methods=["GET"])
@jwt_required()
def get_marketplace_layout(layout_id):
    user_id = get_jwt_identity()
    user = user_repo.get_by_id(user_id)
    if not user or not user.get("is_verified", False):
        return jsonify({"error": "You must verify your email address to browse the marketplace."}), 403

    # Verify layout exists in marketplace
    layout = layout_repo.published_collection.find_one({"layout_id": layout_id})
    if not layout:
        return jsonify({"error": "Target layout not found."}), 404

    # Map _id to id
    layout["id"] = str(layout["_id"])
    del layout["_id"]

    # Dynamic creator/publisher name from users collection
    creator = user_repo.get_by_id(layout["user_id"])
    layout["creator_name"] = creator.get("name", "Anonymous") if creator else layout.get("creator_name", "Anonymous")
    layout["creator_avatar"] = creator.get("profile_picture") if creator else None

    # Fetch latest average rating and favorite status
    rating_stats = layout_repo.get_layout_rating_stats(layout_id)
    layout["average_rating"] = rating_stats["average"]
    layout["ratings_count"] = rating_stats["count"]
    layout["is_favorite"] = layout_repo.is_favorite(user_id, layout_id)

    return jsonify(layout)

@marketplace_bp.route("/favorites", methods=["GET"])
@jwt_required()
def get_user_favorites():
    user_id = get_jwt_identity()
    favs = layout_repo.get_user_favorites(user_id)
    return jsonify(favs)
