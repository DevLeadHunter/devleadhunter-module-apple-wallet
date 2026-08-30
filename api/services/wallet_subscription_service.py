"""Wallet subscription service — recurring merchant billing via Stripe.

Auto-debit (charge the merchant every month with no manual invoice to chase) is
Stripe-only: Qonto cannot auto-charge a client. So the Wallet subscription always runs
on the platform Stripe account, in ``subscription`` mode with a free trial. State is
synced from Stripe webhooks and gates the merchant's access to the module.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

import stripe
from sqlalchemy.orm import Session

from core.config import settings
from enums.wallet_subscription_status import ACCESS_GRANTED_STATUSES, WalletSubscriptionStatus
from models.loyalty_program import LoyaltyProgram
from models.wallet_subscription import WalletSubscription

logger = logging.getLogger(__name__)

# Map Stripe subscription statuses onto ours; anything unexpected reads as incomplete.
_STRIPE_STATUS_MAP: dict[str, str] = {
    "trialing": WalletSubscriptionStatus.TRIALING.value,
    "active": WalletSubscriptionStatus.ACTIVE.value,
    "past_due": WalletSubscriptionStatus.PAST_DUE.value,
    "unpaid": WalletSubscriptionStatus.PAST_DUE.value,
    "canceled": WalletSubscriptionStatus.CANCELED.value,
    "incomplete": WalletSubscriptionStatus.INCOMPLETE.value,
    "incomplete_expired": WalletSubscriptionStatus.INCOMPLETE.value,
}
_SUBSCRIPTION_METADATA_TYPE = "wallet_subscription"


class WalletSubscriptionError(RuntimeError):
    """Raised when a subscription action cannot proceed (Stripe missing, unknown program)."""


class WalletSubscriptionService:
    """Starts, syncs and cancels the merchant's recurring Wallet subscription."""

    def create_checkout(
        self, db: Session, user_id: int, program_id: int, *, success_url: str, cancel_url: str
    ) -> dict[str, str]:
        """Create a Stripe Checkout Session (subscription mode, free trial) for a program.

        Args:
            db: Database session.
            user_id: Operator who owns the program.
            program_id: Program the merchant subscribes for.
            success_url: Where Stripe returns the merchant on success.
            cancel_url: Where Stripe returns the merchant on cancel.

        Returns:
            ``{"url": ..., "session_id": ...}`` — the hosted checkout to open.

        Raises:
            WalletSubscriptionError: When Stripe is unconfigured or the program is unknown.
        """
        program = (
            db.query(LoyaltyProgram)
            .filter(
                LoyaltyProgram.id == program_id,
                LoyaltyProgram.user_id == user_id,
                LoyaltyProgram.deleted_at.is_(None),
            )
            .first()
        )
        if program is None:
            raise WalletSubscriptionError(f"No loyalty program {program_id} for user {user_id}.")

        client = self._client()
        price_cents = settings.wallet_subscription_price_cents
        metadata = {"program_id": str(program_id), "user_id": str(user_id), "type": _SUBSCRIPTION_METADATA_TYPE}
        try:
            session = client.checkout.Session.create(
                mode="subscription",
                line_items=[
                    {
                        "price_data": {
                            "currency": "eur",
                            "product_data": {"name": f"Carte de fidélité — {program.organization_name}"},
                            "unit_amount": price_cents,
                            "recurring": {"interval": "month"},
                        },
                        "quantity": 1,
                    }
                ],
                subscription_data={
                    "trial_period_days": settings.wallet_subscription_trial_days,
                    "metadata": metadata,
                },
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
            )
        except stripe.error.StripeError as error:
            raise WalletSubscriptionError(f"Stripe error creating checkout: {error!s}") from error

        record = WalletSubscription(
            user_id=user_id,
            program_id=program_id,
            status=WalletSubscriptionStatus.INCOMPLETE.value,
            price_cents=price_cents,
            stripe_checkout_session_id=session.id,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return {"url": session.url, "session_id": session.id}

    def is_active(self, db: Session, program_id: int) -> bool:
        """Whether the program's latest subscription grants access (trialing or active).

        Args:
            db: Database session.
            program_id: Program to check.

        Returns:
            ``True`` when the merchant currently has access.
        """
        record = self._latest_for_program(db, program_id)
        return record is not None and record.status in ACCESS_GRANTED_STATUSES

    def program_status(self, db: Session, program_id: int) -> tuple[str, bool]:
        """Return a program's subscription status label and whether it grants access.

        Args:
            db: Database session.
            program_id: Program to inspect.

        Returns:
            ``(status, active)`` — ``status`` is ``"none"`` when the program has no
            subscription yet.
        """
        record = self._latest_for_program(db, program_id)
        status = record.status if record is not None else "none"
        return status, self.is_active(db, program_id)

    def cancel(self, db: Session, user_id: int, program_id: int) -> WalletSubscription:
        """Cancel a program's subscription immediately (Stripe + local state).

        Args:
            db: Database session.
            user_id: Operator who owns the program.
            program_id: Program whose subscription to cancel.

        Returns:
            The canceled subscription row.

        Raises:
            WalletSubscriptionError: When no subscription matches the operator + program.
        """
        record = self._latest_for_program(db, program_id)
        if record is None or record.user_id != user_id:
            raise WalletSubscriptionError(f"No subscription for program {program_id} and user {user_id}.")
        if record.stripe_subscription_id:
            try:
                self._client().Subscription.delete(record.stripe_subscription_id)
            except stripe.error.StripeError as error:
                raise WalletSubscriptionError(f"Stripe error canceling subscription: {error!s}") from error
        record.status = WalletSubscriptionStatus.CANCELED.value
        record.canceled_at = datetime.now(UTC).replace(tzinfo=None)
        db.commit()
        db.refresh(record)
        return record

    def handle_webhook_event(self, db: Session, event: dict[str, Any]) -> bool:
        """Apply a Stripe webhook event to the local subscription state.

        Args:
            db: Database session.
            event: The verified Stripe event.

        Returns:
            ``True`` when the event belonged to a Wallet subscription and was applied.
        """
        event_type = event.get("type")
        obj = event.get("data", {}).get("object", {})
        if event_type == "checkout.session.completed":
            if obj.get("mode") != "subscription" or obj.get("metadata", {}).get("type") != _SUBSCRIPTION_METADATA_TYPE:
                return False
            return self._link_checkout(db, obj)
        if event_type in (
            "customer.subscription.created",
            "customer.subscription.updated",
            "customer.subscription.deleted",
        ):
            return self._sync_subscription(db, obj)
        return False

    def _link_checkout(self, db: Session, session: dict[str, Any]) -> bool:
        """Attach the Stripe subscription + customer to the local row after checkout."""
        record = (
            db.query(WalletSubscription)
            .filter(WalletSubscription.stripe_checkout_session_id == session.get("id"))
            .first()
        )
        if record is None:
            return False
        record.stripe_subscription_id = session.get("subscription")
        record.stripe_customer_id = session.get("customer")
        if record.status == WalletSubscriptionStatus.INCOMPLETE.value:
            record.status = WalletSubscriptionStatus.TRIALING.value
        db.commit()
        return True

    def _sync_subscription(self, db: Session, subscription: dict[str, Any]) -> bool:
        """Sync status + period fields from a Stripe subscription object."""
        record = self._match_subscription(db, subscription)
        if record is None:
            return False
        record.stripe_subscription_id = subscription.get("id") or record.stripe_subscription_id
        record.status = _STRIPE_STATUS_MAP.get(
            subscription.get("status", ""), WalletSubscriptionStatus.INCOMPLETE.value
        )
        record.current_period_end = self._from_unix(subscription.get("current_period_end"))
        record.trial_ends_at = self._from_unix(subscription.get("trial_end"))
        canceled_at = self._from_unix(subscription.get("canceled_at"))
        if canceled_at is not None:
            record.canceled_at = canceled_at
        db.commit()
        return True

    def _match_subscription(self, db: Session, subscription: dict[str, Any]) -> WalletSubscription | None:
        """Find the local row for a Stripe subscription, by id then program metadata."""
        subscription_id = subscription.get("id")
        record = (
            db.query(WalletSubscription).filter(WalletSubscription.stripe_subscription_id == subscription_id).first()
            if subscription_id
            else None
        )
        if record is not None:
            return record
        program_id = subscription.get("metadata", {}).get("program_id")
        return self._latest_for_program(db, int(program_id)) if program_id else None

    @staticmethod
    def _latest_for_program(db: Session, program_id: int) -> WalletSubscription | None:
        """Return the most recent subscription row for a program."""
        return (
            db.query(WalletSubscription)
            .filter(WalletSubscription.program_id == program_id)
            .order_by(WalletSubscription.id.desc())
            .first()
        )

    @staticmethod
    def _from_unix(timestamp: int | None) -> datetime | None:
        """Convert a Stripe unix timestamp to a naive-UTC datetime."""
        if not timestamp:
            return None
        return datetime.fromtimestamp(timestamp, UTC).replace(tzinfo=None)

    @staticmethod
    def _client() -> Any:
        """Return the Stripe SDK bound to the platform key, failing loudly when absent."""
        if not settings.stripe_secret_key:
            raise WalletSubscriptionError("Stripe is not configured (STRIPE_SECRET_KEY missing).")
        stripe.api_key = settings.stripe_secret_key
        return stripe


wallet_subscription_service = WalletSubscriptionService()
