"""Operator-facing loyalty program configuration — create, list and edit a merchant's card.

The operator sells the module and configures one program per merchant here (stamps, reward,
brand colors), then hands the merchant a login (see ``/wallet/merchant/.../login-credentials``).
All routes require the operator to have the Apple Wallet module active.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from models.loyalty_program import LoyaltyProgram
from models.user import User
from services.wallet_program_service import WalletProgramError, wallet_program_service

from .wallet_merchant import require_wallet_module

router = APIRouter(prefix="/wallet/programs", tags=["wallet-programs"])

# Maps the API's camelCase update fields onto the model's snake_case columns.
_UPDATE_FIELD_MAP = {
    "organizationName": "organization_name",
    "stampsRequired": "stamps_required",
    "rewardLabel": "reward_label",
    "description": "description",
    "defaultChangeMessage": "default_change_message",
    "logoUrl": "logo_url",
    "backgroundColor": "background_color",
    "foregroundColor": "foreground_color",
    "labelColor": "label_color",
    "status": "status",
}


class WalletProgramCreateBody(BaseModel):
    """Body to create a loyalty program."""

    organizationName: str
    stampsRequired: int = 10
    rewardLabel: str | None = None
    description: str | None = None
    defaultChangeMessage: str | None = None
    logoUrl: str | None = None
    backgroundColor: str | None = None
    foregroundColor: str | None = None
    labelColor: str | None = None


class WalletProgramUpdateBody(BaseModel):
    """Body to edit a loyalty program (only the sent fields change)."""

    organizationName: str | None = None
    stampsRequired: int | None = None
    rewardLabel: str | None = None
    description: str | None = None
    defaultChangeMessage: str | None = None
    logoUrl: str | None = None
    backgroundColor: str | None = None
    foregroundColor: str | None = None
    labelColor: str | None = None
    status: str | None = None


class WalletProgramResponse(BaseModel):
    """A loyalty program's full configuration."""

    id: int
    organizationName: str
    description: str | None
    stampsRequired: int
    rewardLabel: str | None
    defaultChangeMessage: str | None
    logoUrl: str | None
    backgroundColor: str | None
    foregroundColor: str | None
    labelColor: str | None
    status: str
    publicToken: str | None
    createdAt: datetime | None


def _to_response(program: LoyaltyProgram) -> WalletProgramResponse:
    """Serialize a program to its API shape."""
    return WalletProgramResponse(
        id=program.id,
        organizationName=program.organization_name,
        description=program.description,
        stampsRequired=program.stamps_required,
        rewardLabel=program.reward_label,
        defaultChangeMessage=program.default_change_message,
        logoUrl=program.logo_url,
        backgroundColor=program.background_color,
        foregroundColor=program.foreground_color,
        labelColor=program.label_color,
        status=program.status,
        publicToken=program.public_token,
        createdAt=program.created_at,
    )


@router.post("", response_model=WalletProgramResponse)
async def create_program(
    body: WalletProgramCreateBody,
    current_user: User = Depends(require_wallet_module),
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
    return _to_response(program)


@router.get("", response_model=list[WalletProgramResponse])
async def list_programs(
    current_user: User = Depends(require_wallet_module),
    db: Session = Depends(get_db),
) -> list[WalletProgramResponse]:
    """List the operator's loyalty programs, most recent first."""
    return [_to_response(program) for program in wallet_program_service.list_for_user(db, current_user.id)]


@router.get("/{program_id}", response_model=WalletProgramResponse)
async def get_program(
    program_id: int,
    current_user: User = Depends(require_wallet_module),
    db: Session = Depends(get_db),
) -> WalletProgramResponse:
    """Return one of the operator's programs."""
    program = wallet_program_service.get_for_user(db, current_user.id, program_id)
    if program is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Programme introuvable")
    return _to_response(program)


@router.patch("/{program_id}", response_model=WalletProgramResponse)
async def update_program(
    program_id: int,
    body: WalletProgramUpdateBody,
    current_user: User = Depends(require_wallet_module),
    db: Session = Depends(get_db),
) -> WalletProgramResponse:
    """Apply the operator's edits to one of their programs."""
    if wallet_program_service.get_for_user(db, current_user.id, program_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Programme introuvable")

    provided = body.model_dump(exclude_unset=True)
    changes: dict[str, object] = {
        _UPDATE_FIELD_MAP[key]: value for key, value in provided.items() if key in _UPDATE_FIELD_MAP
    }
    # Never clear the required columns by sending an explicit null.
    for required in ("organization_name", "stamps_required"):
        if changes.get(required) is None:
            changes.pop(required, None)

    try:
        program = wallet_program_service.update(db, current_user.id, program_id, changes)
    except WalletProgramError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error
    return _to_response(program)
