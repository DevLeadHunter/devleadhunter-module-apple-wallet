"""Merchant-facing dashboard API — the surface a merchant logs into to manage their card.

Authenticated by a dedicated merchant JWT (``get_current_merchant``), scoped to the
merchant's own program. Distinct from the operator app and from the operator-side
``/wallet/merchant`` actions (scan, broadcast, subscription).
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from models.merchant_account import MerchantAccount
from services.merchant_auth_service import get_current_merchant, merchant_auth_service
from services.merchant_dashboard_service import merchant_dashboard_service
from services.wallet_subscription_service import wallet_subscription_service

router = APIRouter(prefix="/merchant", tags=["merchant"])


class MerchantLoginBody(BaseModel):
    """Merchant login credentials."""

    email: str
    password: str


class MerchantTokenResponse(BaseModel):
    """A merchant access token."""

    access_token: str
    token_type: str = "bearer"


class MerchantProgramResponse(BaseModel):
    """The merchant's program — everything the card preview and config need."""

    organizationName: str
    stampsRequired: int
    rewardLabel: str | None
    defaultChangeMessage: str | None
    logoUrl: str | None
    backgroundColor: str | None
    foregroundColor: str | None
    labelColor: str | None
    publicToken: str | None
    subscriptionStatus: str
    subscriptionActive: bool


class MerchantStatsResponse(BaseModel):
    """Headline counters for the merchant's program."""

    cardsIssued: int
    cardsInstalled: int
    rewardsReady: int
    totalStamps: int


class MerchantCardResponse(BaseModel):
    """One customer's card, as shown in the merchant's list."""

    serialNumber: str
    stamps: int
    status: str
    holderName: str | None
    lastStampedAt: datetime | None
    addedToWalletAt: datetime | None


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
    program = merchant_dashboard_service.get_program(db, merchant.program_id)
    if program is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Programme introuvable")
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
        MerchantCardResponse(
            serialNumber=card.serial_number,
            stamps=card.stamps,
            status=card.status,
            holderName=card.holder_name,
            lastStampedAt=card.last_stamped_at,
            addedToWalletAt=card.added_to_wallet_at,
        )
        for card in merchant_dashboard_service.cards(db, merchant.program_id)
    ]
