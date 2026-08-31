"""Wallet scan service — the 'add a stamp' / 'redeem the reward' actions on a card.

A stamp is applied by scanning a customer's card QR (its serial): we add one stamp, log
the event, and best-effort push the update so the card refreshes on the customer's lock
screen. A short cooldown debounces accidental double scans. The operator stamps by owning
the card (``record_stamp``); a merchant stamps within their own program
(``stamp_for_program`` / ``redeem_for_program``) — both route through the same core.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from enums.loyalty_card_status import LoyaltyCardStatus
from models.loyalty_card import LoyaltyCard
from models.loyalty_program import LoyaltyProgram
from models.loyalty_scan_event import LoyaltyScanEvent
from services.wallet_automation_service import wallet_automation_service
from services.wallet_push_service import wallet_push_service
from services.wallet_subscription_service import wallet_subscription_service

logger = logging.getLogger(__name__)

_SCAN_COOLDOWN_SECONDS = 15


class WalletScanError(RuntimeError):
    """Raised when a stamp/redeem cannot apply (unknown card, wrong owner, or not ready)."""


@dataclass(frozen=True)
class WalletScanResult:
    """Outcome of a stamp."""

    card: LoyaltyCard
    required: int
    stamped: bool  # a stamp was actually added (False when throttled)
    throttled: bool  # the same card was scanned again within the cooldown
    reward_ready: bool  # the stamp goal is reached
    pushed: bool  # the APNs update fired (best-effort; False without credentials)


@dataclass(frozen=True)
class WalletRedeemResult:
    """Outcome of a redeem (reward handed over, card reset)."""

    card: LoyaltyCard
    pushed: bool


class WalletScanService:
    """Applies a stamp (or a redeem) to a card and notifies the customer's device."""

    def record_stamp(
        self, db: Session, user_id: int, serial_number: str, *, cooldown_seconds: int = _SCAN_COOLDOWN_SECONDS
    ) -> WalletScanResult:
        """Add a stamp to one of the operator's cards, then push the update.

        Args:
            db: Database session.
            user_id: Operator who owns the card (scopes the lookup).
            serial_number: Card serial read from the scanned QR.
            cooldown_seconds: Minimum delay between two stamps on the same card.

        Returns:
            The scan outcome, including the refreshed card.

        Raises:
            WalletScanError: When the card is unknown, not the operator's, or revoked.
        """
        card = (
            db.query(LoyaltyCard)
            .filter(LoyaltyCard.serial_number == serial_number, LoyaltyCard.user_id == user_id)
            .first()
        )
        if card is None:
            raise WalletScanError(f"No loyalty card {serial_number!r} for user {user_id}.")
        return self._apply_stamp(db, card, cooldown_seconds=cooldown_seconds)

    def stamp_for_program(
        self, db: Session, program_id: int, serial_number: str, *, cooldown_seconds: int = _SCAN_COOLDOWN_SECONDS
    ) -> WalletScanResult:
        """Add a stamp to a card of the merchant's own program.

        Args:
            db: Database session.
            program_id: The merchant's program (scopes the lookup).
            serial_number: Card serial to stamp.
            cooldown_seconds: Minimum delay between two stamps on the same card.

        Returns:
            The scan outcome, including the refreshed card.

        Raises:
            WalletScanError: When the card is not in the program, or is revoked.
        """
        card = (
            db.query(LoyaltyCard)
            .filter(LoyaltyCard.serial_number == serial_number, LoyaltyCard.program_id == program_id)
            .first()
        )
        if card is None:
            raise WalletScanError(f"No loyalty card {serial_number!r} in program {program_id}.")
        return self._apply_stamp(db, card, cooldown_seconds=cooldown_seconds)

    def redeem_for_program(self, db: Session, program_id: int, serial_number: str) -> WalletRedeemResult:
        """Hand over the reward and reset a completed card, within the merchant's program.

        Args:
            db: Database session.
            program_id: The merchant's program (scopes the lookup).
            serial_number: Card serial to redeem.

        Returns:
            The redeem outcome, including the reset card.

        Raises:
            WalletScanError: When the card is not in the program, or the reward is not yet reached.
        """
        card = (
            db.query(LoyaltyCard)
            .filter(LoyaltyCard.serial_number == serial_number, LoyaltyCard.program_id == program_id)
            .first()
        )
        if card is None:
            raise WalletScanError(f"No loyalty card {serial_number!r} in program {program_id}.")
        program = self._program_of(db, card)
        self._ensure_operable(db, program)
        if card.stamps < program.stamps_required:
            raise WalletScanError(f"Loyalty card {serial_number!r} has not reached its reward yet.")

        stamps_before = card.stamps
        card.stamps = 0
        card.status = LoyaltyCardStatus.ACTIVE.value
        db.add(
            LoyaltyScanEvent(
                card_id=card.id,
                program_id=program.id,
                user_id=program.user_id,
                stamps_delta=-stamps_before,
                stamps_after=0,
                source="merchant_redeem",
            )
        )
        db.commit()
        db.refresh(card)
        return WalletRedeemResult(card=card, pushed=self._notify(db, program.user_id, card.id))

    def _apply_stamp(self, db: Session, card: LoyaltyCard, *, cooldown_seconds: int) -> WalletScanResult:
        """Add one stamp to a resolved card (shared by the operator and merchant paths)."""
        if card.status == LoyaltyCardStatus.REVOKED.value:
            raise WalletScanError(f"Loyalty card {card.serial_number!r} is revoked.")
        program = self._program_of(db, card)
        self._ensure_operable(db, program)

        now = datetime.now(UTC).replace(tzinfo=None)
        if card.last_stamped_at is not None and now - card.last_stamped_at < timedelta(seconds=cooldown_seconds):
            return WalletScanResult(
                card=card,
                required=program.stamps_required,
                stamped=False,
                throttled=True,
                reward_ready=card.stamps >= program.stamps_required,
                pushed=False,
            )

        card.stamps += 1
        card.last_stamped_at = now
        reward_ready = card.stamps >= program.stamps_required
        if reward_ready:
            card.status = LoyaltyCardStatus.COMPLETED.value
        db.add(
            LoyaltyScanEvent(
                card_id=card.id,
                program_id=program.id,
                user_id=program.user_id,
                stamps_delta=1,
                stamps_after=card.stamps,
                source="merchant_scan",
            )
        )
        db.commit()
        db.refresh(card)
        wallet_automation_service.schedule_on_scan(db, card, program)
        return WalletScanResult(
            card=card,
            required=program.stamps_required,
            stamped=True,
            throttled=False,
            reward_ready=reward_ready,
            pushed=self._notify(db, program.user_id, card.id),
        )

    @staticmethod
    def _program_of(db: Session, card: LoyaltyCard) -> LoyaltyProgram:
        """Resolve a card's program, raising when it is missing."""
        program = db.query(LoyaltyProgram).filter(LoyaltyProgram.id == card.program_id).first()
        if program is None:
            raise WalletScanError(f"Loyalty card {card.serial_number!r} has no program.")
        return program

    @staticmethod
    def _ensure_operable(db: Session, program: LoyaltyProgram) -> None:
        """Raise when the program is closed (deleted) or suspended (subscription lapsed)."""
        if program.deleted_at is not None:
            raise WalletScanError(f"Loyalty program {program.id} is closed.")
        if not wallet_subscription_service.has_access(db, program.id):
            raise WalletScanError(f"Loyalty program {program.id} is suspended (subscription past due).")

    @staticmethod
    def _notify(db: Session, user_id: int, card_id: int) -> bool:
        """Push the card update to its devices — best-effort, never blocks the action."""
        try:
            wallet_push_service.push_card_update(db, user_id, card_id)
            return True
        except Exception as error:
            logger.info("Wallet push skipped for card %s: %s", card_id, error)
            return False


wallet_scan_service = WalletScanService()
