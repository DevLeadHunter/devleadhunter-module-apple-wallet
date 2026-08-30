"""Unit tests for the operator-side loyalty program CRUD."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base
from enums.loyalty_program_status import LoyaltyProgramStatus

# Import the relationship targets so the mappers configure cleanly.
from models import loyalty_automation, loyalty_card, loyalty_program  # noqa: F401
from models.loyalty_program import LoyaltyProgram
from services.wallet_program_service import WalletProgramError, wallet_program_service


@pytest.fixture
def session() -> Iterator[Session]:
    """A session on an isolated in-memory SQLite with just the programs table."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine, tables=[LoyaltyProgram.__table__])
    db = sessionmaker(bind=engine)()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


def test_create_mints_a_draft_with_a_public_token(session: Session) -> None:
    """A new program starts as a draft and gets its public enrollment token."""
    program = wallet_program_service.create(
        session, 1, organization_name="Kebab Istanbul", stamps_required=8, reward_label="1 kebab offert"
    )
    assert program.id is not None
    assert program.user_id == 1
    assert program.status == LoyaltyProgramStatus.DRAFT.value
    assert program.public_token
    assert program.stamps_required == 8
    assert program.reward_label == "1 kebab offert"


def test_list_returns_only_the_operators_live_programs(session: Session) -> None:
    """Listing is scoped to the operator and excludes soft-deleted programs."""
    first = wallet_program_service.create(session, 1, organization_name="A")
    wallet_program_service.create(session, 1, organization_name="B")
    wallet_program_service.create(session, 2, organization_name="Other")

    assert {p.organization_name for p in wallet_program_service.list_for_user(session, 1)} == {"A", "B"}

    first.deleted_at = datetime(2026, 1, 1)
    session.commit()
    assert {p.organization_name for p in wallet_program_service.list_for_user(session, 1)} == {"B"}


def test_get_is_scoped_to_the_operator(session: Session) -> None:
    """A program is only readable by its owner."""
    program = wallet_program_service.create(session, 1, organization_name="A")
    assert wallet_program_service.get_for_user(session, 1, program.id) is not None
    assert wallet_program_service.get_for_user(session, 2, program.id) is None


def test_update_applies_whitelisted_changes(session: Session) -> None:
    """An update writes the config fields and a valid status."""
    program = wallet_program_service.create(session, 1, organization_name="A", stamps_required=10)
    updated = wallet_program_service.update(
        session,
        1,
        program.id,
        {"organization_name": "B", "stamps_required": 6, "reward_label": "x", "status": "active"},
    )
    assert updated.organization_name == "B"
    assert updated.stamps_required == 6
    assert updated.reward_label == "x"
    assert updated.status == LoyaltyProgramStatus.ACTIVE.value


def test_update_rejects_unknown_program_bad_status_and_other_owner(session: Session) -> None:
    """Update fails for a missing program, an invalid status, or another operator."""
    with pytest.raises(WalletProgramError):
        wallet_program_service.update(session, 1, 999, {"organization_name": "X"})

    program = wallet_program_service.create(session, 1, organization_name="A")
    with pytest.raises(WalletProgramError):
        wallet_program_service.update(session, 1, program.id, {"status": "bogus"})
    with pytest.raises(WalletProgramError):
        wallet_program_service.update(session, 2, program.id, {"organization_name": "X"})
