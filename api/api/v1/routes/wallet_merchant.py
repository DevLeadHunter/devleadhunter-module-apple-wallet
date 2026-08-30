"""Merchant-facing wallet endpoints — authenticated operator actions (scan a card).

Distinct from the public ``wallet`` router (Apple's device + customer enrollment): these
require an app session (``get_current_active_user``) and are scoped to the caller's cards.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from enums.app_module import AppModule
from models.user import User
from services.auth_service import get_current_active_user
from services.module_service import module_service
from services.wallet_automation_service import WalletAutomationError, wallet_automation_service
from services.wallet_scan_service import WalletScanError, wallet_scan_service

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
