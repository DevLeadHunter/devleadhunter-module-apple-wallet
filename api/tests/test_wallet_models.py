"""Unit tests for the Apple Wallet loyalty models — schema, relationships, enums."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from sqlalchemy import UniqueConstraint, create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base
from enums.loyalty_automation_trigger import LoyaltyAutomationTrigger
from enums.loyalty_card_status import LoyaltyCardStatus
from enums.loyalty_program_status import LoyaltyProgramStatus
from models.loyalty_automation import LoyaltyAutomation
from models.loyalty_card import LoyaltyCard
from models.loyalty_program import LoyaltyProgram
from models.loyalty_scan_event import LoyaltyScanEvent
from models.wallet_device_registration import WalletDeviceRegistration

_MODULE_TABLES = [
    LoyaltyProgram.__table__,
    LoyaltyCard.__table__,
    WalletDeviceRegistration.__table__,
    LoyaltyAutomation.__table__,
    LoyaltyScanEvent.__table__,
]


@pytest.fixture
def session() -> Iterator[Session]:
    """A session on an isolated in-memory SQLite holding only the module's tables."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection: object, _record: object) -> None:
        cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine, tables=_MODULE_TABLES)
    db = sessionmaker(bind=engine)()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def test_module_tables_are_registered() -> None:
    """Every table is known to the shared metadata, so create_all builds them."""
    assert {
        "loyalty_programs",
        "loyalty_cards",
        "wallet_device_registrations",
        "loyalty_automations",
        "loyalty_scan_events",
    } <= set(Base.metadata.tables)


def test_registration_is_unique_per_device_and_serial() -> None:
    """PassKit registers one device per pass — the schema enforces it."""
    unique_columns = {
        tuple(sorted(column.name for column in constraint.columns))
        for constraint in WalletDeviceRegistration.__table__.constraints
        if isinstance(constraint, UniqueConstraint)
    }
    assert ("device_library_identifier", "serial_number") in unique_columns


def test_enum_values_are_stable() -> None:
    """Persisted enum strings are the contract other phases depend on."""
    assert {status.value for status in LoyaltyProgramStatus} == {"draft", "active", "archived"}
    assert {status.value for status in LoyaltyCardStatus} == {"active", "completed", "revoked"}
    assert {trigger.value for trigger in LoyaltyAutomationTrigger} == {"on_scan", "broadcast"}


def test_program_card_graph_round_trips(session: Session) -> None:
    """A program, its card, device registration, automation and scan wire up both ways."""
    program = LoyaltyProgram(user_id=7, organization_name="Kebab Istanbul")
    session.add(program)
    session.flush()

    card = LoyaltyCard(
        program_id=program.id,
        user_id=7,
        serial_number="card-0001",
        authentication_token="tok-0001",
    )
    session.add(card)
    session.flush()

    session.add(
        WalletDeviceRegistration(
            card_id=card.id,
            user_id=7,
            device_library_identifier="device-A",
            push_token="push-A",
            pass_type_identifier="pass.fr.dibodev.fidelite",
            serial_number=card.serial_number,
        )
    )
    session.add(
        LoyaltyAutomation(
            program_id=program.id,
            user_id=7,
            trigger_type=LoyaltyAutomationTrigger.ON_SCAN.value,
            delay_minutes=10,
            change_message="Plus que %@ avant votre kebab offert",
        )
    )
    session.add(LoyaltyScanEvent(card_id=card.id, program_id=program.id, user_id=7, stamps_after=1))
    session.commit()

    assert card.stamps == 0
    assert card.status == LoyaltyCardStatus.ACTIVE.value
    assert program.status == LoyaltyProgramStatus.DRAFT.value

    assert program.cards == [card]
    assert card.program.id == program.id
    assert len(card.device_registrations) == 1
    assert len(card.scan_events) == 1
    assert len(program.automations) == 1


def test_deleting_a_program_cascades_to_its_cards(session: Session) -> None:
    """Deleting a program relies on DB-level cascade to drop its cards and their logs."""
    program = LoyaltyProgram(user_id=1, organization_name="Café Central")
    session.add(program)
    session.flush()
    card = LoyaltyCard(program_id=program.id, user_id=1, serial_number="c-1", authentication_token="t-1")
    session.add(card)
    session.flush()
    session.add(LoyaltyScanEvent(card_id=card.id, program_id=program.id, user_id=1, stamps_after=1))
    session.commit()

    session.delete(program)
    session.commit()

    assert session.query(LoyaltyCard).count() == 0
    assert session.query(LoyaltyScanEvent).count() == 0


def test_card_serial_number_is_unique(session: Session) -> None:
    """Two cards cannot share a serial — it is the pass serial and the QR payload."""
    program = LoyaltyProgram(user_id=1, organization_name="Salon Éclat")
    session.add(program)
    session.flush()
    session.add(LoyaltyCard(program_id=program.id, user_id=1, serial_number="dup", authentication_token="t1"))
    session.commit()

    session.add(LoyaltyCard(program_id=program.id, user_id=1, serial_number="dup", authentication_token="t2"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
