"""Operator-facing loyalty program configuration — create, list and edit a merchant's card.

The operator sells the module and configures one program per merchant here (stamps, reward,
brand colors), then hands the merchant a login (see ``/wallet/merchant/.../login-credentials``).
The core closes every route (404) while the module is switched off.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from models.user import User
from services.auth_service import get_current_active_user

from devleadhunter_apple_wallet.schemas.wallet_program import (
    WalletProgramCreateBody,
    WalletProgramResponse,
    WalletProgramUpdateBody,
)
from devleadhunter_apple_wallet.services.wallet_program_service import WalletProgramError, wallet_program_service

router = APIRouter(prefix="/wallet/programs", tags=["wallet-programs"])


@router.post("", response_model=WalletProgramResponse)
async def create_program(
    body: WalletProgramCreateBody,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> WalletProgramResponse:
    """Create a draft program (with a public enrollment token) for the operator."""
    program = wallet_program_service.create(
        db,
        current_user.id,
        organization_name=body.organizationName,
        stamps_required=body.stampsRequired,
        reward_label=body.rewardLabel,
        description=body.description,
        default_change_message=body.defaultChangeMessage,
        logo_url=body.logoUrl,
        background_color=body.backgroundColor,
        foreground_color=body.foregroundColor,
        label_color=body.labelColor,
    )
    return WalletProgramResponse.from_program(program)


@router.get("", response_model=list[WalletProgramResponse])
async def list_programs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[WalletProgramResponse]:
    """List the operator's loyalty programs, most recent first."""
    return [
        WalletProgramResponse.from_program(program)
        for program in wallet_program_service.list_for_user(db, current_user.id)
    ]


@router.get("/{program_id}", response_model=WalletProgramResponse)
async def get_program(
    program_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> WalletProgramResponse:
    """Return one of the operator's programs."""
    program = wallet_program_service.get_for_user(db, current_user.id, program_id)
    if program is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Programme introuvable")
    return WalletProgramResponse.from_program(program)


@router.patch("/{program_id}", response_model=WalletProgramResponse)
async def update_program(
    program_id: int,
    body: WalletProgramUpdateBody,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> WalletProgramResponse:
    """Apply the operator's edits to one of their programs."""
    if wallet_program_service.get_for_user(db, current_user.id, program_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Programme introuvable")
    try:
        program = wallet_program_service.update(db, current_user.id, program_id, body.column_changes())
    except WalletProgramError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return WalletProgramResponse.from_program(program)
