"""The loyalty card, as the core's campaign engine sells it.

No page shows a prospect the card prepared for him, so no prospect has a card demo: ``{lien_carte}`` renders empty,
and every email or SMS linking it is held back on every send path with the reason the dashboard shows, « Pas de démo
de carte de fidélité pour ce prospect ». ``{prix_carte}`` is the merchant's monthly price, in the prospect's currency.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from core.product_modules.campaign_offer import CampaignOffer
from services.country_profiles import CountryProfiles

from devleadhunter_apple_wallet.campaigns.sms_templates import LOYALTY_CARD_SMS_TEMPLATES
from devleadhunter_apple_wallet.settings import wallet_settings

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from models.prospect_db import ProspectDB
    from services.sms.templates import SmsTemplate

LOYALTY_CARD_DEMO_MISSING_REASON: str = "Pas de démo de carte de fidélité pour ce prospect"


class LoyaltyCardOffer(CampaignOffer):
    """
    The card offer of the Apple Wallet module: its template variables, its guards and its SMS templates.

    Not sellable (no card demo to link): the core refuses its templates outright.
    """

    CARD_LINK: ClassVar[str] = "lien_carte"
    CARD_PRICE: ClassVar[str] = "prix_carte"

    module_key: ClassVar[str] = "apple-wallet"
    is_sellable: ClassVar[bool] = False
    offer_label: ClassVar[str] = "loyalty-card demo"
    expired_offer_skip_reason: ClassVar[str] = LOYALTY_CARD_DEMO_MISSING_REASON

    email_link_variables: ClassVar[tuple[str, ...]] = (CARD_LINK,)
    email_offer_variables: ClassVar[tuple[str, ...]] = (CARD_LINK, CARD_PRICE)
    sms_link_variables: ClassVar[tuple[str, ...]] = (CARD_LINK,)
    sms_offer_variables: ClassVar[tuple[str, ...]] = (CARD_LINK, CARD_PRICE)
    preview_link_variables: ClassVar[tuple[str, ...]] = (CARD_LINK,)
    email_price_variables: ClassVar[tuple[str, ...]] = (CARD_PRICE,)

    missing_offer_skip_reason: ClassVar[str] = LOYALTY_CARD_DEMO_MISSING_REASON
    missing_offer_launch_summary: ClassVar[str] = "faute de démo de carte de fidélité"

    def has_active_offer(self, db: Session, *, prospect_id: int, user_id: int) -> bool:
        """
        Whether the prospect has a card demo to link: never, no page shows a prospect his card.

        Args:
            db: Active database session.
            prospect_id: The prospect.
            user_id: The sending user.

        Returns:
            False.
        """
        return False

    def email_variables(
        self, db: Session, prospect: ProspectDB, *, user_id: int, include_video: bool, variant: str | None
    ) -> dict[str, str]:
        """
        ``{lien_carte}`` (empty) and ``{prix_carte}`` of a prospect's email.

        Args:
            db: Active database session.
            prospect: The prospect being emailed.
            user_id: The sending user.
            include_video: The campaign's video switch (the card has no video).
            variant: The send's A/B variant (the card has no link to stamp).

        Returns:
            The value of each offer variable.
        """
        return self._variables(prospect)

    def sms_variables(self, db: Session, prospect: ProspectDB, *, user_id: int) -> dict[str, str]:
        """
        ``{lien_carte}`` (empty) and ``{prix_carte}`` of a prospect's SMS.

        Args:
            db: Active database session.
            prospect: The prospect being texted.
            user_id: The sending user.

        Returns:
            The value of each offer variable.
        """
        return self._variables(prospect)

    def email_button_labels(self, variables: dict[str, str]) -> dict[str, str]:
        """
        The wording of the button the dressed layouts draw under the card's link.

        Args:
            variables: The rendered variables of the send.

        Returns:
            The wording by link variable.
        """
        return {self.CARD_LINK: "Voir ma carte"}

    def sms_templates(self) -> list[SmsTemplate]:
        """
        The card's SMS templates, added to the core's library.

        Returns:
            The four ``carte-…`` templates, in display order.
        """
        return list(LOYALTY_CARD_SMS_TEMPLATES)

    @classmethod
    def monthly_price_for(cls, prospect: ProspectDB) -> str:
        """
        The merchant's monthly price as a prospect of his country reads it, without the « ≈ » of a converted price.

        Args:
            prospect: The prospect the price is written for.

        Returns:
            The price (« 19 € », or its conversion in the prospect's currency).
        """
        return CountryProfiles.get(prospect.country).format_price_without_approximation(
            wallet_settings.subscription_price_cents
        )

    def _variables(self, prospect: ProspectDB) -> dict[str, str]:
        return {self.CARD_LINK: "", self.CARD_PRICE: self.monthly_price_for(prospect)}
