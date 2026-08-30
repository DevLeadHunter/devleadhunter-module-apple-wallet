"""Wallet subscription model — a merchant's recurring billing for the Wallet module."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from core.database import Base
from enums.wallet_subscription_status import WalletSubscriptionStatus


class WalletSubscription(Base):
    """A merchant's recurring Apple Wallet subscription, billed via Stripe.

    Recurring auto-debit is Stripe-only (Qonto cannot auto-charge a client), so the
    Wallet subscription always runs on the platform Stripe account, whatever provider
    the operator uses for one-shot website sales. State mirrors the Stripe subscription
    and drives access: only ``trialing``/``active`` grant the module to the merchant.

    Attributes:
        user_id: Operator who sold the subscription (denormalized).
        program_id: The merchant program being subscribed.
        status: Subscription lifecycle (see :class:`WalletSubscriptionStatus`).
        price_cents: Monthly price at checkout time.
        stripe_customer_id / stripe_subscription_id / stripe_checkout_session_id: Stripe refs.
        trial_ends_at: End of the free trial.
        current_period_end: End of the paid period Stripe last billed.
        canceled_at: When it was canceled.
    """

    __tablename__ = "wallet_subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    program_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=WalletSubscriptionStatus.INCOMPLETE.value,
        server_default=WalletSubscriptionStatus.INCOMPLETE.value,
        index=True,
    )
    price_cents: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="eur", server_default="eur")

    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    stripe_checkout_session_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)

    trial_ends_at: Mapped[datetime | None] = mapped_column(nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(nullable=True)
    canceled_at: Mapped[datetime | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(onupdate=func.now(), nullable=True)

    def __repr__(self) -> str:
        """String representation of the subscription."""
        return f"<WalletSubscription id={self.id} program={self.program_id} status={self.status}>"
