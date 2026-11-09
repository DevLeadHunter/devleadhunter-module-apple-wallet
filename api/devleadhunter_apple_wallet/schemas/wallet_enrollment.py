"""Contracts of the public enrollment page, where a customer adds the merchant's card to Apple Wallet."""

from __future__ import annotations

from pydantic import BaseModel

from devleadhunter_apple_wallet.models.loyalty_program import LoyaltyProgram


class AddCardBody(BaseModel):
    """Optional details a customer provides when adding a card."""

    holderName: str | None = None
    holderEmail: str | None = None
    consent: bool = False


class EnrollProgramResponse(BaseModel):
    """Public branding a customer sees on a program's enrollment landing page."""

    organizationName: str
    stampsRequired: int
    rewardLabel: str | None
    logoUrl: str | None
    backgroundColor: str | None
    foregroundColor: str | None
    labelColor: str | None

    @classmethod
    def from_program(cls, program: LoyaltyProgram) -> EnrollProgramResponse:
        """
        The branding of a program, as the enrollment page shows it.

        Args:
            program: The program the public token points to.

        Returns:
            The response body.
        """
        return cls(
            organizationName=program.organization_name,
            stampsRequired=program.stamps_required,
            rewardLabel=program.reward_label,
            logoUrl=program.logo_url,
            backgroundColor=program.background_color,
            foregroundColor=program.foreground_color,
            labelColor=program.label_color,
        )
