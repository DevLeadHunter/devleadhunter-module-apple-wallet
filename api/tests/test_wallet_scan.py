"""Unit tests for the Apple Wallet scan service — stamping, reward, cooldown, guards."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base
from enums.loyalty_card_status import LoyaltyCardStatus
from models.loyalty_automation import LoyaltyAutomation
from models.loyalty_card import LoyaltyCard
from models.loyalty_program import LoyaltyProgram
from models.loyalty_scan_event import LoyaltyScanEvent
from models.wallet_automation_job import WalletAutomationJob
from models.wallet_credentials import WalletCredentials
from models.wallet_device_registration import WalletDeviceRegistration
from services.wallet_scan_service import WalletScanError, wallet_scan_service

_MODULE_TABLES = [
    LoyaltyProgram.__table__,
    LoyaltyAutomation.__table__,
    LoyaltyCard.__table__,
    LoyaltyScanEvent.__table__,
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


def _program(db: Session, *, stamps_required: int = 3, user_id: int = 1) -> LoyaltyProgram:
    """Persist a program with a chosen stamp goal."""
    program = LoyaltyProgram(user_id=user_id, organization_name="Kebab Istanbul", stamps_required=stamps_required)
    db.add(program)
    db.flush()
    return program


def _card(
    db: Session,
    *,
    program_id: int,
    user_id: int = 1,
    stamps: int = 0,
    status: str = LoyaltyCardStatus.ACTIVE.value,
    serial: str = "card-1",
) -> LoyaltyCard:
    """Persist a card for a program."""
    card = LoyaltyCard(
        program_id=program_id,
        user_id=user_id,
        serial_number=serial,
        authentication_token="a" * 16,
        stamps=stamps,
        status=status,
    )
    db.add(card)
    db.flush()
    return card


def test_scan_adds_a_stamp_and_logs_the_event(session: Session) -> None:
    """A scan increments the stamp, stamps the timestamp, and logs a scan event."""
    program = _program(session, stamps_required=3)
    card = _card(session, program_id=program.id)
    session.commit()

    result = wallet_scan_service.record_stamp(session, 1, card.serial_number)

    assert result.stamped is True
    assert result.throttled is False
    assert result.reward_ready is False
    assert result.pushed is False  # no APNs credentials configured
    stored = session.query(LoyaltyCard).filter_by(id=card.id).one()
    assert stored.stamps == 1
    assert stored.last_stamped_at is not None
    assert session.query(LoyaltyScanEvent).count() == 1


def test_scan_reaching_the_goal_marks_reward_ready(session: Session) -> None:
    """The stamp that reaches the goal flags reward-ready and completes the card."""
    program = _program(session, stamps_required=1)
    card = _card(session, program_id=program.id)
    session.commit()

    result = wallet_scan_service.record_stamp(session, 1, card.serial_number)

    assert result.reward_ready is True
    assert result.card.status == LoyaltyCardStatus.COMPLETED.value


def test_scan_cooldown_throttles_a_rapid_rescan(session: Session) -> None:
    """A second scan within the cooldown is throttled and adds no stamp."""
    program = _program(session, stamps_required=10)
    card = _card(session, program_id=program.id)
    session.commit()

    first = wallet_scan_service.record_stamp(session, 1, card.serial_number)
    second = wallet_scan_service.record_stamp(session, 1, card.serial_number)

    assert first.stamped is True
    assert second.stamped is False
    assert second.throttled is True
    assert session.query(LoyaltyCard).filter_by(id=card.id).one().stamps == 1


def test_scan_cooldown_zero_allows_consecutive_stamps(session: Session) -> None:
    """With the cooldown disabled, consecutive scans each add a stamp."""
    program = _program(session, stamps_required=10)
    card = _card(session, program_id=program.id)
    session.commit()

    wallet_scan_service.record_stamp(session, 1, card.serial_number, cooldown_seconds=0)
    wallet_scan_service.record_stamp(session, 1, card.serial_number, cooldown_seconds=0)

    assert session.query(LoyaltyCard).filter_by(id=card.id).one().stamps == 2


def test_scan_unknown_card_raises(session: Session) -> None:
    """Scanning an unknown serial fails loudly."""
    with pytest.raises(WalletScanError):
        wallet_scan_service.record_stamp(session, 1, "does-not-exist")


def test_scan_rejects_a_card_of_another_operator(session: Session) -> None:
    """An operator cannot stamp a card they do not own."""
    program = _program(session, stamps_required=3, user_id=1)
    card = _card(session, program_id=program.id, user_id=1)
    session.commit()
    with pytest.raises(WalletScanError):
        wallet_scan_service.record_stamp(session, 999, card.serial_number)


def test_scan_rejects_a_revoked_card(session: Session) -> None:
    """A revoked card cannot be stamped."""
    program = _program(session, stamps_required=3)
    card = _card(session, program_id=program.id, status=LoyaltyCardStatus.REVOKED.value)
    session.commit()
    with pytest.raises(WalletScanError):
        wallet_scan_service.record_stamp(session, 1, card.serial_number)
