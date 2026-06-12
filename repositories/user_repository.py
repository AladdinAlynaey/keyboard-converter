from repositories.base import BaseRepository
from typing import Dict, Any, Optional
import datetime

class UserRepository(BaseRepository):
    def __init__(self):
        super().__init__("users")

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        return self.find_one({"email": email.lower().strip()})

    def get_by_google_id(self, google_id: str) -> Optional[Dict[str, Any]]:
        return self.find_one({"google_id": google_id})

    def create_user(self, email: str, password_hash: Optional[str] = None, google_id: Optional[str] = None, name: Optional[str] = None) -> Dict[str, Any]:
        user_data = {
            "email": email.lower().strip(),
            "name": name or email.split("@")[0],
            "password_hash": password_hash,
            "google_id": google_id,
            "is_verified": False if google_id is None else True, # Google users are pre-verified
            "verification_token": None if google_id is not None else None, # populated when token is created
            "verification_token_expires": None,
            "password_reset_token": None,
            "password_reset_expires": None,
            "profile_picture": None,
            "ai_settings": {
                "preferred_model": "meta-llama/llama-3.3-70b-instruct:free",
                "temperature": 0.3,
                "prompt_prefix": ""
            },
            "created_at": datetime.datetime.utcnow()
        }
        user_id = self.create(user_data)
        user_data["id"] = user_id
        if "_id" in user_data:
            del user_data["_id"]
        return user_data

    def set_verification_token(self, user_id: str, token: str, expires_in_hours: int = 24) -> bool:
        expires = datetime.datetime.utcnow() + datetime.timedelta(hours=expires_in_hours)
        return self.update(user_id, {
            "verification_token": token,
            "verification_token_expires": expires
        })

    def verify_email(self, token: str) -> Optional[Dict[str, Any]]:
        user = self.find_one({
            "verification_token": token,
            "verification_token_expires": {"$gt": datetime.datetime.utcnow()}
        })
        if user:
            self.update(user["id"], {
                "is_verified": True,
                "verification_token": None,
                "verification_token_expires": None
            })
            # Reload updated user
            return self.get_by_id(user["id"])
        return None

    def set_password_reset_token(self, user_id: str, token: str, expires_in_hours: int = 2) -> bool:
        expires = datetime.datetime.utcnow() + datetime.timedelta(hours=expires_in_hours)
        return self.update(user_id, {
            "password_reset_token": token,
            "password_reset_expires": expires
        })

    def reset_password(self, token: str, new_password_hash: str) -> Optional[Dict[str, Any]]:
        user = self.find_one({
            "password_reset_token": token,
            "password_reset_expires": {"$gt": datetime.datetime.utcnow()}
        })
        if user:
            self.update(user["id"], {
                "password_hash": new_password_hash,
                "password_reset_token": None,
                "password_reset_expires": None
            })
            return user
        return None

    def update_profile(self, user_id: str, name: Optional[str] = None, password_hash: Optional[str] = None) -> bool:
        update_data = {}
        if name:
            update_data["name"] = name
        if password_hash:
            update_data["password_hash"] = password_hash
        
        if not update_data:
            return False
        return self.update(user_id, update_data)

    def update_ai_settings(self, user_id: str, settings: Dict[str, Any]) -> bool:
        # Fetch current user to preserve existing sub-keys
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        current_settings = user.get("ai_settings", {})
        current_settings.update(settings)
        return self.update(user_id, {"ai_settings": current_settings})
