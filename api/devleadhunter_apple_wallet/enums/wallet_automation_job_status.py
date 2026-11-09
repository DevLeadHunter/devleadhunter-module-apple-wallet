"""Lifecycle status of a deferred wallet automation job."""

from enum import Enum


class WalletAutomationJobStatus(str, Enum):
    """Status of a scheduled automation job (card field update + push)."""

    PENDING = "pending"  # waiting for its scheduled time
    SENT = "sent"  # applied and pushed
    FAILED = "failed"  # execution errored
    CANCELLED = "cancelled"  # card/automation gone or disabled before it fired
