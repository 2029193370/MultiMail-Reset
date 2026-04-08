import json
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator


class PasswordRule(BaseModel):
    length: int = 16
    uppercase: bool = True
    lowercase: bool = True
    digits: bool = True
    special: bool = True
    prefix: str = ""
    suffix: str = ""
    exclude_chars: str = "lI1O0"


class AccountCreate(BaseModel):
    email: str
    provider_type: str
    password: str
    display_name: str = ""
    auto_change_enabled: bool = False
    change_interval_days: int = 30
    password_rule: PasswordRule | None = None
    notes: str = ""


class AccountUpdate(BaseModel):
    display_name: str | None = None
    password: str | None = None
    auto_change_enabled: bool | None = None
    change_interval_days: int | None = None
    password_rule: PasswordRule | None = None
    notes: str | None = None
    status: str | None = None


class AccountOut(BaseModel):
    id: UUID
    email: str
    provider_type: str
    display_name: str
    auto_change_enabled: bool
    change_interval_days: int
    password_rule: PasswordRule | None = None
    last_password_change: datetime | None
    next_password_change: datetime | None
    status: str
    notes: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("password_rule", mode="before")
    @classmethod
    def parse_password_rule(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return None
        return v


class AccountWithPassword(AccountOut):
    """包含解密后密码的响应（仅在显式请求时返回）"""
    current_password: str
