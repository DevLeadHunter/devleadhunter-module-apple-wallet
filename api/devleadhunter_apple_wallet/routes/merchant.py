"""Merchant-facing dashboard API — the surface a merchant logs into to manage their card.

Authenticated by a dedicated merchant JWT (``get_current_merchant``), scoped to the
merchant's own program. Distinct from the operator app and from the operator-side
``/wallet/merchant`` actions (scan, broadcast, subscription). The core closes it (404) while
the module is switched off.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from core.database import get_db

from devleadhunter_apple_wallet.models.loyalty_program import LoyaltyProgram
from devleadhunter_apple_wallet.models.merchant_account import MerchantAccount
from devleadhunter_apple_wallet.schemas.merchant import (
    MerchantCardActionResponse,
    MerchantCardResponse,
    MerchantLoginBody,
    MerchantProgramResponse,
    MerchantStatsResponse,
    MerchantTokenResponse,
)
from devleadhunter_apple_wallet.schemas.wallet_automation import (
    AutomationBody,
    AutomationResponse,
    AutomationUpdateBody,
    BroadcastResponse,
)
from devleadhunter_apple_wallet.services.merchant_auth_service import get_current_merchant, merchant_auth_service
from devleadhunter_apple_wallet.services.merchant_dashboard_service import merchant_dashboard_service
from devleadhunter_apple_wallet.services.wallet_automation_service import (
    WalletAutomationError,
    wallet_automation_service,
)
from devleadhunter_apple_wallet.services.wallet_scan_service import WalletScanError, wallet_scan_service
from devleadhunter_apple_wallet.services.wallet_subscription_service import wallet_subscription_service

router = APIRouter(prefix="/merchant", tags=["merchant"])


def _merchant_program(db: Session, merchant: MerchantAccount) -> LoyaltyProgram:
    """Return the merchant's own program (its owner scopes the shared automation service), or raise 404."""
    program = merchant_dashboard_service.get_program(db, merchant.program_id)
    if program is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Programme introuvable")
    return program


@router.post("/login", response_model=MerchantTokenResponse)
async def login(body: MerchantLoginBody, db: Session = Depends(get_db)) -> MerchantTokenResponse:
    """Authenticate a merchant and return their access token."""
    account = merchant_auth_service.authenticate(db, body.email, body.password)
    if account is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")
    return MerchantTokenResponse(access_token=merchant_auth_service.create_token(account))


@router.get("/me", response_model=MerchantProgramResponse)
async def get_my_program(
    merchant: MerchantAccount = Depends(get_current_merchant),
    db: Session = Depends(get_db),
) -> MerchantProgramResponse:
    """Return the merchant's program config and subscription state."""
    program = _merchant_program(db, merchant)
    subscription_status, subscription_active = wallet_subscription_service.program_status(db, program.id)
    return MerchantProgramResponse(
        organizationName=program.organization_name,
        stampsRequired=program.stamps_required,
        rewardLabel=program.reward_label,
        defaultChangeMessage=program.default_change_message,
        logoUrl=program.logo_url,
        backgroundColor=program.background_color,
        foregroundColor=program.foreground_color,
        labelColor=program.label_color,
        publicToken=program.public_token,
        subscriptionStatus=subscription_status,
        subscriptionActive=subscription_active,
    )


@router.get("/summary", response_model=MerchantStatsResponse)
async def get_summary(
    merchant: MerchantAccount = Depends(get_current_merchant),
    db: Session = Depends(get_db),
) -> MerchantStatsResponse:
    """Return the headline counters for the merchant's program."""
    stats = merchant_dashboard_service.stats(db, merchant.program_id)
    return MerchantStatsResponse(
        cardsIssued=stats.cards_issued,
        cardsInstalled=stats.cards_installed,
        rewardsReady=stats.rewards_ready,
        totalStamps=stats.total_stamps,
    )


