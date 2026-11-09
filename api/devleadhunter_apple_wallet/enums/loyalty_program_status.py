"""Lifecycle status of a merchant's loyalty program (its Apple Wallet card config)."""

from enum import Enum


class LoyaltyProgramStatus(str, Enum):
    """Lifecycle of a loyalty program."""

    DRAFT = "draft"  # being configured, no cards issued yet
    ACTIVE = "active"  # live: cards can be issued and stamped
    ARCHIVED = "archived"  # retired, kept for history
