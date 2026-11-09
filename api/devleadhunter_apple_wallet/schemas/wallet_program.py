"""Contracts of the operator's loyalty program configuration (one program per merchant)."""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel

from devleadhunter_apple_wallet.models.loyalty_program import LoyaltyProgram


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

    COLUMN_BY_FIELD: ClassVar[dict[str, str]] = {
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
    REQUIRED_COLUMNS: ClassVar[tuple[str, ...]] = ("organization_name", "stamps_required")

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

    def column_changes(self) -> dict[str, object]:
        """
        The columns this edit writes: only the fields the caller sent, a null never clearing a required one.

        Returns:
            The new value by column name.
        """
        changes: dict[str, object] = {
            self.COLUMN_BY_FIELD[field]: value
            for field, value in self.model_dump(exclude_unset=True).items()
            if field in self.COLUMN_BY_FIELD
        }
        for column in self.REQUIRED_COLUMNS:
            if changes.get(column) is None:
                changes.pop(column, None)
        return changes


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

    @classmethod
    def from_program(cls, program: LoyaltyProgram) -> WalletProgramResponse:
        """
        A program in its API shape.

        Args:
            program: The operator's program.

        Returns:
            The response body.
        """
        return cls(
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
