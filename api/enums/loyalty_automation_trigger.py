"""What fires a loyalty automation — the card-update-then-push mechanism."""

from enum import Enum


class LoyaltyAutomationTrigger(str, Enum):
    """Event that triggers a card-field update followed by an APNs push."""

    ON_SCAN = "on_scan"  # after a stamp on one card, optionally delayed (targeted)
    BROADCAST = "broadcast"  # applied to every active card of the program
