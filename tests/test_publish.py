import pytest
from unittest.mock import MagicMock, patch
from flask import Flask, jsonify
from flask_jwt_extended import create_access_token
from routes.converter import DEFAULT_EN_AR_MAPPING

@pytest.fixture
def client():
    with patch("configuration.db.get_db") as mock_db:
        from app import create_app
        app = create_app()
        app.config["TESTING"] = True
        app.config["JWT_COOKIE_CSRF_PROTECT"] = False
        with app.test_client() as client:
            with app.app_context():
                token = create_access_token(identity="user_123")
            client.set_cookie("access_token_cookie", token)
            yield client

def test_publish_system_default_duplicate(client):
    mock_user = {"id": "user_123", "email": "test@test.com", "is_verified": True}
    # Create copy of DEFAULT_EN_AR_MAPPING with reversed key order to test order independence
    reversed_keys_mapping = dict(reversed(list(DEFAULT_EN_AR_MAPPING.items())))
    mock_layout = {
        "id": "layout_123",
        "name": "My Custom Arabic Layout",
        "mapping": reversed_keys_mapping
    }
    
    with patch("routes.layouts.user_repo.get_by_id", return_value=mock_user), \
         patch("routes.layouts.layout_repo.get_user_layout", return_value=mock_layout):
         
         response = client.post("/api/layouts/layout_123/publish", json={"tags": ["custom"]})
         assert response.status_code == 400
         assert "matches a system default layout" in response.json["error"]

def test_publish_existing_published_duplicate(client):
    mock_user = {"id": "user_123", "email": "test@test.com", "is_verified": True}
    custom_mapping = {"a": "z", "b": "y"}
    mock_layout = {
        "id": "layout_123",
        "name": "My Custom Layout",
        "mapping": custom_mapping
    }
    
    # We mock find to return a mapping with different key order {"b": "y", "a": "z"} to test order-independence
    with patch("routes.layouts.user_repo.get_by_id", return_value=mock_user), \
         patch("routes.layouts.layout_repo.get_user_layout", return_value=mock_layout), \
         patch("routes.layouts.layout_repo.published_collection.find", return_value=[{"layout_id": "other_layout_abc", "mapping": {"b": "y", "a": "z"}}]):
         
         response = client.post("/api/layouts/layout_123/publish", json={"tags": ["custom"]})
         assert response.status_code == 400
         assert "identical to another already published layout" in response.json["error"]

def test_publish_success(client):
    mock_user = {"id": "user_123", "email": "test@test.com", "is_verified": True}
    custom_mapping = {"a": "z", "b": "y"}
    mock_layout = {
        "id": "layout_123",
        "name": "My Custom Layout",
        "mapping": custom_mapping
    }
    
    with patch("routes.layouts.user_repo.get_by_id", return_value=mock_user), \
         patch("routes.layouts.layout_repo.get_user_layout", return_value=mock_layout), \
         patch("routes.layouts.layout_repo.published_collection.find", return_value=[]), \
         patch("routes.layouts.layout_repo.publish_layout", return_value=True):
         
         response = client.post("/api/layouts/layout_123/publish", json={"tags": ["custom"]})
         assert response.status_code == 200
         assert response.json["message"] == "Layout published to marketplace successfully"
