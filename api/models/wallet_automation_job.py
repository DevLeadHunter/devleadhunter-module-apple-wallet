"""Wallet automation job model — a deferred 'update a card field, then push' task."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.database import Base
from enums.wallet_automation_job_status import WalletAutomationJobStatus


class WalletAutomationJob(Base):
    """A scheduled run of a loyalty automation against one card.

    An ``on_scan`` automation enqueues one job per scan (fired after its delay); a
    ``broadcast`` enqueues one per active card. A worker loop applies the field change
    and pushes the update when ``scheduled_at`` is due.

    Attributes:
        automation_id: The automation this job runs.
        card_id: The card the automation targets.
        user_id: Operator who owns the program (denormalized).
        scheduled_at: When the job becomes due.
        status: Job lifecycle.
        error: Last failure reason, when it failed.
    """

    __tablename__ = "wallet_automation_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    automation_id: Mapped[int] = mapped_column(
        ForeignKey("loyalty_automations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    card_id: Mapped[int] = mapped_column(ForeignKey("loyalty_cards.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    scheduled_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=WalletAutomationJobStatus.PENDING.value,
        server_default=WalletAutomationJobStatus.PENDING.value,
        index=True,
    )
    error: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        """String representation of the job."""
        return f"<WalletAutomationJob id={self.id} automation={self.automation_id} card={self.card_id} status={self.status}>"
