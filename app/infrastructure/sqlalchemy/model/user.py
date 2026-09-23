from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.sqlalchemy.sqlalchemy import Base

if TYPE_CHECKING:
    from app.infrastructure.sqlalchemy.model.oauth_account import OAuthAccountModel
    from app.infrastructure.sqlalchemy.model.password_credential import (
        PasswordCredentialModel,
    )


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        nullable=False,
    )

    email_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    password_credential: Mapped["PasswordCredentialModel | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    oauth_accounts: Mapped[list["OAuthAccountModel"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
