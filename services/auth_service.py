import bcrypt
import requests
import datetime
from typing import Dict, Any, Optional
from configuration.db import get_db
from configuration.config import Config, logger

class AuthService:
    def __init__(self):
        self.db = get_db()
        self.sessions_collection = self.db["sessions"]

    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False

    # --- Session / Refresh Token Revocation tracking ---
    
    def register_session(self, user_id: str, jti: str, expires_in_seconds: int) -> None:
        expiry_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in_seconds)
        self.sessions_collection.update_one(
            {"user_id": user_id, "jti": jti},
            {"$set": {
                "user_id": user_id,
                "jti": jti,
                "expires_at": expiry_time,
                "created_at": datetime.datetime.utcnow()
            }},
            upsert=True
        )

    def is_session_revoked(self, jti: str) -> bool:
        # If we find the token in the sessions collection, it is NOT revoked.
        # If it's missing (either deleted on logout or expired by TTL index), it is revoked.
        session = self.sessions_collection.find_one({"jti": jti})
        return session is None

    def revoke_session(self, jti: str) -> None:
        self.sessions_collection.delete_one({"jti": jti})

    def revoke_all_user_sessions(self, user_id: str) -> None:
        self.sessions_collection.delete_many({"user_id": user_id})

    # --- Google OAuth Flow ---

    def verify_google_code(self, auth_code: str) -> Optional[Dict[str, Any]]:
        """
        Exchanges code for access token and retrieves profile info from Google.
        """
        if not Config.GOOGLE_CLIENT_ID or not Config.GOOGLE_CLIENT_SECRET:
            logger.error("Google OAuth client ID or secret is not configured.")
            return None

        token_url = "https://oauth2.googleapis.com/token"
        payload = {
            "code": auth_code,
            "client_id": Config.GOOGLE_CLIENT_ID,
            "client_secret": Config.GOOGLE_CLIENT_SECRET,
            "redirect_uri": Config.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code"
        }

        try:
            # Exchange auth code for tokens
            response = requests.post(token_url, data=payload, timeout=10)
            if response.status_code != 200:
                logger.error(f"Google Token Exchange failed: {response.text}")
                return None
            
            token_data = response.json()
            access_token = token_data.get("access_token")
            if not access_token:
                logger.error("No access token found in Google OAuth response.")
                return None

            # Retrieve user profile info using access token
            userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
            headers = {"Authorization": f"Bearer {access_token}"}
            userinfo_response = requests.get(userinfo_url, headers=headers, timeout=10)
            
            if userinfo_response.status_code != 200:
                logger.error(f"Google User Info retrieval failed: {userinfo_response.text}")
                return None
                
            return userinfo_response.json()
            
        except Exception as e:
            logger.error(f"Exception raised during Google OAuth verification: {e}")
            return None
