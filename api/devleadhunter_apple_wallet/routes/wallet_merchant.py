"""Merchant-facing wallet endpoints — authenticated operator actions (scan a card).

Distinct from the public ``wallet`` router (Apple's device + customer enrollment): these
require an app session (``get_current_active_user``) and are scoped to the caller's cards.
The core closes them (404) while the module is switched off.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from core.config import settings
from core.database import get_db
from models.user import User
from services.auth_service import get_current_active_user

from devleadhunter_apple_wallet.models.loyalty_program import LoyaltyProgram
from devleadhunter_apple_wallet.schemas.wallet_automation import (
    AutomationBody,
    AutomationResponse,
    AutomationUpdateBody,
    BroadcastResponse,
)
from devleadhunter_apple_wallet.schemas.wallet_merchant import (
    MerchantCredentialsResponse,
    ScanBody,
    ScanResponse,
    SubscriptionCheckoutBody,
    SubscriptionCheckoutResponse,
    SubscriptionStatusResponse,
)
from devleadhunter_apple_wallet.services.merchant_auth_service import merchant_auth_service
from devleadhunter_apple_wallet.services.wallet_automation_service import (
    WalletAutomationError,
    wallet_automation_service,
)
from devleadhunter_apple_wallet.services.wallet_program_service import wallet_program_service
from devleadhunter_apple_wallet.services.wallet_scan_service import WalletScanError, wallet_scan_service
from devleadhunter_apple_wallet.services.wallet_subscription_service import (
    WalletSubscriptionError,
    wallet_subscription_service,
)

router = APIRouter(prefix="/wallet/merchant", tags=["wallet-merchant"])


def _require_program(db: Session, user_id: int, program_id: int) -> LoyaltyProgram:
    """Return the operator's live program or raise 404."""
    program = wallet_program_service.get_for_user(db, user_id, program_id)
    if program is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Programme introuvable")
    return program


@router.post("/scan", response_model=ScanResponse)
async def scan_card(
    body: ScanBody,
    current_user: User = Depends(get_current_active_user),
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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> BroadcastResponse:
    """Fan a broadcast automation out to every active card of its program."""
    try:
        scheduled = wallet_automation_service.trigger_broadcast(db, current_user.id, automation_id)
    except WalletAutomationError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return BroadcastResponse(scheduled=scheduled)


@router.get("/programs/{program_id}/automations", response_model=list[AutomationResponse])
async def list_automations(
    program_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[AutomationResponse]:
    """List a program's automations."""
    _require_program(db, current_user.id, program_id)
    return [
        AutomationResponse.from_automation(automation)
        for automation in wallet_automation_service.list_for_program(db, current_user.id, program_id)
    ]


@router.post("/programs/{program_id}/automations", response_model=AutomationResponse)
async def create_automation(
    program_id: int,
    body: AutomationBody,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AutomationResponse:
    """Create an automation for a program."""
    _require_program(db, current_user.id, program_id)
    try:
        automation = wallet_automation_service.create(
            db,
            current_user.id,
            program_id,
            name=body.name,
            trigger_type=body.triggerType,
            delay_minutes=body.delayMinutes,
            field_value=body.fieldValue,
            change_message=body.changeMessage,
        )
    except WalletAutomationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return AutomationResponse.from_automation(automation)


@router.patch("/automations/{automation_id}", response_model=AutomationResponse)
async def update_automation(
    automation_id: int,
    body: AutomationUpdateBody,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AutomationResponse:
    """Apply the operator's edits to one of their automations."""
    if wallet_automation_service.get_for_user(db, current_user.id, automation_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automatisation introuvable")
    try:
        automation = wallet_automation_service.update(db, current_user.id, automation_id, body.column_changes())
    except WalletAutomationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return AutomationResponse.from_automation(automation)


@router.delete("/automations/{automation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_automation(
    automation_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    """Delete one of the operator's automations."""
    try:
        wallet_automation_service.delete(db, current_user.id, automation_id)
    except WalletAutomationError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/subscription/checkout", response_model=SubscriptionCheckoutResponse)
async def start_subscription_checkout(
    body: SubscriptionCheckoutBody,
    current_user: User = Depends(get_current_active_user),
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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SubscriptionStatusResponse:
    """Return the subscription status of one of the operator's programs and whether it currently grants access."""
    _require_program(db, current_user.id, program_id)
    status_label, active = wallet_subscription_service.program_status(db, program_id)
    return SubscriptionStatusResponse(programId=program_id, status=status_label, active=active)


@router.post("/subscription/{program_id}/cancel", response_model=SubscriptionStatusResponse)
async def cancel_subscription(
    program_id: int,
    current_user: User = Depends(get_current_active_user),
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
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> MerchantCredentialsResponse:
    """Create (or reset) the merchant's login for a program and return it once for handover."""
    program = _require_program(db, current_user.id, program_id)
    account, password = merchant_auth_service.provision(db, program_id, organization_name=program.organization_name)
    return MerchantCredentialsResponse(email=account.email, password=password)
