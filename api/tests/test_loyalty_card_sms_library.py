"""The card SMS within the core's SMS library: unique keys, and one billed segment in France.

The core's ``test_sms_templates.py`` loops over its own library; these are its loops over the ``carte-…`` templates,
which the module brings. The two-segment budget in France and Switzerland and the absence of the opt-out mention are
locked in ``test_loyalty_card_templates.py``.
"""

from __future__ import annotations

import pytest

from services.sms.templates import SmsTemplate, list_sms_templates
from services.sms_service import sms_service

from devleadhunter_apple_wallet.campaigns.sms_templates import LOYALTY_CARD_SMS_TEMPLATES

_TYPICAL_VARIABLES: dict[str, str] = {
    "salutation": "Bonjour Geoffrey",
    "entreprise": "Garage Martin Auto",
    "ville": "Poitiers",
    "metier": "garagiste",
    "lien_carte": "demo.dibodev.fr/s/c/garage-martin-auto",
    "prix_carte": "19 €",
    "date_expiration": "12 novembre",
    "telephone": "06 12 34 56 78",
    "signature": "Léo",
}
_LONG_SLUG_VARIABLES: dict[str, str] = {
    **_TYPICAL_VARIABLES,
    "entreprise": "Plomberie Chauffage Dupont",
    "lien_carte": "demo.dibodev.fr/s/c/plomberie-chauffage-dupont",
    "date_expiration": "30 septembre",
}


def test_the_card_keys_are_unique_in_the_library_the_core_lists() -> None:
    keys = [template.key for template in list_sms_templates()]

    assert len(keys) == len(set(keys))
    assert {template.key for template in LOYALTY_CARD_SMS_TEMPLATES} <= set(keys)


@pytest.mark.parametrize("template", LOYALTY_CARD_SMS_TEMPLATES, ids=lambda template: template.key)
def test_every_card_sms_fits_one_segment_in_france_with_its_greeting(template: SmsTemplate) -> None:
    body = sms_service.compose_within_budget(template, _TYPICAL_VARIABLES, country="FR")

    assert sms_service.marketing_segment_count(body, country="FR") == 1, f"{template.key}: {len(body)} chars"
    assert body.startswith(_TYPICAL_VARIABLES["salutation"]), template.key


@pytest.mark.parametrize("template", LOYALTY_CARD_SMS_TEMPLATES, ids=lambda template: template.key)
def test_a_long_business_name_keeps_one_segment_by_dropping_the_first_name(template: SmsTemplate) -> None:
    body = sms_service.compose_within_budget(template, _LONG_SLUG_VARIABLES, country="FR")

    assert sms_service.marketing_segment_count(body, country="FR") == 1, f"{template.key}: {len(body)} chars"
