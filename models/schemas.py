from typing import Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

class UserRegisterSchema(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        # Check password complexity: must have at least one lowercase, one uppercase, one number or special char
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[0-9\W]", v):
            raise ValueError("Password must contain at least one number or special character.")
        return v

class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False

class PasswordResetRequestSchema(BaseModel):
    email: EmailStr

class PasswordResetConfirmSchema(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[0-9\W]", v):
            raise ValueError("Password must contain at least one number or special character.")
        return v

class ProfileUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    current_password: Optional[str] = None
    new_password: Optional[str] = Field(None, min_length=8, max_length=128)

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[0-9\W]", v):
            raise ValueError("Password must contain at least one number or special character.")
        return v

class LayoutCreateSchema(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = Field("", max_length=250)
    language: str = Field(..., min_length=2, max_length=30)
    mapping: Dict[str, str] = Field(...)
    is_public: Optional[bool] = False
    direction: Optional[str] = Field("ltr", pattern="^(ltr|rtl)$")

    @field_validator('mapping')
    @classmethod
    def validate_mapping(cls, v: Dict[str, str]) -> Dict[str, str]:
        if not v:
            raise ValueError("Keyboard layout mapping cannot be empty.")
        # Validate that keys are valid keyboard inputs (length <= 5 to support some composite sequences)
        for key, val in v.items():
            if len(key) > 5:
                raise ValueError(f"Mapping key '{key}' is too long. Keys must be standard keyboard characters/sequences.")
            if not isinstance(val, str):
                raise ValueError(f"Mapping value for key '{key}' must be a string.")
        return v

class LayoutUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=250)
    language: Optional[str] = Field(None, min_length=2, max_length=30)
    mapping: Optional[Dict[str, str]] = None
    is_public: Optional[bool] = None
    direction: Optional[str] = Field(None, pattern="^(ltr|rtl)$")

    @field_validator('mapping')
    @classmethod
    def validate_mapping(cls, v: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
        if v is None:
            return v
        if not v:
            raise ValueError("Keyboard layout mapping cannot be empty.")
        for key, val in v.items():
            if len(key) > 5:
                raise ValueError(f"Mapping key '{key}' is too long.")
            if not isinstance(val, str):
                raise ValueError(f"Mapping value for key '{key}' must be a string.")
        return v

class CommentCreateSchema(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)

class RatingCreateSchema(BaseModel):
    rating: int = Field(..., ge=1, le=5)

class AIConverterSettingsSchema(BaseModel):
    preferred_model: str = Field("meta-llama/llama-3-8b-instruct:free")
    temperature: float = Field(0.3, ge=0.0, le=2.0)
    prompt_prefix: Optional[str] = Field("", max_length=500)

class ConvertTextSchema(BaseModel):
    text: str = Field(..., max_length=10000) # Limit large inputs to prevent DoS
    layout_id: str
    mode: int = Field(1, ge=1, le=4) # Mode 1-4
    ai_settings: Optional[AIConverterSettingsSchema] = None
