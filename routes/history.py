from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from repositories.history_repository import HistoryRepository

history_bp = Blueprint("history", __name__)
history_repo = HistoryRepository()

@history_bp.route("", methods=["GET"])
@jwt_required()
def get_history():
    user_id = get_jwt_identity()
    limit = int(request.args.get("limit", 50))
    skip = int(request.args.get("skip", 0))
    
    user_history = history_repo.get_user_history(user_id, limit, skip)
    return jsonify(user_history)

@history_bp.route("/<id>", methods=["DELETE"])
@jwt_required()
def delete_history_item(id):
    user_id = get_jwt_identity()
    success = history_repo.delete_history_item(id, user_id)
    if not success:
        return jsonify({"error": "History log not found or access denied."}), 404
        
    return jsonify({"message": "History entry deleted successfully."})

@history_bp.route("/clear", methods=["DELETE"])
@jwt_required()
def clear_history():
    user_id = get_jwt_identity()
    success = history_repo.clear_user_history(user_id)
    return jsonify({"message": "Conversion history cleared successfully."})
