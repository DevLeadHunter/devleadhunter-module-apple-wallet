"""Loyalty automation model — a rule that updates a card field and pushes a notification."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from core.database import Base

if TYPE_CHECKING:
    from models.loyalty_program import LoyaltyProgram


class LoyaltyAutomation(Base):
    """
    A merchant automation: change a card field so Wallet shows a ``changeMessage`` on
    the lock screen after an APNs push.

    ``on_scan`` fires for the scanned card after ``delay_minutes``; ``broadcast``
    applies to every active card of the program. ``trigger_type`` holds a
    :class:`~enums.loyalty_automation_trigger.LoyaltyAutomationTrigger` value.

    Attributes:
        program_id: Program the automation belongs to.
        user_id: Operator who owns the program (denormalized).
        trigger_type: What fires the automation (on_scan | broadcast).
        delay_minutes: For on_scan, minutes to wait after the stamp.
        field_key: Card field the automation changes.
        field_value: New value written to that field.
        change_message: Lock-screen text (with ``%@``) shown when the field changes.
        is_active: Whether the automation runs.
    """

    __tablename__ = "loyalty_automations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    program_id: Mapped[int] = mapped_column(
        ForeignKey("loyalty_programs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    trigger_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    delay_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")

    field_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    field_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    change_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(onupdate=func.now(), nullable=True)

    program: Mapped[LoyaltyProgram] = relationship("LoyaltyProgram", back_populates="automations")

    def __repr__(self) -> str:
        """String representation of the automation."""
        return f"<LoyaltyAutomation id={self.id} trigger={self.trigger_type} program={self.program_id}>"
