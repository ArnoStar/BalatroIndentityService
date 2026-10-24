from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.sqlalchemy.sqlalchemy import Base

if TYPE_CHECKING:
    from app.infrastructure.sqlalchemy.model.user import UserModel


class OAuthAccountModel(Base):
    __tablename__ = "oauth_accounts"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(50))
    provider_user_id: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["UserModel"] = relationship(back_populates="oauth_accounts")

    __table_args__ = (
        # one account of a provider is one user
        UniqueConstraint(
            "provider", "provider_user_id", name="uq_oauth_accounts_provider_user"
        ),
        # and a user has at most one account per provider
        UniqueConstraint("user_id", "provider", name="uq_oauth_accounts_user_provider"),
    )
