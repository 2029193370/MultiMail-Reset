import uuid

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.compat import GUID


class PasswordHistory(Base):
    __tablename__ = "password_history"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    account_id = Column(GUID, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)

    encrypted_old_password = Column(Text, default="")
    encrypted_new_password = Column(Text, nullable=False)

    change_method = Column(String(20), default="manual")
    status = Column(String(20), default="pending")
    error_message = Column(Text, default="")

    created_at = Column(DateTime, server_default=func.now())

    account = relationship("Account", back_populates="password_history")
