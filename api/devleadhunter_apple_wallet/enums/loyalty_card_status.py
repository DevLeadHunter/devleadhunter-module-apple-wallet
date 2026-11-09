"""Lifecycle status of a single end-customer loyalty card."""

from enum import Enum


class LoyaltyCardStatus(str, Enum):
    """Lifecycle of a loyalty card held by a merchant's customer."""

    ACTIVE = "active"  # in the customer's Wallet, collecting stamps
    COMPLETED = "completed"  # reward goal reached
    REVOKED = "revoked"  # disabled by the merchant or removed by the customer
