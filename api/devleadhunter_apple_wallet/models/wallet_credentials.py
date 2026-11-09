"""Wallet credentials model — a user's encrypted Apple signing + APNs material."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base

if TYPE_CHECKING:
    from models.user import User


class WalletCredentials(Base):
    """A user's Apple Wallet signing credentials, stored encrypted at rest.

    Secrets (private signing key, signing certificate, WWDR chain, APNs auth key)
    are encrypted via ``encryption_service`` — the same treatment as the OAuth
    tokens on ``PaymentAccount`` / ``EmailAccount``. The identifiers
    (``pass_type_identifier``, ``team_id``, ``apns_key_id``) are not secret and are
    kept in clear so a credential set is self-describing.

    Attributes:
        user_id: Owner of the credentials (unique — one Apple account per operator).
        pass_type_identifier: Apple Pass Type ID (e.g. ``pass.fr.dibodev.fidelite``).
        team_id: Apple Developer Team ID.
        apns_key_id: Key ID of the ``.p8`` APNs auth key.
        signing_certificate: Encrypted pass signing certificate (PEM).
        signing_private_key: Encrypted private signing key (PEM).
        wwdr_certificate: Encrypted Apple WWDR intermediate certificate (PEM).
        apns_auth_key: Encrypted ``.p8`` APNs auth key.
        is_active: Whether the full credential set is present and usable.
    """

    __tablename__ = "wallet_credentials"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True, index=True)

    pass_type_identifier: Mapped[str | None] = mapped_column(String(255), nullable=True)
    team_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    apns_key_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    signing_certificate: Mapped[str | None] = mapped_column(Text, nullable=True)
    signing_private_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    wwdr_certificate: Mapped[str | None] = mapped_column(Text, nullable=True)
    apns_auth_key: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(onupdate=func.now(), nullable=True)

    user: Mapped[User] = relationship("User")

    def __repr__(self) -> str:
        """String representation of the credentials."""
        return f"<WalletCredentials id={self.id} user_id={self.user_id} active={self.is_active}>"
