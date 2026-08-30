"""Merchant dashboard service — the read views a merchant sees of their own program."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from enums.loyalty_card_status import LoyaltyCardStatus
from models.loyalty_card import LoyaltyCard
from models.loyalty_program import LoyaltyProgram

_CARDS_PAGE_SIZE = 100


@dataclass(frozen=True)
class MerchantStats:
    """Headline counters for a merchant's loyalty program."""

    cards_issued: int
    cards_installed: int
    rewards_ready: int
    total_stamps: int


class MerchantDashboardService:
    """Read-only views over a merchant's own program, cards and figures."""

    def get_program(self, db: Session, program_id: int) -> LoyaltyProgram | None:
        """Return the merchant's program.

        Args:
            db: Database session.
            program_id: The merchant's program.

        Returns:
            The program, or ``None`` when it no longer exists.
        """
        return db.query(LoyaltyProgram).filter(LoyaltyProgram.id == program_id).first()

    def stats(self, db: Session, program_id: int) -> MerchantStats:
        """Compute headline counters for a program.

        Args:
            db: Database session.
            program_id: The merchant's program.

        Returns:
            The counters (all zero when the program has no cards yet).
        """
        base = db.query(LoyaltyCard).filter(LoyaltyCard.program_id == program_id)
        cards_issued = base.count()
        cards_installed = base.filter(LoyaltyCard.added_to_wallet_at.isnot(None)).count()
        rewards_ready = base.filter(LoyaltyCard.status == LoyaltyCardStatus.COMPLETED.value).count()
        total_stamps = (
            db.query(func.coalesce(func.sum(LoyaltyCard.stamps), 0))
            .filter(LoyaltyCard.program_id == program_id)
            .scalar()
        )
        return MerchantStats(
            cards_issued=cards_issued,
            cards_installed=cards_installed,
            rewards_ready=rewards_ready,
            total_stamps=int(total_stamps or 0),
        )

    def cards(self, db: Session, program_id: int) -> list[LoyaltyCard]:
        """Return the program's cards, most recently stamped first.

        Args:
            db: Database session.
            program_id: The merchant's program.

        Returns:
            Up to a page of cards.
        """
        return (
            db.query(LoyaltyCard)
            .filter(LoyaltyCard.program_id == program_id)
            .order_by(LoyaltyCard.last_stamped_at.is_(None), LoyaltyCard.last_stamped_at.desc(), LoyaltyCard.id.desc())
            .limit(_CARDS_PAGE_SIZE)
            .all()
        )


merchant_dashboard_service = MerchantDashboardService()
