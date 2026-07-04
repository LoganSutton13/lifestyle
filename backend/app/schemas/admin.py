from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.auth import UserPublicWithCreated


class AdminStatsResponse(BaseModel):
    clients: int
    coaches: int
    admins: int
    recent_users: list[UserPublicWithCreated] = Field(alias="recentUsers")

    model_config = {"populate_by_name": True}


class AdminUserListResponse(BaseModel):
    items: list[UserPublicWithCreated]
    page: int
    page_size: int = Field(alias="pageSize")
    total: int
    has_next_page: bool = Field(alias="hasNextPage")

    model_config = {"populate_by_name": True}


class CreateCoachRequest(BaseModel):
    username: str
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    password: str
    password_confirm: str = Field(alias="passwordConfirm")

    model_config = {"populate_by_name": True}

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 10:
            msg = "Password must be at least 10 characters"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def passwords_match(self) -> "CreateCoachRequest":
        if self.password != self.password_confirm:
            msg = "Passwords do not match"
            raise ValueError(msg)
        return self


class RoleUpdateRequest(BaseModel):
    role: str


class AdminDeleteUserRequest(BaseModel):
    admin_password: str = Field(alias="adminPassword")
    confirm_username: str = Field(alias="confirmUsername")

    model_config = {"populate_by_name": True}