@router.get("/cards", response_model=list[MerchantCardResponse])
async def get_cards(
    merchant: MerchantAccount = Depends(get_current_merchant),
    db: Session = Depends(get_db),
) -> list[MerchantCardResponse]:
    """Return the merchant's customer cards, most recently stamped first."""
    return [
        MerchantCardResponse(**MerchantCardResponse.fields_of(card))
        for card in merchant_dashboard_service.cards(db, merchant.program_id)
    ]


@router.post("/cards/{serial_number}/stamp", response_model=MerchantCardActionResponse)
async def stamp_card(
    serial_number: str,
    merchant: MerchantAccount = Depends(get_current_merchant),
    db: Session = Depends(get_db),
) -> MerchantCardActionResponse:
    """Add a stamp to one of the merchant's customer cards and return its refreshed state."""
    try:
        result = wallet_scan_service.stamp_for_program(db, merchant.program_id, serial_number)
    except WalletScanError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    return MerchantCardActionResponse(
        **MerchantCardResponse.fields_of(result.card),
        throttled=result.throttled,
        rewardReady=result.reward_ready,
        pushed=result.pushed,
    )


@router.post("/cards/{serial_number}/redeem", response_model=MerchantCardActionResponse)
async def redeem_card(
    serial_number: str,
    merchant: MerchantAccount = Depends(get_current_merchant),
    db: Session = Depends(get_db),
) -> MerchantCardActionResponse:
    """Hand over the reward and reset a completed card, then return its refreshed state."""
    try:
        result = wallet_scan_service.redeem_for_program(db, merchant.program_id, serial_number)
    except WalletScanError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return MerchantCardActionResponse(**MerchantCardResponse.fields_of(result.card), pushed=result.pushed)


@router.get("/automations", response_model=list[AutomationResponse])
async def list_my_automations(
    merchant: MerchantAccount = Depends(get_current_merchant),
    db: Session = Depends(get_db),
) -> list[AutomationResponse]:
    """List the merchant's own automations."""
    return [
        AutomationResponse.from_automation(automation)
        for automation in wallet_automation_service.list_by_program(db, merchant.program_id)
    ]


@router.post("/automations", response_model=AutomationResponse)
async def create_my_automation(
    body: AutomationBody,
    merchant: MerchantAccount = Depends(get_current_merchant),
    db: Session = Depends(get_db),
) -> AutomationResponse:
    """Create an automation for the merchant's own program."""
    program = _merchant_program(db, merchant)
    try:
        automation = wallet_automation_service.create(
            db,
            program.user_id,
            merchant.program_id,
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
async def update_my_automation(
    automation_id: int,
    body: AutomationUpdateBody,
    merchant: MerchantAccount = Depends(get_current_merchant),
    db: Session = Depends(get_db),
) -> AutomationResponse:
    """Edit one of the merchant's own automations."""
    automation = wallet_automation_service.get_for_program(db, merchant.program_id, automation_id)
    if automation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automatisation introuvable")
    try:
        updated = wallet_automation_service.update(db, automation.user_id, automation_id, body.column_changes())
    except WalletAutomationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return AutomationResponse.from_automation(updated)


@router.delete("/automations/{automation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_automation(
    automation_id: int,
    merchant: MerchantAccount = Depends(get_current_merchant),
    db: Session = Depends(get_db),
) -> Response:
    """Delete one of the merchant's own automations."""
    automation = wallet_automation_service.get_for_program(db, merchant.program_id, automation_id)
    if automation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automatisation introuvable")
    wallet_automation_service.delete(db, automation.user_id, automation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/automations/{automation_id}/broadcast", response_model=BroadcastResponse)
async def broadcast_my_automation(
    automation_id: int,
    merchant: MerchantAccount = Depends(get_current_merchant),
    db: Session = Depends(get_db),
) -> BroadcastResponse:
    """Fan one of the merchant's broadcast automations out to every active card."""
    automation = wallet_automation_service.get_for_program(db, merchant.program_id, automation_id)
    if automation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automatisation introuvable")
    try:
        scheduled = wallet_automation_service.trigger_broadcast(db, automation.user_id, automation_id)
    except WalletAutomationError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return BroadcastResponse(scheduled=scheduled)
