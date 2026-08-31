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

# Statuses that cut access (a subscription that lapsed or ended). A program with no
# subscription yet, or still setting one up, keeps a grace access until it lapses.
ACCESS_CUT_STATUSES: frozenset[str] = frozenset(
    {WalletSubscriptionStatus.PAST_DUE.value, WalletSubscriptionStatus.CANCELED.value}
)
