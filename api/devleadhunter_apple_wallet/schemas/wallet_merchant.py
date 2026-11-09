"""Contracts of the operator's actions on a merchant: scan a card, bill the subscription, hand the login over."""

from pydantic import BaseModel


class ScanBody(BaseModel):
    """Body of a merchant scan request."""

    serialNumber: str


class ScanResponse(BaseModel):
    """Card state returned after a scan."""

    serialNumber: str
    stamps: int
    stampsRequired: int
    stamped: bool
    throttled: bool
    rewardReady: bool
    pushed: bool


class SubscriptionCheckoutBody(BaseModel):
    """Body to start a merchant subscription checkout."""

    programId: int
    successUrl: str | None = None
    cancelUrl: str | None = None


class SubscriptionCheckoutResponse(BaseModel):
    """The hosted Stripe checkout URL to open."""

    url: str


class SubscriptionStatusResponse(BaseModel):
    """A program's subscription state."""

    programId: int
    status: str
    active: bool


class MerchantCredentialsResponse(BaseModel):
    """Freshly provisioned merchant login, shown once for handover."""

    email: str
    password: str
