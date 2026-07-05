import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.timezone import validate_timezone

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]{3,30}$")


class UserPublic(BaseModel):
    id: UUID
    username: str
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    role: str
    avatar_key: str = Field(alias="avatarKey")
    timezone: str

    model_config = {"from_attributes": True, "populate_by_name": True}


class UserPublicWithCreated(UserPublic):
    created_at: datetime = Field(alias="createdAt")

    model_config = {"from_attributes": True, "populate_by_name": True}


class RegisterRequest(BaseModel):
    username: str
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    password: str
    password_confirm: str = Field(alias="passwordConfirm")
    timezone: str = "America/Los_Angeles"

    model_config = {"populate_by_name": True}

    @field_validator("timezone")
    @classmethod
    def validate_timezone_field(cls, value: str) -> str:
        return validate_timezone(value)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if not USERNAME_PATTERN.match(value):
            msg = "Username must be 3-30 characters and contain only letters, numbers, underscore, hyphen, or period"
            raise ValueError(msg)
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 6:
            msg = "Password must be at least 6 characters"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterRequest":
        if self.password != self.password_confirm:
            msg = "Passwords do not match"
            raise ValueError(msg)
        return self


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    user: UserPublic
    access_token: str = Field(alias="accessToken")

    model_config = {"populate_by_name": True}


class AccessTokenResponse(BaseModel):
    access_token: str = Field(alias="accessToken")

    model_config = {"populate_by_name": True}


class ProfileUpdateRequest(BaseModel):
    username: str | None = None
    first_name: str | None = Field(default=None, alias="firstName")
    last_name: str | None = Field(default=None, alias="lastName")
    timezone: str | None = None
    avatar_key: str | None = Field(default=None, alias="avatarKey")

    model_config = {"populate_by_name": True}

    @field_validator("timezone")
    @classmethod
    def validate_timezone_field(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_timezone(value)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(alias="currentPassword")
    new_password: str = Field(alias="newPassword")
    new_password_confirm: str = Field(alias="newPasswordConfirm")

    model_config = {"populate_by_name": True}

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        if len(value) < 10:
            msg = "Password must be at least 10 characters"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def passwords_match(self) -> "ChangePasswordRequest":
        if self.new_password != self.new_password_confirm:
            msg = "Passwords do not match"
            raise ValueError(msg)
        return self


class DeleteAccountRequest(BaseModel):
    password: str
