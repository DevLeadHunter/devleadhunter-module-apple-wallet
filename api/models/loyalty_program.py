"""Loyalty program model — a merchant's Apple Wallet loyalty-card configuration."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base
from enums.loyalty_program_status import LoyaltyProgramStatus

if TYPE_CHECKING:
    from models.loyalty_automation import LoyaltyAutomation
    from models.loyalty_card import LoyaltyCard


class LoyaltyProgram(Base):
    """
    A merchant's loyalty-card configuration, scoped to the operator who sells it.

    One program issues many end-customer cards; its branding and stamp rules are
    baked into every ``.pkpass`` generated for the merchant.

    Attributes:
        user_id: Operator who owns this program (denormalized, no FK — house style).
        prospect_id: Merchant prospect this program was built for.
        order_id: Sale that turned the program into a paying subscription.
        organization_name: Merchant name shown on the card (``organizationName``).
        stamps_required: Number of stamps that unlocks the reward.
        reward_label: What the customer earns (e.g. « 1 kebab offert »).
        default_change_message: Lock-screen text (with ``%@``) pushed on a stamp.
        logo_url: Merchant logo baked onto the card.
        background_color / foreground_color / label_color: Card colors (rgb() strings).
        status: Program lifecycle.
    """

    __tablename__ = "loyalty_programs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    prospect_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    order_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    organization_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    stamps_required: Mapped[int] = mapped_column(Integer, nullable=False, default=10, server_default="10")
    reward_label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    default_change_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    background_color: Mapped[str | None] = mapped_column(String(32), nullable=True)
    foreground_color: Mapped[str | None] = mapped_column(String(32), nullable=True)
    label_color: Mapped[str | None] = mapped_column(String(32), nullable=True)

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=LoyaltyProgramStatus.DRAFT.value,
        server_default=LoyaltyProgramStatus.DRAFT.value,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(onupdate=func.now(), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    cards: Mapped[list[LoyaltyCard]] = relationship("LoyaltyCard", back_populates="program", passive_deletes=True)
    automations: Mapped[list[LoyaltyAutomation]] = relationship(
        "LoyaltyAutomation", back_populates="program", passive_deletes=True
    )

    def __repr__(self) -> str:
        """String representation of the program."""
        return f"<LoyaltyProgram id={self.id} org={self.organization_name!r} status={self.status}>"
