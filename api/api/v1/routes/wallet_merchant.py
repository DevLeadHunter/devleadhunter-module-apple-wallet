"""Merchant-facing wallet endpoints — authenticated operator actions (scan a card).

Distinct from the public ``wallet`` router (Apple's device + customer enrollment): these
require an app session (``get_current_active_user``) and are scoped to the caller's cards.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from enums.app_module import AppModule
from models.loyalty_program import LoyaltyProgram
from models.user import User
from services.auth_service import get_current_active_user
from services.merchant_auth_service import merchant_auth_service
from services.module_service import module_service
from services.wallet_automation_service import WalletAutomationError, wallet_automation_service
from services.wallet_scan_service import WalletScanError, wallet_scan_service
from services.wallet_subscription_service import WalletSubscriptionError, wallet_subscription_service

router = APIRouter(prefix="/wallet/merchant", tags=["wallet-merchant"])


def require_wallet_module(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> User:
    """Ensure the caller has the Apple Wallet module active before any merchant action."""
    if not module_service.is_active(db, current_user.id, AppModule.APPLE_WALLET.value):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Module Apple Wallet non activé")
    return current_user


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


class BroadcastResponse(BaseModel):
    """How many cards a broadcast was scheduled for."""

    scheduled: int


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


@router.post("/scan", response_model=ScanResponse)
async def scan_card(
    body: ScanBody,
    current_user: User = Depends(require_wallet_module),
    db: Session = Depends(get_db),
) -> ScanResponse:
    """Add a stamp to the scanned card and return its refreshed state."""
    try:
        result = wallet_scan_service.record_stamp(db, current_user.id, body.serialNumber)
    except WalletScanError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return ScanResponse(
        serialNumber=result.card.serial_number,
        stamps=result.card.stamps,
        stampsRequired=result.required,
        stamped=result.stamped,
        throttled=result.throttled,
        rewardReady=result.reward_ready,
        pushed=result.pushed,
    )


@router.post("/automations/{automation_id}/broadcast", response_model=BroadcastResponse)
async def broadcast_automation(
    automation_id: int,
    current_user: User = Depends(require_wallet_module),
    db: Session = Depends(get_db),
) -> BroadcastResponse:
    """Fan a broadcast automation out to every active card of its program."""
    try:
        scheduled = wallet_automation_service.trigger_broadcast(db, current_user.id, automation_id)
    except WalletAutomationError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return BroadcastResponse(scheduled=scheduled)


@router.post("/subscription/checkout", response_model=SubscriptionCheckoutResponse)
async def start_subscription_checkout(
    body: SubscriptionCheckoutBody,
    current_user: User = Depends(require_wallet_module),
    db: Session = Depends(get_db),
) -> SubscriptionCheckoutResponse:
    """Open a Stripe subscription checkout (free trial, auto-debit) for a program."""
    frontend = settings.frontend_url.rstrip("/")
    success_url = body.successUrl or f"{frontend}/dashboard?wallet_subscription=success"
    cancel_url = body.cancelUrl or f"{frontend}/dashboard?wallet_subscription=canceled"
    try:
        result = wallet_subscription_service.create_checkout(
            db, current_user.id, body.programId, success_url=success_url, cancel_url=cancel_url
        )
    except WalletSubscriptionError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return SubscriptionCheckoutResponse(url=result["url"])


@router.get("/subscription/{program_id}", response_model=SubscriptionStatusResponse)
async def subscription_status(
    program_id: int,
    current_user: User = Depends(require_wallet_module),
    db: Session = Depends(get_db),
) -> SubscriptionStatusResponse:
    """Return a program's subscription status and whether it currently grants access."""
    status_label, active = wallet_subscription_service.program_status(db, program_id)
    return SubscriptionStatusResponse(programId=program_id, status=status_label, active=active)


@router.post("/subscription/{program_id}/cancel", response_model=SubscriptionStatusResponse)
async def cancel_subscription(
    program_id: int,
    current_user: User = Depends(require_wallet_module),
    db: Session = Depends(get_db),
) -> SubscriptionStatusResponse:
    """Cancel a program's subscription immediately."""
    try:
        record = wallet_subscription_service.cancel(db, current_user.id, program_id)
    except WalletSubscriptionError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return SubscriptionStatusResponse(programId=program_id, status=record.status, active=False)


@router.post("/{program_id}/login-credentials", response_model=MerchantCredentialsResponse)
async def provision_merchant_login(
    program_id: int,
    current_user: User = Depends(require_wallet_module),
    db: Session = Depends(get_db),
) -> MerchantCredentialsResponse:
    """Create (or reset) the merchant's login for a program and return it once for handover."""
    program = (
        db.query(LoyaltyProgram)
        .filter(
            LoyaltyProgram.id == program_id,
            LoyaltyProgram.user_id == current_user.id,
            LoyaltyProgram.deleted_at.is_(None),
        )
        .first()
    )
    if program is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Programme introuvable")
    account, password = merchant_auth_service.provision(db, program_id, organization_name=program.organization_name)
    return MerchantCredentialsResponse(email=account.email, password=password)
