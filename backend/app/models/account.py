import uuid

from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text, func
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.compat import GUID


class Account(Base):
    __tablename__ = "accounts"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    provider_type = Column(String(50), nullable=False)
    encrypted_password = Column(Text, nullable=False)
    display_name = Column(String(255), default="")

    auto_change_enabled = Column(Boolean, default=False)
    change_interval_days = Column(Integer, default=30)
    password_rule = Column(Text, default=None)

    last_password_change = Column(DateTime, default=None)
    next_password_change = Column(DateTime, default=None)
    status = Column(String(20), default="active")

    notes = Column(Text, default="")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    password_history = relationship(
        "PasswordHistory", back_populates="account", cascade="all, delete-orphan",
        order_by="desc(PasswordHistory.created_at)",
    )
