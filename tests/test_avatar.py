import io
import pytest
from unittest.mock import MagicMock, patch
from flask import Flask, jsonify
from flask_jwt_extended import create_access_token

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

def test_upload_avatar_no_file(client):
    with patch("routes.auth.user_repo.get_by_id", return_value={"id": "user_123", "email": "test@test.com"}):
        response = client.post("/api/auth/profile/avatar")
        assert response.status_code == 400
        assert response.json["error"] == "No file part in the request"

def test_upload_avatar_empty_filename(client):
    with patch("routes.auth.user_repo.get_by_id", return_value={"id": "user_123"}):
        data = {"avatar": (io.BytesIO(b""), "")}
        response = client.post("/api/auth/profile/avatar", data=data, content_type="multipart/form-data")
        assert response.status_code == 400
        assert response.json["error"] == "No file selected for uploading"

def test_upload_avatar_too_large(client):
    with patch("routes.auth.user_repo.get_by_id", return_value={"id": "user_123"}):
        large_data = b"x" * (2 * 1024 * 1024 + 1)
        data = {"avatar": (io.BytesIO(large_data), "test.png")}
        response = client.post("/api/auth/profile/avatar", data=data, content_type="multipart/form-data")
        assert response.status_code == 400
        assert response.json["error"] == "File size exceeds the 2MB limit"

def test_upload_avatar_invalid_magic_bytes(client):
    with patch("routes.auth.user_repo.get_by_id", return_value={"id": "user_123"}):
        fake_png_data = b"This is not a PNG file, it's just text!"
        data = {"avatar": (io.BytesIO(fake_png_data), "fake.png")}
        response = client.post("/api/auth/profile/avatar", data=data, content_type="multipart/form-data")
        assert response.status_code == 400
        assert response.json["error"] == "Invalid file type. Only JPEG, PNG, GIF, and WEBP images are allowed."

def test_upload_avatar_success(client):
    valid_png_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"x" * 100
    mock_user = {"id": "user_123", "email": "test@test.com", "profile_picture": None}
    
    with patch("routes.auth.user_repo.get_by_id", return_value=mock_user), \
         patch("routes.auth.user_repo.update") as mock_update, \
         patch("werkzeug.datastructures.FileStorage.save") as mock_save:
         
         data = {"avatar": (io.BytesIO(valid_png_data), "avatar.png")}
         response = client.post("/api/auth/profile/avatar", data=data, content_type="multipart/form-data")
         
         assert response.status_code == 200
         assert response.json["message"] == "Profile picture updated successfully"
         assert response.json["profile_picture"].startswith("/static/uploads/avatars/")
         assert mock_update.called
         assert mock_save.called
