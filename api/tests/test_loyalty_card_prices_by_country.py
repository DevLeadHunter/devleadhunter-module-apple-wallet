"""``{prix_carte}`` is written in the prospect's currency, from his country, and stays the platform's price.

The core's ``test_price_variables_by_country.py`` checks its own prices; these are its checks on ``{prix_carte}``, which
the module brings. The price goes through the core's email and SMS variable builders, the module switched on, as a send
does.
"""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from enums.sms_template_category import SmsTemplateCategory
from models.prospect_db import ProspectDB
from models.user import User
from services.email_variables import EmailVariables
from services.sms.gsm_segments import is_gsm7
from services.sms.templates import SmsTemplate
from services.sms_service import sms_service
from services.sms_variables import SmsVariables

from devleadhunter_apple_wallet.campaigns.loyalty_card_offer import LoyaltyCardOffer
from devleadhunter_apple_wallet.module import AppleWalletModule
from devleadhunter_apple_wallet.settings import wallet_settings

_CARD_PRICE_SMS = SmsTemplate(
    key="prix-carte", name="Prix carte", category=SmsTemplateCategory.FIRST_CONTACT, body="{prix_carte}"
)


def _sender(db: Session, name: str = "Marc Dupont", email: str = "marc@example.com") -> User:
    user = User(name=name, email=email, hashed_password="x")
    db.add(user)
    db.commit()
    return user


def _prospect(db: Session, sender: User, country: str) -> ProspectDB:
    row = ProspectDB(
        user_id=sender.id,
        name="Paysagement Tremblay",
        city="Laval",
        email="info@tremblay.ca",
        phone="514 555-0199",
        category="paysagiste",
        source="google_maps",
        country=country,
    )
    db.add(row)
    db.commit()
    return row


@pytest.mark.parametrize(
    ("country", "card_price"), [("FR", "19 €"), ("CH", "18 CHF"), ("CA", "30 $ CA"), ("BE", "19 €")]
)
def test_the_card_price_follows_the_prospect_country_in_an_email(
    db: Session, apple_wallet_module_switched_on: AppleWalletModule, country: str, card_price: str
) -> None:
    sender = _sender(db)

    variables = EmailVariables.build_for_prospect(db, _prospect(db, sender, country), user_id=sender.id)

    assert variables[LoyaltyCardOffer.CARD_PRICE] == card_price


@pytest.mark.parametrize(("country", "card_price"), [("FR", "19 €"), ("CH", "18 CHF"), ("CA", "30 $ CA")])
def test_the_card_price_reads_firm_in_an_sms_and_stays_in_gsm7(
    db: Session, apple_wallet_module_switched_on: AppleWalletModule, country: str, card_price: str
) -> None:
    """A converted price reads firm in an SMS too, and stays inside GSM-7."""
    sender = _sender(db)
    variables = SmsVariables.build_for_prospect(db, user_id=sender.id, prospect=_prospect(db, sender, country))

    body = sms_service.render_template_body(_CARD_PRICE_SMS, variables)

    assert body == card_price
    assert is_gsm7(body)


def test_the_card_price_is_the_platform_price_whoever_sends(
    db: Session, apple_wallet_module_switched_on: AppleWalletModule, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``{prix_carte}`` reads ``WALLET_SUBSCRIPTION_PRICE_CENTS``: no per-user price to resolve."""
    monkeypatch.setattr(wallet_settings, "subscription_price_cents", 2400)

    for sender in (_sender(db), _sender(db, name="Marie Durand", email="marie@example.com")):
        prospect = _prospect(db, sender, "FR")
        email_variables = EmailVariables.build_for_prospect(db, prospect, user_id=sender.id)
        sms_variables = SmsVariables.build_for_prospect(db, user_id=sender.id, prospect=prospect)

        assert email_variables[LoyaltyCardOffer.CARD_PRICE] == sms_variables[LoyaltyCardOffer.CARD_PRICE] == "24 €"
