"""Unit tests for the merchant login + dashboard reads."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime

import pytest
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.config import settings
from core.database import Base
from enums.loyalty_card_status import LoyaltyCardStatus
from models.loyalty_card import LoyaltyCard
from models.loyalty_program import LoyaltyProgram
from models.merchant_account import MerchantAccount
from services.merchant_auth_service import merchant_auth_service
from services.merchant_dashboard_service import merchant_dashboard_service


@pytest.fixture
def session() -> Iterator[Session]:
    """A session on an isolated in-memory SQLite with the merchant + program + card tables."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(
        engine,
        tables=[MerchantAccount.__table__, LoyaltyProgram.__table__, LoyaltyCard.__table__],
    )
    db = sessionmaker(bind=engine)()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def _program(db: Session, *, organization_name: str = "Kebab Istanbul") -> LoyaltyProgram:
    """Persist a program."""
    program = LoyaltyProgram(user_id=1, organization_name=organization_name, stamps_required=10)
    db.add(program)
    db.flush()
    return program


def _card(
    db: Session,
    program_id: int,
    *,
    serial: str,
    stamps: int = 0,
    status: str = LoyaltyCardStatus.ACTIVE.value,
    added_to_wallet_at: datetime | None = None,
) -> LoyaltyCard:
    """Persist a card for a program."""
    card = LoyaltyCard(
        program_id=program_id,
        user_id=1,
        serial_number=serial,
        authentication_token="a" * 16,
        stamps=stamps,
        status=status,
        added_to_wallet_at=added_to_wallet_at,
    )
    db.add(card)
    db.flush()
    return card


def test_provision_creates_a_readable_login_then_resets(session: Session) -> None:
    """Provisioning builds a readable email; re-provisioning resets the password in place."""
    account, password = merchant_auth_service.provision(session, 1, organization_name="Kebab Istanbul")
    assert account.email.startswith("kebab-istanbul-")
    assert account.email.endswith("@merchant.dibodev.fr")
    assert password

    account_again, password_again = merchant_auth_service.provision(session, 1, organization_name="Kebab Istanbul")
    assert account_again.id == account.id
    assert password_again != password
    assert session.query(MerchantAccount).count() == 1


def test_authenticate_matches_only_valid_active_credentials(session: Session) -> None:
    """Only the right password on an active account authenticates."""
    account, password = merchant_auth_service.provision(session, 1, organization_name="X")
    assert merchant_auth_service.authenticate(session, account.email, password) is not None
    assert merchant_auth_service.authenticate(session, account.email, "wrong") is None
    assert merchant_auth_service.authenticate(session, "unknown@merchant.dibodev.fr", password) is None
    assert session.query(MerchantAccount).filter_by(id=account.id).one().last_login_at is not None


def test_authenticate_rejects_a_deactivated_account(session: Session) -> None:
    """A deactivated account cannot log in."""
    account, password = merchant_auth_service.provision(session, 1, organization_name="X")
    account.is_active = False
    session.commit()
    assert merchant_auth_service.authenticate(session, account.email, password) is None


def test_token_carries_merchant_claims(session: Session) -> None:
    """The issued token is a merchant token scoped to the program."""
    account, _ = merchant_auth_service.provision(session, 5, organization_name="X")
    token = merchant_auth_service.create_token(account)
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    assert payload["type"] == "merchant"
    assert payload["program_id"] == 5
    assert payload["merchant_id"] == account.id
    assert payload["sub"] == account.email


def test_dashboard_stats_and_cards(session: Session) -> None:
    """Stats count issued/installed/rewards and sum stamps; cards come back for the program."""
    program = _program(session)
    _card(session, program.id, serial="a", stamps=3)
    _card(
        session,
        program.id,
        serial="b",
        stamps=10,
        status=LoyaltyCardStatus.COMPLETED.value,
        added_to_wallet_at=datetime(2026, 1, 1),
    )
    session.commit()

    stats = merchant_dashboard_service.stats(session, program.id)
    assert stats.cards_issued == 2
    assert stats.cards_installed == 1
    assert stats.rewards_ready == 1
    assert stats.total_stamps == 13

    cards = merchant_dashboard_service.cards(session, program.id)
    assert {card.serial_number for card in cards} == {"a", "b"}
