from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.sqlalchemy.sqlalchemy import Base

if TYPE_CHECKING:
    from app.infrastructure.sqlalchemy.model.user import UserModel


class UserRoleModel(Base):
    """A role an account has, who gave it and when."""

    __tablename__ = "user_roles"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(32), primary_key=True)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    # (not a foreign key: the record stays when the granting account is deleted)
    granted_by: Mapped[UUID | None] = mapped_column(Uuid)

    user: Mapped["UserModel"] = relationship(back_populates="roles")
