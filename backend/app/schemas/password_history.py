from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PasswordHistoryOut(BaseModel):
    id: UUID
    account_id: UUID
    account_email: str | None = None
    change_method: str
    status: str
    error_message: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PasswordHistoryDetail(PasswordHistoryOut):
    """包含密码明文的详情（需显式请求）"""
    old_password: str | None = None
    new_password: str | None = None
