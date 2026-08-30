"""Lifecycle status of a merchant's Apple Wallet subscription (mirrors Stripe)."""

from enum import Enum


class WalletSubscriptionStatus(str, Enum):
    """Status of a Wallet subscription, aligned with Stripe subscription states."""

    INCOMPLETE = "incomplete"  # checkout created, payment not yet confirmed
    TRIALING = "trialing"  # free trial running
    ACTIVE = "active"  # paying
    PAST_DUE = "past_due"  # a payment failed — access should be cut
    CANCELED = "canceled"  # ended


# Statuses that grant the merchant access to the module.
ACCESS_GRANTED_STATUSES: frozenset[str] = frozenset(
    {WalletSubscriptionStatus.TRIALING.value, WalletSubscriptionStatus.ACTIVE.value}
)
