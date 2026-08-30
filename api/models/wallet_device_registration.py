"""Wallet device registration — PassKit link between an iPhone and a loyalty card."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base

if TYPE_CHECKING:
    from models.loyalty_card import LoyaltyCard


class WalletDeviceRegistration(Base):
    """
    A device⇄pass registration created by Apple's PassKit web service.

    When a card is added to Wallet, the iPhone POSTs its push token here; that token
    is what APNs targets to wake the device for a card update.

    Attributes:
        card_id: Card this device registered for.
        user_id: Operator who owns the program (denormalized).
        device_library_identifier: Apple's per-device identifier.
        push_token: APNs token for this device + pass.
        pass_type_identifier: Pass type id from the registration route.
        serial_number: Card serial (denormalized — PassKit routes by serial).
    """

    __tablename__ = "wallet_device_registrations"
    __table_args__ = (
        UniqueConstraint("device_library_identifier", "serial_number", name="uq_wallet_registration_device_serial"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("loyalty_cards.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    device_library_identifier: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    push_token: Mapped[str] = mapped_column(String(255), nullable=False)
    pass_type_identifier: Mapped[str] = mapped_column(String(255), nullable=False)
    serial_number: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(onupdate=func.now(), nullable=True)

    card: Mapped[LoyaltyCard] = relationship("LoyaltyCard", back_populates="device_registrations")

    def __repr__(self) -> str:
        """String representation of the registration."""
        return f"<WalletDeviceRegistration id={self.id} serial={self.serial_number!r} device={self.device_library_identifier!r}>"
