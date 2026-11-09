"""The card offer as the core's campaign engine reads it: its variables, its price, its button and its preview."""

from __future__ import annotations

import re

import pytest
from sqlalchemy.orm import Session

from enums.email_template_layout import EmailTemplateLayout
from models.prospect_db import ProspectDB
from services.campaign_offers import CampaignOffers
from services.country_profiles import CountryProfiles
from services.email_layout import EmailLayout
from services.email_variables import EmailVariables

from devleadhunter_apple_wallet.campaigns.email_templates import LOYALTY_CARD_EMAIL_TEMPLATES
from devleadhunter_apple_wallet.campaigns.loyalty_card_offer import LOYALTY_CARD_DEMO_MISSING_REASON, LoyaltyCardOffer
from devleadhunter_apple_wallet.campaigns.sms_templates import LOYALTY_CARD_SMS_TEMPLATES
from devleadhunter_apple_wallet.module import AppleWalletModule

_CARD_URL = "https://demo.example/c/menuiserie-lefort?src=email"


def _prospect(country: str) -> ProspectDB:
    return ProspectDB(user_id=1, name="Menuiserie Lefort", source="google_maps", country=country)


class TestOffer:
    def test_the_core_sees_the_card_offer_of_the_installed_module(
        self, apple_wallet_module_installed: AppleWalletModule
    ) -> None:
        offer = apple_wallet_module_installed.campaign_offer()

        assert CampaignOffers.installed() == [offer]
        assert isinstance(offer, LoyaltyCardOffer)
        assert offer.module_key == AppleWalletModule.key
        assert offer.is_sellable is False
        assert CampaignOffers.email_link_variables() == ("lien_carte",)
        assert CampaignOffers.preview_link_variables() == ("lien_carte",)
        assert CampaignOffers.sms_templates() == LOYALTY_CARD_SMS_TEMPLATES
        assert CampaignOffers.module_label(offer) == "Cartes Apple Wallet"

    def test_no_prospect_has_a_card_demo(self, db: Session) -> None:
        offer = LoyaltyCardOffer()

        assert offer.has_active_offer(db, prospect_id=1, user_id=1) is False
        assert offer.has_ready_video(db, prospect_id=1, user_id=1) is False
        assert offer.offer_lifetime(db, prospect_id=1, user_id=1).has_offer is False
        assert offer.missing_offer_skip_reason == offer.expired_offer_skip_reason == LOYALTY_CARD_DEMO_MISSING_REASON
        assert offer.missing_offer_launch_summary == "faute de démo de carte de fidélité"

    @pytest.mark.parametrize("country", ["FR", "BE", "CH"])
    def test_the_price_is_the_platform_one_in_the_prospect_currency(self, db: Session, country: str) -> None:
        offer = LoyaltyCardOffer()
        expected_price = CountryProfiles.get(country).format_price_without_approximation(1900)

        email_values = offer.email_variables(db, _prospect(country), user_id=1, include_video=True, variant="A")
        sms_values = offer.sms_variables(db, _prospect(country), user_id=1)

        assert email_values == sms_values == {"lien_carte": "", "prix_carte": expected_price}
        assert "≈" not in expected_price
        if country != "CH":
            assert expected_price == "19 €"

    def test_a_switched_off_module_renders_its_variables_empty(
        self, db: Session, apple_wallet_module_installed: AppleWalletModule
    ) -> None:
        assert CampaignOffers.email_variables(db, _prospect("FR"), user_id=1, include_video=False, variant=None) == {
            "lien_carte": "",
            "prix_carte": "",
        }
        assert CampaignOffers.sms_variables(db, _prospect("FR"), user_id=1) == {"lien_carte": "", "prix_carte": ""}


class TestEmailDressing:
    @staticmethod
    def _dressed_first_contact() -> str:
        variables = {
            "salutation": "Bonjour",
            "entreprise": "Menuiserie Lefort",
            "lien_carte": EmailVariables.build_demo_link_html(_CARD_URL),
            "prix_carte": "19 €",
            "date_expiration": "2 novembre",
        }
        body = next(
            str(template["body_html"])
            for template in LOYALTY_CARD_EMAIL_TEMPLATES
            if template["name"] == "Carte fidélité - premier contact franc"
        )
        for key, value in variables.items():
            body = body.replace(f"{{{key}}}", value)
        return EmailLayout.dress(EmailTemplateLayout.CARD_TABLE.value, body, "", variables, "#6f5fe0")

    def test_a_card_email_gets_its_own_button(self, apple_wallet_module_installed: AppleWalletModule) -> None:
        html = self._dressed_first_contact()

        assert ">Voir ma carte</a>" in html
        assert re.findall(r'class="em-label"[^>]*><div>([^<]+)</div>', html)[0] == "Prix"

    def test_the_preview_renders_the_card_link_as_a_link(
        self, apple_wallet_module_installed: AppleWalletModule
    ) -> None:
        preview = EmailVariables.preview_values({"lien_carte": "demo.dibodev.fr/c/menuiserie-lefort"})

        assert preview["lien_carte"].startswith('<a href="')
