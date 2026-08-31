"""Wallet automation engine — defer 'update a card field, then push' jobs and fire them.

An ``on_scan`` automation enqueues a job per scan (fired after its delay); a ``broadcast``
enqueues one per active card. A worker loop applies each due job — sets the card's current
offer and best-effort pushes the update — so the customer sees a lock-screen notification.
Built on the existing file/worker + periodic-loop patterns, not a new scheduler. A single
pending job per (automation, card) is kept, so rapid scans do not stack notifications.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from core.database import SessionLocal
from enums.loyalty_automation_trigger import LoyaltyAutomationTrigger
from enums.loyalty_card_status import LoyaltyCardStatus
from enums.wallet_automation_job_status import WalletAutomationJobStatus
from models.loyalty_automation import LoyaltyAutomation
from models.loyalty_card import LoyaltyCard
from models.loyalty_program import LoyaltyProgram
from models.wallet_automation_job import WalletAutomationJob
from services.wallet_push_service import wallet_push_service

logger = logging.getLogger(__name__)

_WORKER_INTERVAL_SECONDS = 60

# Fields an operator may edit on an automation; ids/timestamps stay managed.
_AUTOMATION_EDITABLE_FIELDS = ("name", "trigger_type", "delay_minutes", "field_value", "change_message", "is_active")


class WalletAutomationError(RuntimeError):
    """Raised when a broadcast cannot be triggered (unknown or inactive automation)."""


class WalletAutomationService:
    """Schedules deferred automation jobs and runs the ones that are due."""

    def schedule_on_scan(self, db: Session, card: LoyaltyCard, program: LoyaltyProgram) -> int:
        """Enqueue the program's ``on_scan`` automations for a freshly scanned card.

        Args:
            db: Database session.
            card: The card that was just stamped.
            program: The card's program.

        Returns:
            How many jobs were scheduled.
        """
        automations = (
            db.query(LoyaltyAutomation)
            .filter(
                LoyaltyAutomation.program_id == program.id,
                LoyaltyAutomation.trigger_type == LoyaltyAutomationTrigger.ON_SCAN.value,
                LoyaltyAutomation.is_active.is_(True),
            )
            .all()
        )
        now = datetime.now(UTC).replace(tzinfo=None)
        scheduled = 0
        for automation in automations:
            if self._has_pending_job(db, automation.id, card.id):
                continue
            db.add(
                WalletAutomationJob(
                    automation_id=automation.id,
                    card_id=card.id,
                    user_id=card.user_id,
                    scheduled_at=now + timedelta(minutes=automation.delay_minutes),
                )
            )
            scheduled += 1
        if scheduled:
            db.commit()
        return scheduled

    def trigger_broadcast(self, db: Session, user_id: int, automation_id: int) -> int:
        """Enqueue a broadcast automation for every active card of its program.

        Args:
            db: Database session.
            user_id: Operator who owns the automation.
            automation_id: The broadcast automation to fan out.

        Returns:
            How many jobs were scheduled.

        Raises:
            WalletAutomationError: When no active broadcast automation matches.
        """
        automation = (
            db.query(LoyaltyAutomation)
            .filter(
                LoyaltyAutomation.id == automation_id,
                LoyaltyAutomation.user_id == user_id,
                LoyaltyAutomation.trigger_type == LoyaltyAutomationTrigger.BROADCAST.value,
                LoyaltyAutomation.is_active.is_(True),
            )
            .first()
        )
        if automation is None:
            raise WalletAutomationError(f"No active broadcast automation {automation_id} for user {user_id}.")
        cards = (
            db.query(LoyaltyCard)
            .filter(
                LoyaltyCard.program_id == automation.program_id,
                LoyaltyCard.status != LoyaltyCardStatus.REVOKED.value,
            )
            .all()
        )
        scheduled_at = datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=automation.delay_minutes)
        scheduled = 0
        for card in cards:
            if self._has_pending_job(db, automation.id, card.id):
                continue
            db.add(
                WalletAutomationJob(
                    automation_id=automation.id, card_id=card.id, user_id=user_id, scheduled_at=scheduled_at
                )
            )
            scheduled += 1
        if scheduled:
            db.commit()
        return scheduled

    def list_for_program(self, db: Session, user_id: int, program_id: int) -> list[LoyaltyAutomation]:
        """Return a program's automations, newest first.

        Args:
            db: Database session.
            user_id: Operator who owns the program.
            program_id: The program whose automations to list.

        Returns:
            The automations owned by the operator for that program.
        """
        return (
            db.query(LoyaltyAutomation)
            .filter(LoyaltyAutomation.program_id == program_id, LoyaltyAutomation.user_id == user_id)
            .order_by(LoyaltyAutomation.id.desc())
            .all()
        )

    def get_for_user(self, db: Session, user_id: int, automation_id: int) -> LoyaltyAutomation | None:
        """Return one of the operator's automations, or ``None``.

        Args:
            db: Database session.
            user_id: Operator who must own the automation.
            automation_id: The automation to fetch.

        Returns:
            The automation, or ``None`` when it does not exist or is not owned.
        """
        return (
            db.query(LoyaltyAutomation)
            .filter(LoyaltyAutomation.id == automation_id, LoyaltyAutomation.user_id == user_id)
            .first()
        )

    def list_by_program(self, db: Session, program_id: int) -> list[LoyaltyAutomation]:
        """Return a program's automations, newest first (program-scoped, for the merchant surface).

        Args:
            db: Database session.
            program_id: The program whose automations to list.

        Returns:
            The program's automations.
        """
        return (
            db.query(LoyaltyAutomation)
            .filter(LoyaltyAutomation.program_id == program_id)
            .order_by(LoyaltyAutomation.id.desc())
            .all()
        )

    def get_for_program(self, db: Session, program_id: int, automation_id: int) -> LoyaltyAutomation | None:
        """Return one of a program's automations, or ``None`` (program-scoped).

        Args:
            db: Database session.
            program_id: The program the automation must belong to.
            automation_id: The automation to fetch.

        Returns:
            The automation, or ``None`` when it does not exist or is not in the program.
        """
        return (
            db.query(LoyaltyAutomation)
            .filter(LoyaltyAutomation.id == automation_id, LoyaltyAutomation.program_id == program_id)
            .first()
        )

    def create(
        self,
        db: Session,
        user_id: int,
        program_id: int,
        *,
        name: str | None,
        trigger_type: str,
        delay_minutes: int = 0,
        field_value: str | None = None,
        change_message: str | None = None,
    ) -> LoyaltyAutomation:
        """Create an automation for a program.

        Args:
            db: Database session.
            user_id: Operator who owns the program.
            program_id: The program the automation belongs to.
            name: Human label for the automation.
            trigger_type: ``on_scan`` or ``broadcast``.
            delay_minutes: Minutes to wait before applying (clamped to >= 0).
            field_value: The offer text written onto the card.
            change_message: Lock-screen text (with ``%@``) pushed when it applies.

        Returns:
            The persisted automation.

        Raises:
            WalletAutomationError: When the trigger type is invalid.
        """
        automation = LoyaltyAutomation(
            program_id=program_id,
            user_id=user_id,
            name=name,
            trigger_type=self._validated_trigger(trigger_type),
            delay_minutes=max(delay_minutes, 0),
            field_value=field_value,
            change_message=change_message,
            is_active=True,
        )
        db.add(automation)
        db.commit()
        db.refresh(automation)
        return automation

    def update(self, db: Session, user_id: int, automation_id: int, changes: dict[str, object]) -> LoyaltyAutomation:
        """Apply an operator's edits to one of their automations.

        Args:
            db: Database session.
            user_id: Operator who must own the automation.
            automation_id: The automation to update.
            changes: The fields to set (already narrowed to those the caller sent).

        Returns:
            The updated automation.

        Raises:
            WalletAutomationError: When the automation is not found, or a trigger is invalid.
        """
        automation = self.get_for_user(db, user_id, automation_id)
        if automation is None:
            raise WalletAutomationError("Automatisation introuvable")
        if "trigger_type" in changes:
            changes["trigger_type"] = self._validated_trigger(changes["trigger_type"])
        for field in _AUTOMATION_EDITABLE_FIELDS:
            if field in changes:
                setattr(automation, field, changes[field])
        automation.delay_minutes = max(automation.delay_minutes, 0)
        db.commit()
        db.refresh(automation)
        return automation

    def delete(self, db: Session, user_id: int, automation_id: int) -> None:
        """Delete one of the operator's automations.

        Args:
            db: Database session.
            user_id: Operator who must own the automation.
            automation_id: The automation to delete.

        Raises:
            WalletAutomationError: When the automation is not found.
        """
        automation = self.get_for_user(db, user_id, automation_id)
        if automation is None:
            raise WalletAutomationError("Automatisation introuvable")
        db.delete(automation)
        db.commit()

    @staticmethod
    def _validated_trigger(value: object) -> str:
        """Return a valid trigger value, or raise.

        Args:
            value: The candidate trigger type.

        Returns:
            The validated trigger value.

        Raises:
            WalletAutomationError: When the value is not a known trigger.
        """
        try:
            return LoyaltyAutomationTrigger(value).value
        except ValueError as error:
            raise WalletAutomationError("Type de déclencheur invalide") from error

    def run_due_jobs(self, db: Session | None = None) -> int:
        """Fire every pending job whose time has come.

        Args:
            db: Session to use; a private one is opened and closed when omitted
                (the worker path, off the event loop).

        Returns:
            How many jobs fired (applied their field change).
        """
        owns_session = db is None
        session = db if db is not None else SessionLocal()
        fired = 0
        try:
            now = datetime.now(UTC).replace(tzinfo=None)
            jobs = (
                session.query(WalletAutomationJob)
                .filter(
                    WalletAutomationJob.status == WalletAutomationJobStatus.PENDING.value,
                    WalletAutomationJob.scheduled_at <= now,
                )
                .all()
            )
            for job in jobs:
                if self._execute_job(session, job):
                    fired += 1
        finally:
            if owns_session:
                session.close()
        return fired

    def _execute_job(self, db: Session, job: WalletAutomationJob) -> bool:
        """Apply one job — set the card offer, best-effort push — and mark its outcome."""
        automation = db.query(LoyaltyAutomation).filter(LoyaltyAutomation.id == job.automation_id).first()
        card = db.query(LoyaltyCard).filter(LoyaltyCard.id == job.card_id).first()
        if (
            automation is None
            or not automation.is_active
            or card is None
            or card.status == LoyaltyCardStatus.REVOKED.value
        ):
            job.status = WalletAutomationJobStatus.CANCELLED.value
            db.commit()
            return False
        try:
            card.current_offer = automation.field_value or automation.change_message
            db.commit()
        except Exception as error:
            db.rollback()
            job.status = WalletAutomationJobStatus.FAILED.value
            job.error = str(error)[:500]
            db.commit()
            logger.exception("Wallet automation job %s failed: %s", job.id, error)
            return False
        self._notify(db, job.user_id, card.id)
        job.status = WalletAutomationJobStatus.SENT.value
        job.sent_at = datetime.now(UTC).replace(tzinfo=None)
        db.commit()
        return True

    @staticmethod
    def _notify(db: Session, user_id: int, card_id: int) -> None:
        """Push the card update — best-effort, never fails the job."""
        try:
            wallet_push_service.push_card_update(db, user_id, card_id)
        except Exception as error:
            logger.info("Wallet automation push skipped for card %s: %s", card_id, error)

    @staticmethod
    def _has_pending_job(db: Session, automation_id: int, card_id: int) -> bool:
        """Whether a pending job already exists for this automation and card."""
        return (
            db.query(WalletAutomationJob)
            .filter(
                WalletAutomationJob.automation_id == automation_id,
                WalletAutomationJob.card_id == card_id,
                WalletAutomationJob.status == WalletAutomationJobStatus.PENDING.value,
            )
            .first()
            is not None
        )


wallet_automation_service = WalletAutomationService()


async def run_wallet_automation_worker_loop(interval_seconds: int = _WORKER_INTERVAL_SECONDS) -> None:
    """Periodically fire due wallet automation jobs, off the event loop.

    Args:
        interval_seconds: Delay between passes (default 60s).
    """
    while True:
        try:
            fired = await asyncio.to_thread(wallet_automation_service.run_due_jobs)
            if fired:
                logger.info("Wallet automation worker fired %s job(s)", fired)
        except Exception as exc:
            logger.exception("Wallet automation pass failed: %s", exc)
        await asyncio.sleep(interval_seconds)
