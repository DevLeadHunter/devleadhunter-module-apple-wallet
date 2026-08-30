"""Unit tests for the Apple Wallet PassKit service — auth, registration, update discovery."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base
from enums.wallet_registration_outcome import WalletRegistrationOutcome
from models.loyalty_card import LoyaltyCard
from models.wallet_device_registration import WalletDeviceRegistration
from services.wallet_passkit_service import wallet_passkit_service


@pytest.fixture
def session() -> Iterator[Session]:
    """A session on an isolated in-memory SQLite with the card + registration tables."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine, tables=[LoyaltyCard.__table__, WalletDeviceRegistration.__table__])
    db = sessionmaker(bind=engine)()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def _card(db: Session, *, serial: str, token: str = "a" * 16, created_at: datetime | None = None) -> LoyaltyCard:
    """Persist a loyalty card with a chosen serial, token and optional creation time."""
    card = LoyaltyCard(program_id=1, user_id=1, serial_number=serial, authentication_token=token)
    if created_at is not None:
        card.created_at = created_at
    db.add(card)
    db.flush()
    return card


def test_parse_pass_token() -> None:
    """Only a well-formed ``ApplePass <token>`` header yields a token."""
    assert wallet_passkit_service.parse_pass_token("ApplePass abc123") == "abc123"
    assert wallet_passkit_service.parse_pass_token("Bearer abc123") is None
    assert wallet_passkit_service.parse_pass_token("ApplePass ") is None
    assert wallet_passkit_service.parse_pass_token(None) is None


def test_authenticated_card_matches_only_the_right_token(session: Session) -> None:
    """A card authenticates with its exact token and nothing else."""
    _card(session, serial="s1", token="tok-123456789012")
    session.commit()
    assert (
        wallet_passkit_service.authenticated_card(session, serial_number="s1", pass_token="tok-123456789012")
        is not None
    )
    assert wallet_passkit_service.authenticated_card(session, serial_number="s1", pass_token="wrong") is None
    assert (
        wallet_passkit_service.authenticated_card(session, serial_number="absent", pass_token="tok-123456789012")
        is None
    )


def test_register_device_creates_then_refreshes(session: Session) -> None:
    """First registration stores the token and marks the card installed; the second refreshes it."""
    _card(session, serial="s1", token="tok")
    session.commit()

    created = wallet_passkit_service.register_device(
        session,
        device_library_identifier="dev-1",
        pass_type_identifier="pass.x",
        serial_number="s1",
        push_token="push-1",
        pass_token="tok",
    )
    assert created == WalletRegistrationOutcome.CREATED
    assert session.query(WalletDeviceRegistration).one().push_token == "push-1"
    assert session.query(LoyaltyCard).filter_by(serial_number="s1").one().added_to_wallet_at is not None

    refreshed = wallet_passkit_service.register_device(
        session,
        device_library_identifier="dev-1",
        pass_type_identifier="pass.x",
        serial_number="s1",
        push_token="push-2",
        pass_token="tok",
    )
    assert refreshed == WalletRegistrationOutcome.ALREADY_REGISTERED
    assert session.query(WalletDeviceRegistration).one().push_token == "push-2"


def test_register_device_rejects_a_bad_token(session: Session) -> None:
    """A wrong token registers nothing and reports unauthorized."""
    _card(session, serial="s1", token="tok")
    session.commit()
    outcome = wallet_passkit_service.register_device(
        session,
        device_library_identifier="dev-1",
        pass_type_identifier="pass.x",
        serial_number="s1",
        push_token="push-1",
        pass_token="wrong",
    )
    assert outcome == WalletRegistrationOutcome.UNAUTHORIZED
    assert session.query(WalletDeviceRegistration).count() == 0


def test_unregister_device(session: Session) -> None:
    """An authenticated unregister removes the row; a wrong token is refused."""
    _card(session, serial="s1", token="tok")
    session.commit()
    wallet_passkit_service.register_device(
        session,
        device_library_identifier="dev-1",
        pass_type_identifier="pass.x",
        serial_number="s1",
        push_token="push-1",
        pass_token="tok",
    )

    deleted = wallet_passkit_service.unregister_device(
        session, device_library_identifier="dev-1", serial_number="s1", pass_token="tok"
    )
    assert deleted == WalletRegistrationOutcome.DELETED
    assert session.query(WalletDeviceRegistration).count() == 0

    refused = wallet_passkit_service.unregister_device(
        session, device_library_identifier="dev-1", serial_number="s1", pass_token="nope"
    )
    assert refused == WalletRegistrationOutcome.UNAUTHORIZED


def test_serials_updated_since_filters_by_tag(session: Session) -> None:
    """Only serials changed after the tag are returned; an unknown device yields nothing."""
    old_card = _card(session, serial="old", token="t1", created_at=datetime(2026, 1, 1))
    new_card = _card(session, serial="new", token="t2", created_at=datetime(2026, 6, 1))
    session.commit()
    session.add_all(
        [
            WalletDeviceRegistration(
                card_id=old_card.id,
                user_id=1,
                device_library_identifier="dev-1",
                push_token="p-old",
                pass_type_identifier="pass.x",
                serial_number="old",
            ),
            WalletDeviceRegistration(
                card_id=new_card.id,
                user_id=1,
                device_library_identifier="dev-1",
                push_token="p-new",
                pass_type_identifier="pass.x",
                serial_number="new",
            ),
        ]
    )
    session.commit()

    since = str(int(datetime(2026, 3, 1, tzinfo=UTC).timestamp()))
    changed, last_updated = wallet_passkit_service.serials_updated_since(
        session, device_library_identifier="dev-1", pass_type_identifier="pass.x", updated_since=since
    )
    assert changed == ["new"]
    assert int(last_updated) == int(datetime(2026, 6, 1, tzinfo=UTC).timestamp())

    without_tag, _ = wallet_passkit_service.serials_updated_since(
        session, device_library_identifier="dev-1", pass_type_identifier="pass.x", updated_since=None
    )
    assert set(without_tag) == {"old", "new"}

    empty, tag = wallet_passkit_service.serials_updated_since(
        session, device_library_identifier="dev-none", pass_type_identifier="pass.x", updated_since=None
    )
    assert empty == []
    assert tag is None
