"""Loyalty card model — one end-customer's Apple Wallet card for a program."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base
from enums.loyalty_card_status import LoyaltyCardStatus

if TYPE_CHECKING:
    from models.loyalty_program import LoyaltyProgram
    from models.loyalty_scan_event import LoyaltyScanEvent
    from models.wallet_device_registration import WalletDeviceRegistration


class LoyaltyCard(Base):
    """
    A single loyalty card held by a merchant's customer.

    ``serial_number`` is the ``.pkpass`` serial (globally unique under the pass type
    id) and the payload encoded in the card's QR code; ``authentication_token`` guards
    the PassKit web-service calls for this card.

    Attributes:
        program_id: Program this card belongs to.
        user_id: Operator who owns the program (denormalized for per-user queries).
        serial_number: Unique pass serial — also the scanned QR payload.
        authentication_token: Per-card PassKit bearer token.
        stamps: Current stamp count.
        status: Card lifecycle.
        holder_name / holder_email: The end customer, when known (often anonymous).
        marketing_consent_at: When the holder consented to marketing pushes (RGPD).
        last_stamped_at: When the last stamp was applied.
        added_to_wallet_at: First device registration — the card is actually installed.
    """

    __tablename__ = "loyalty_cards"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    program_id: Mapped[int] = mapped_column(
        ForeignKey("loyalty_programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    serial_number: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    authentication_token: Mapped[str] = mapped_column(String(64), nullable=False)

    stamps: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=LoyaltyCardStatus.ACTIVE.value,
        server_default=LoyaltyCardStatus.ACTIVE.value,
        index=True,
    )

    holder_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    holder_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    marketing_consent_at: Mapped[datetime | None] = mapped_column(nullable=True)

    last_stamped_at: Mapped[datetime | None] = mapped_column(nullable=True)
    added_to_wallet_at: Mapped[datetime | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(onupdate=func.now(), nullable=True)

    program: Mapped[LoyaltyProgram] = relationship("LoyaltyProgram", back_populates="cards")
    device_registrations: Mapped[list[WalletDeviceRegistration]] = relationship(
        "WalletDeviceRegistration", back_populates="card", passive_deletes=True
    )
    scan_events: Mapped[list[LoyaltyScanEvent]] = relationship(
        "LoyaltyScanEvent", back_populates="card", passive_deletes=True
    )

    def __repr__(self) -> str:
        """String representation of the card."""
        return f"<LoyaltyCard id={self.id} serial={self.serial_number!r} stamps={self.stamps}>"
