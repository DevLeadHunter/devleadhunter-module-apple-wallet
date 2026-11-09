"""Contracts of the loyalty automations (offers pushed to the cards), shared by the operator and the merchant."""

from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel, Field

from devleadhunter_apple_wallet.models.loyalty_automation import LoyaltyAutomation


class AutomationBody(BaseModel):
    """Body to create an automation."""

    name: str | None = None
    triggerType: str
    delayMinutes: int = Field(default=0, ge=0)
    fieldValue: str | None = None
    changeMessage: str | None = None


class AutomationUpdateBody(BaseModel):
    """Body to edit an automation (only the sent fields change)."""

    # The model column each API field writes.
    COLUMN_BY_FIELD: ClassVar[dict[str, str]] = {
        "name": "name",
        "triggerType": "trigger_type",
        "delayMinutes": "delay_minutes",
        "fieldValue": "field_value",
        "changeMessage": "change_message",
        "isActive": "is_active",
    }

    name: str | None = None
    triggerType: str | None = None
    delayMinutes: int | None = Field(default=None, ge=0)
    fieldValue: str | None = None
    changeMessage: str | None = None
    isActive: bool | None = None

    def column_changes(self) -> dict[str, object]:
        """
        The columns this edit writes: only the fields the caller sent.

        Returns:
            The new value by column name.
        """
        return {
            self.COLUMN_BY_FIELD[field]: value
            for field, value in self.model_dump(exclude_unset=True).items()
            if field in self.COLUMN_BY_FIELD
        }


class AutomationResponse(BaseModel):
    """An automation's configuration."""

    id: int
    name: str | None
    triggerType: str
    delayMinutes: int
    fieldValue: str | None
    changeMessage: str | None
    isActive: bool

    @classmethod
    def from_automation(cls, automation: LoyaltyAutomation) -> AutomationResponse:
        """
        An automation in its API shape.

        Args:
            automation: The stored automation.

        Returns:
            The response body.
        """
        return cls(
            id=automation.id,
            name=automation.name,
            triggerType=automation.trigger_type,
            delayMinutes=automation.delay_minutes,
            fieldValue=automation.field_value,
            changeMessage=automation.change_message,
            isActive=automation.is_active,
        )


class BroadcastResponse(BaseModel):
    """How many cards a broadcast was scheduled for."""

    scheduled: int
