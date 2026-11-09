"""Merchant account model — a merchant's login to their own wallet dashboard."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.database import Base


class MerchantAccount(Base):
    """Credentials the merchant uses to manage their own loyalty program.

    A dedicated login (like the Storyblok handover for websites): one account per
    program, separate from the operator's ``User``. The JWT it issues carries a
    ``merchant`` type so operator routes never accept it and vice versa.

    Attributes:
        program_id: The loyalty program this account manages (one account per program).
        email: Login email (auto-generated at provisioning).
        hashed_password: bcrypt hash of the password.
        is_active: Whether the account can log in.
        last_login_at: When the merchant last authenticated.
    """

    __tablename__ = "merchant_accounts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    program_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(onupdate=func.now(), nullable=True)

    def __repr__(self) -> str:
        """String representation of the merchant account."""
        return f"<MerchantAccount id={self.id} program={self.program_id} email={self.email!r}>"
