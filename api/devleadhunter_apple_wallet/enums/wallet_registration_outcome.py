"""Outcome of a PassKit device (un)registration request."""

from enum import Enum


class WalletRegistrationOutcome(str, Enum):
    """Result of registering or unregistering a device for a pass."""

    CREATED = "created"  # newly registered → HTTP 201
    ALREADY_REGISTERED = "already_registered"  # push token refreshed → HTTP 200
    DELETED = "deleted"  # unregistered (idempotent) → HTTP 200
    UNAUTHORIZED = "unauthorized"  # bad/absent pass token or unknown serial → HTTP 401
