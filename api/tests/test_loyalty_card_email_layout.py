"""The dressing of a loyalty-card email: its own button, its offer table, and not one word lost.

The core's ``test_email_layout.py`` dresses its own library; these are its checks on the « Carte fidélité - … »
templates, which the module brings. The layout works on the rendered body, so the tests render the templates the way a
send does and check what the prospect receives.
"""

from __future__ import annotations

import re

import pytest

from enums.email_template_layout import EmailTemplateLayout
from services.email_layout import EmailLayout
from services.email_variables import EmailVariables

from devleadhunter_apple_wallet.campaigns.email_templates import LOYALTY_CARD_EMAIL_TEMPLATES
from devleadhunter_apple_wallet.campaigns.loyalty_card_offer import LoyaltyCardOffer

_DEMO_URL = "https://demo.example/menuiserie-lefort?src=email"
_CARD_URL = "https://demo.example/c/menuiserie-lefort?src=email"
_VIDEO_URL = "https://demo.example/v/menuiserie-lefort?src=email"
_SIGNATURE = '<div style="margin-top:16px;"><!--StartFragment--><table><tr><td>Marc Dupont</td></tr></table><br></div>'
_CARD_TABLE = EmailTemplateLayout.CARD_TABLE.value
_CARD = EmailTemplateLayout.CARD.value


def _variables() -> dict[str, str]:
    """The substitution map of a send, with the links and thumbnails in the form ``EmailVariables`` builds."""
    return {
        EmailVariables.SALUTATION: "Bonjour",
        EmailVariables.COMPANY: "Menuiserie Lefort",
        EmailVariables.CITY: "Rennes",
        EmailVariables.TRADE: "menuisier",
        EmailVariables.OLD_WEBSITE: "menuiserie-lefort.example",
        EmailVariables.DEMO_LINK: EmailVariables.build_demo_link_html(_DEMO_URL),
        LoyaltyCardOffer.CARD_LINK: EmailVariables.build_demo_link_html(_CARD_URL),
        EmailVariables.VIDEO_LINK: _VIDEO_URL,
        EmailVariables.VIDEO_THUMBNAIL: EmailVariables.build_video_thumbnail_html(
            _VIDEO_URL, "https://cdn.example/t.jpg"
        ),
        EmailVariables.PRICE: "500 €",
        LoyaltyCardOffer.CARD_PRICE: "19 €",
        EmailVariables.EXPIRY_DATE: "2 novembre",
    }


def _rendered(body_html: str, variables: dict[str, str]) -> str:
    for key, value in variables.items():
        body_html = body_html.replace(f"{{{key}}}", value)
    return body_html


def _library_body(name: str) -> str:
    return next(str(template["body_html"]) for template in LOYALTY_CARD_EMAIL_TEMPLATES if template["name"] == name)


def _dressed(name: str, layout: str = _CARD_TABLE) -> str:
    variables = _variables()
    return EmailLayout.dress(layout, _rendered(_library_body(name), variables), _SIGNATURE, variables, "#6f5fe0")


def _row_labels(html: str) -> list[str]:
    return re.findall(r'class="em-label"[^>]*><div>([^<]+)</div>', html)


def _letters(html: str) -> str:
    """The text of a fragment without its tags nor its spaces: what must survive the dressing, in order."""
    return re.sub(r"\s+", "", re.sub(r"<[^>]+>", "", html))


def test_a_loyalty_card_email_gets_its_own_button() -> None:
    html = _dressed("Carte fidélité - premier contact franc")
    assert ">Voir ma carte</a>" in html
    assert _row_labels(html)[0] == "Prix"


@pytest.mark.parametrize("layout", [_CARD, _CARD_TABLE])
@pytest.mark.parametrize("template", LOYALTY_CARD_EMAIL_TEMPLATES, ids=lambda template: str(template["name"]))
def test_no_card_template_loses_a_word(template: dict[str, object], layout: str) -> None:
    variables = _variables()
    body = _rendered(str(template["body_html"]), variables)
    dressed_letters = _letters(EmailLayout.dress(layout, body, "", variables))
    position = 0
    for paragraph in re.findall(r"<(?:p|li)[^>]*>(.*?)</(?:p|li)>", body, re.DOTALL):
        letters = _letters(paragraph)
        found_at = dressed_letters.find(letters, position)
        assert found_at != -1, paragraph
        position = found_at + len(letters)
