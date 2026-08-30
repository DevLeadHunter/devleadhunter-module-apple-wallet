"""Unit tests for the Apple Wallet automation engine — scheduling, broadcast, firing."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base
from enums.loyalty_automation_trigger import LoyaltyAutomationTrigger
from enums.loyalty_card_status import LoyaltyCardStatus
from enums.wallet_automation_job_status import WalletAutomationJobStatus
from models.loyalty_automation import LoyaltyAutomation
from models.loyalty_card import LoyaltyCard
from models.loyalty_program import LoyaltyProgram
from models.wallet_automation_job import WalletAutomationJob
from models.wallet_credentials import WalletCredentials
from models.wallet_device_registration import WalletDeviceRegistration
from services.wallet_automation_service import WalletAutomationError, wallet_automation_service

_MODULE_TABLES = [
    LoyaltyProgram.__table__,
    LoyaltyAutomation.__table__,
    LoyaltyCard.__table__,
    WalletAutomationJob.__table__,
    WalletCredentials.__table__,
    WalletDeviceRegistration.__table__,
]


@pytest.fixture
def session() -> Iterator[Session]:
    """A session on an isolated in-memory SQLite holding the module's tables."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine, tables=_MODULE_TABLES)
    db = sessionmaker(bind=engine)()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def _program(db: Session, *, user_id: int = 1) -> LoyaltyProgram:
    """Persist a program."""
    program = LoyaltyProgram(user_id=user_id, organization_name="Kebab Istanbul", stamps_required=10)
    db.add(program)
    db.flush()
    return program


def _automation(
    db: Session,
    program: LoyaltyProgram,
    *,
    trigger: str = LoyaltyAutomationTrigger.ON_SCAN.value,
    delay: int = 10,
    field_value: str = "-10% sur ton prochain kebab",
    is_active: bool = True,
) -> LoyaltyAutomation:
    """Persist an automation for a program."""
    automation = LoyaltyAutomation(
        program_id=program.id,
        user_id=program.user_id,
        trigger_type=trigger,
        delay_minutes=delay,
        field_value=field_value,
        is_active=is_active,
    )
    db.add(automation)
    db.flush()
    return automation


def _card(
    db: Session, program: LoyaltyProgram, *, serial: str = "card-1", status: str = LoyaltyCardStatus.ACTIVE.value
) -> LoyaltyCard:
    """Persist a card for a program."""
    card = LoyaltyCard(
        program_id=program.id,
        user_id=program.user_id,
        serial_number=serial,
        authentication_token="a" * 16,
        status=status,
    )
    db.add(card)
    db.flush()
    return card


def test_schedule_on_scan_enqueues_active_on_scan_automations(session: Session) -> None:
    """A scan schedules a pending job for each active on_scan automation."""
    program = _program(session)
    _automation(session, program, delay=10)
    card = _card(session, program)
    session.commit()

    assert wallet_automation_service.schedule_on_scan(session, card, program) == 1
    job = session.query(WalletAutomationJob).one()
    assert job.status == WalletAutomationJobStatus.PENDING.value
    assert job.card_id == card.id


def test_schedule_on_scan_does_not_stack_pending_jobs(session: Session) -> None:
    """A second scan does not pile up another pending job for the same automation."""
    program = _program(session)
    _automation(session, program)
    card = _card(session, program)
    session.commit()

    assert wallet_automation_service.schedule_on_scan(session, card, program) == 1
    assert wallet_automation_service.schedule_on_scan(session, card, program) == 0
    assert session.query(WalletAutomationJob).count() == 1


def test_schedule_on_scan_ignores_inactive_and_broadcast(session: Session) -> None:
    """Inactive and broadcast automations are not fired by a scan."""
    program = _program(session)
    _automation(session, program, is_active=False)
    _automation(session, program, trigger=LoyaltyAutomationTrigger.BROADCAST.value)
    card = _card(session, program)
    session.commit()

    assert wallet_automation_service.schedule_on_scan(session, card, program) == 0


def test_trigger_broadcast_enqueues_active_cards_only(session: Session) -> None:
    """A broadcast fans out to every active card, skipping revoked ones."""
    program = _program(session)
    automation = _automation(session, program, trigger=LoyaltyAutomationTrigger.BROADCAST.value, delay=0)
    _card(session, program, serial="a")
    _card(session, program, serial="b")
    _card(session, program, serial="c", status=LoyaltyCardStatus.REVOKED.value)
    session.commit()

    assert wallet_automation_service.trigger_broadcast(session, 1, automation.id) == 2
    assert session.query(WalletAutomationJob).count() == 2


def test_trigger_broadcast_rejects_unknown_or_non_broadcast(session: Session) -> None:
    """An unknown id or a non-broadcast automation fails loudly."""
    program = _program(session)
    on_scan = _automation(session, program, trigger=LoyaltyAutomationTrigger.ON_SCAN.value)
    session.commit()
    with pytest.raises(WalletAutomationError):
        wallet_automation_service.trigger_broadcast(session, 1, 999)
    with pytest.raises(WalletAutomationError):
        wallet_automation_service.trigger_broadcast(session, 1, on_scan.id)


def test_run_due_jobs_applies_offer_and_marks_sent(session: Session) -> None:
    """A due job writes the offer onto the card and is marked sent."""
    program = _program(session)
    _automation(session, program, field_value="Offre du jour", delay=0)
    card = _card(session, program)
    session.commit()
    wallet_automation_service.schedule_on_scan(session, card, program)

    assert wallet_automation_service.run_due_jobs(db=session) == 1
    assert session.query(LoyaltyCard).filter_by(id=card.id).one().current_offer == "Offre du jour"
    job = session.query(WalletAutomationJob).one()
    assert job.status == WalletAutomationJobStatus.SENT.value
    assert job.sent_at is not None


def test_run_due_jobs_skips_future_jobs(session: Session) -> None:
    """A job scheduled in the future is left pending."""
    program = _program(session)
    _automation(session, program, delay=60)
    card = _card(session, program)
    session.commit()
    wallet_automation_service.schedule_on_scan(session, card, program)

    assert wallet_automation_service.run_due_jobs(db=session) == 0
    assert session.query(WalletAutomationJob).one().status == WalletAutomationJobStatus.PENDING.value


def test_run_due_jobs_cancels_a_job_for_a_revoked_card(session: Session) -> None:
    """A job whose card was revoked before firing is cancelled, not applied."""
    program = _program(session)
    _automation(session, program, delay=0)
    card = _card(session, program)
    session.commit()
    wallet_automation_service.schedule_on_scan(session, card, program)
    card.status = LoyaltyCardStatus.REVOKED.value
    session.commit()

    assert wallet_automation_service.run_due_jobs(db=session) == 0
    assert session.query(WalletAutomationJob).one().status == WalletAutomationJobStatus.CANCELLED.value
