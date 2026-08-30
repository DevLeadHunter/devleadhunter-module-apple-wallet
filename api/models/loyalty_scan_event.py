"""Loyalty scan event model — an append-only log of stamps, feeding automations."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base

if TYPE_CHECKING:
    from models.loyalty_card import LoyaltyCard


class LoyaltyScanEvent(Base):
    """
    One stamp applied to a card — the event our own system controls, which is why it
    anchors the « scan → delay → push » automations.

    Attributes:
        card_id: Card that was stamped.
        program_id: Program (denormalized for per-program analytics).
        user_id: Operator who owns the program (denormalized).
        stamps_delta: Stamps added by this event.
        stamps_after: Card stamp count after the event.
        source: Where the scan came from (merchant scan app, manual, …).
    """

    __tablename__ = "loyalty_scan_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("loyalty_cards.id", ondelete="CASCADE"), nullable=False, index=True)
    program_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    stamps_delta: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    stamps_after: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="merchant_scan", server_default="merchant_scan"
    )

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    card: Mapped[LoyaltyCard] = relationship("LoyaltyCard", back_populates="scan_events")

    def __repr__(self) -> str:
        """String representation of the scan event."""
        return f"<LoyaltyScanEvent id={self.id} card={self.card_id} stamps_after={self.stamps_after}>"
