"""Contracts of the merchant's own space: login, program, counters and customer cards."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from devleadhunter_apple_wallet.models.loyalty_card import LoyaltyCard


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

    @staticmethod
    def fields_of(card: LoyaltyCard) -> dict[str, object]:
        """
        The fields of a card shared by the list and the actions' responses.

        Args:
            card: A customer card of the merchant's program.

        Returns:
            The field values by response name.
        """
        return {
            "serialNumber": card.serial_number,
            "stamps": card.stamps,
            "status": card.status,
            "holderName": card.holder_name,
            "lastStampedAt": card.last_stamped_at,
            "addedToWalletAt": card.added_to_wallet_at,
        }


class MerchantCardActionResponse(MerchantCardResponse):
    """A card's refreshed state after a stamp or redeem, plus action feedback."""

    throttled: bool = False
    rewardReady: bool = False
    pushed: bool = False
