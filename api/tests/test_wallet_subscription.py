"""Unit tests for the Wallet subscription service — Stripe SDK faked, state synced."""

from __future__ import annotations

from collections.abc import Iterator
from typing import ClassVar

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import services.wallet_subscription_service as wss
from core.database import Base
from enums.wallet_subscription_status import WalletSubscriptionStatus
from models.loyalty_program import LoyaltyProgram
from models.wallet_subscription import WalletSubscription


class _StripeError(Exception):
    """Stand-in for ``stripe.error.StripeError``."""


class _Obj(dict):
    """Dict with attribute access, mimicking a Stripe SDK object."""

    def __getattr__(self, name: str) -> object:
        try:
            return self[name]
        except KeyError as error:
            raise AttributeError(name) from error


class _FakeSession:
    created: ClassVar[list[dict]] = []

    @staticmethod
    def create(**kwargs: object) -> _Obj:
        _FakeSession.created.append(dict(kwargs))
        return _Obj({"id": "cs_test_1", "url": "https://stripe.test/checkout/cs_test_1"})


class _FakeCheckout:
    Session = _FakeSession


class _FakeSubscription:
    deleted: ClassVar[list[str]] = []

    @staticmethod
    def delete(subscription_id: str) -> _Obj:
        _FakeSubscription.deleted.append(subscription_id)
        return _Obj({"id": subscription_id, "status": "canceled"})


class _FakeError:
    StripeError = _StripeError


class _FakeStripe:
    api_key: str | None = None
    checkout = _FakeCheckout
    Subscription = _FakeSubscription
    error = _FakeError


@pytest.fixture
def session() -> Iterator[Session]:
    """A session on an isolated in-memory SQLite with the program + subscription tables."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine, tables=[LoyaltyProgram.__table__, WalletSubscription.__table__])
    db = sessionmaker(bind=engine)()
    try:
        yield db
    finally:
        db.close()
        engine.dispose()


@pytest.fixture
def fake_stripe(monkeypatch: pytest.MonkeyPatch) -> type[_FakeStripe]:
    """Swap the Stripe SDK for the fake and provide a platform key."""
    _FakeSession.created.clear()
    _FakeSubscription.deleted.clear()
    monkeypatch.setattr(wss, "stripe", _FakeStripe)
    monkeypatch.setattr(wss.settings, "stripe_secret_key", "sk_test_x", raising=False)
    return _FakeStripe


def _program(db: Session, *, user_id: int = 1) -> LoyaltyProgram:
    """Persist a program."""
    program = LoyaltyProgram(user_id=user_id, organization_name="Kebab Istanbul", stamps_required=10)
    db.add(program)
    db.flush()
    return program


def _checkout_event(program_id: int) -> dict:
    """A checkout.session.completed event for the fake session."""
    return {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_1",
                "mode": "subscription",
                "metadata": {"type": "wallet_subscription", "program_id": str(program_id)},
                "subscription": "sub_123",
                "customer": "cus_123",
            }
        },
    }


def test_create_checkout_builds_a_subscription_session_with_trial(
    session: Session, fake_stripe: type[_FakeStripe]
) -> None:
    """Checkout is subscription mode, monthly recurring, with the free trial."""
    program = _program(session)
    session.commit()
    result = wss.wallet_subscription_service.create_checkout(session, 1, program.id, success_url="s", cancel_url="c")
    assert result["url"].startswith("https://stripe.test/")
    call = fake_stripe.checkout.Session.created[-1]
    assert call["mode"] == "subscription"
    assert call["subscription_data"]["trial_period_days"] == 30
    assert call["line_items"][0]["price_data"]["recurring"]["interval"] == "month"
    record = session.query(WalletSubscription).one()
    assert record.status == WalletSubscriptionStatus.INCOMPLETE.value
    assert record.stripe_checkout_session_id == "cs_test_1"


def test_webhook_checkout_completed_links_and_starts_trial(session: Session, fake_stripe: type[_FakeStripe]) -> None:
    """Completing checkout attaches the Stripe ids and moves to trialing."""
    program = _program(session)
    wss.wallet_subscription_service.create_checkout(session, 1, program.id, success_url="s", cancel_url="c")
    assert wss.wallet_subscription_service.handle_webhook_event(session, _checkout_event(program.id)) is True
    record = session.query(WalletSubscription).one()
    assert record.stripe_subscription_id == "sub_123"
    assert record.stripe_customer_id == "cus_123"
    assert record.status == WalletSubscriptionStatus.TRIALING.value


def test_webhook_subscription_past_due_cuts_access(session: Session, fake_stripe: type[_FakeStripe]) -> None:
    """A past_due subscription syncs and no longer grants access."""
    program = _program(session)
    wss.wallet_subscription_service.create_checkout(session, 1, program.id, success_url="s", cancel_url="c")
    wss.wallet_subscription_service.handle_webhook_event(session, _checkout_event(program.id))
    event = {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_123",
                "status": "past_due",
                "current_period_end": 1893456000,
                "metadata": {"program_id": str(program.id)},
            }
        },
    }
    assert wss.wallet_subscription_service.handle_webhook_event(session, event) is True
    assert session.query(WalletSubscription).one().status == WalletSubscriptionStatus.PAST_DUE.value
    assert wss.wallet_subscription_service.is_active(session, program.id) is False


def test_is_active_reflects_status(session: Session) -> None:
    """Only trialing/active grant access; no subscription means no access."""
    program = _program(session)
    subscription = WalletSubscription(user_id=1, program_id=program.id, status=WalletSubscriptionStatus.ACTIVE.value)
    session.add(subscription)
    session.commit()
    assert wss.wallet_subscription_service.is_active(session, program.id) is True
    subscription.status = WalletSubscriptionStatus.CANCELED.value
    session.commit()
    assert wss.wallet_subscription_service.is_active(session, program.id) is False
    assert wss.wallet_subscription_service.is_active(session, 999) is False


def test_cancel_deletes_the_stripe_subscription_and_marks_canceled(
    session: Session, fake_stripe: type[_FakeStripe]
) -> None:
    """Cancelling calls Stripe and flips the local row to canceled."""
    program = _program(session)
    subscription = WalletSubscription(
        user_id=1,
        program_id=program.id,
        status=WalletSubscriptionStatus.ACTIVE.value,
        stripe_subscription_id="sub_123",
    )
    session.add(subscription)
    session.commit()
    record = wss.wallet_subscription_service.cancel(session, 1, program.id)
    assert record.status == WalletSubscriptionStatus.CANCELED.value
    assert record.canceled_at is not None
    assert "sub_123" in fake_stripe.Subscription.deleted


def test_create_checkout_unknown_program_raises(session: Session, fake_stripe: type[_FakeStripe]) -> None:
    """An unknown program is refused before any Stripe call."""
    with pytest.raises(wss.WalletSubscriptionError):
        wss.wallet_subscription_service.create_checkout(session, 1, 999, success_url="s", cancel_url="c")


def test_stripe_not_configured_fails_loudly(session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    """Without a Stripe key the service fails loudly rather than silently."""
    monkeypatch.setattr(wss.settings, "stripe_secret_key", "", raising=False)
    program = _program(session)
    session.commit()
    with pytest.raises(wss.WalletSubscriptionError):
        wss.wallet_subscription_service.create_checkout(session, 1, program.id, success_url="s", cancel_url="c")
