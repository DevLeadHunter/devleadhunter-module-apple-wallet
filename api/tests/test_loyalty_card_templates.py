"""Locks the copy rules of the loyalty-card prospecting templates, email and SMS.

The module brings them to the core's libraries: « Carte fidélité - … » through ``email_template_library()``, ``carte-…``
through its campaign offer. Every template is frank (one link, the monthly price, how to answer; the emails also say
who writes, the withdrawal day and how to say no), assured, honest about the device (an iPhone card) and white-label.
Every SMS stays within two GSM-7 segments once smsmode appends its opt-out mention, for a French and a Swiss prospect,
rendered and counted by the core's sending service itself.
"""

from __future__ import annotations

import re

import pytest

from enums.email_template_category import EmailTemplateCategory
from enums.sms_template_category import SmsTemplateCategory
from services.country_profiles import CountryProfiles
from services.sms.gsm_segments import is_gsm7, to_gsm7
from services.sms.templates import SmsTemplate, find_sms_template, list_sms_templates
from services.sms_service import sms_service
from services.sms_variables import SmsVariables

from devleadhunter_apple_wallet.campaigns.email_templates import LOYALTY_CARD_EMAIL_TEMPLATES
from devleadhunter_apple_wallet.campaigns.sms_templates import LOYALTY_CARD_SMS_TEMPLATES
from devleadhunter_apple_wallet.module import AppleWalletModule
from devleadhunter_apple_wallet.settings import wallet_settings

_EMAIL_NAME_PREFIX = "Carte fidélité - "
_SMS_KEY_PREFIX = "carte-"
_LOYALTY_CARD_EMAILS: list[dict[str, object]] = AppleWalletModule().email_template_library()
_LOYALTY_CARD_SMS: list[SmsTemplate] = list(LOYALTY_CARD_SMS_TEMPLATES)

_VARIABLE_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")
_FORBIDDEN_WORDS = re.compile(r"\b(voici|cliquez|ici)\b", re.IGNORECASE)
_LONG_DASHES = ("—", "–")
_SUBJECT_BRANDS = ("google", "apple", "wallet", "iphone", "facebook", "instagram")
_UNSURE_PHRASES = (
    "dernier message",
    "promis",
    "non merci",
    "je range",
    "pas une personne",
    "désolé",
    "je me permets",
)
_OTHER_MODULES_LINK_VARIABLES = (
    "{lien_demo}",
    "{lien_video}",
    "{vignette_video}",
    "{lien_assistant}",
    "{lien_video_assistant}",
    "{vignette_video_assistant}",
)
_ALLOWED_EMAIL_VARIABLES = frozenset(
    {"salutation", "prenom", "nom", "entreprise", "ville", "metier", "lien_carte", "prix_carte", "date_expiration"}
)
_ALLOWED_SMS_VARIABLES = frozenset(
    {
        "salutation",
        "entreprise",
        "ville",
        "metier",
        "lien_carte",
        "prix_carte",
        "date_expiration",
        "telephone",
        "signature",
    }
)
_PROSPECTING_SEGMENT_BUDGET = 2

_TYPICAL_VARIABLES: dict[str, str] = {
    "salutation": "Bonjour Geoffrey",
    "entreprise": "Boulangerie Martin",
    "ville": "Clermont-Ferrand",
    "metier": "boulanger",
    "lien_carte": "demo.dibodev.fr/s/c/boulangerie-martin",
    "prix_carte": "19 €",
    "date_expiration": "12 novembre",
    "telephone": "06 12 34 56 78",
    "signature": "Marc",
}
_LONG_SLUG_VARIABLES: dict[str, str] = {
    **_TYPICAL_VARIABLES,
    "entreprise": "Boulangerie Pâtisserie Roux",
    "lien_carte": "demo.dibodev.fr/s/c/boulangerie-patisserie-roux",
    "date_expiration": "30 septembre",
}


def _as_read_in(country: str, variables: dict[str, str]) -> dict[str, str]:
    """The variables as a prospect of *country* reads them: the price in his currency, the phone dialable from there."""
    return {
        **variables,
        "prix_carte": CountryProfiles.get(country).format_price(wallet_settings.subscription_price_cents),
        "telephone": SmsVariables.phone_for(variables["telephone"], country),
    }


def _variables_used_in(text: str) -> set[str]:
    return set(_VARIABLE_PATTERN.findall(text))


def _first_emails() -> list[dict[str, object]]:
    return [t for t in _LOYALTY_CARD_EMAILS if t["category"] == EmailTemplateCategory.FIRST_EMAIL.value]


def _follow_up_emails() -> list[dict[str, object]]:
    return [t for t in _LOYALTY_CARD_EMAILS if t["category"] == EmailTemplateCategory.FOLLOW_UP.value]


def _sort_order_of(template: dict[str, object]) -> int:
    order = template["sort_order"]
    assert isinstance(order, int), template["name"]
    return order


def _texts_a_prospect_reads() -> list[tuple[str, str]]:
    """Each email's subject and body, and each SMS body, labelled by template."""
    emails = [(str(t["name"]), f"{t['subject']} {t['body_html']}") for t in _LOYALTY_CARD_EMAILS]
    sms = [(f"SMS {t.key}", t.body) for t in _LOYALTY_CARD_SMS]
    return emails + sms


def _template_bodies() -> list[tuple[str, str]]:
    """Each email and SMS body without the subject: where the link, the price and the day must sit."""
    emails = [(str(t["name"]), str(t["body_html"])) for t in _LOYALTY_CARD_EMAILS]
    sms = [(f"SMS {t.key}", t.body) for t in _LOYALTY_CARD_SMS]
    return emails + sms


class TestLibraryShape:
    def test_the_card_templates_are_exactly_the_ones_linking_the_card(self) -> None:
        linking_emails = {str(t["name"]) for t in LOYALTY_CARD_EMAIL_TEMPLATES if "{lien_carte}" in str(t["body_html"])}
        linking_sms = {t.key for t in list_sms_templates() if t.uses("lien_carte")}
        assert linking_emails == {str(t["name"]) for t in _LOYALTY_CARD_EMAILS}
        assert all(str(t["name"]).startswith(_EMAIL_NAME_PREFIX) for t in _LOYALTY_CARD_EMAILS)
        assert linking_sms == {t.key for t in _LOYALTY_CARD_SMS}
        assert all(t.key.startswith(_SMS_KEY_PREFIX) for t in _LOYALTY_CARD_SMS)
        assert all(t.name.startswith(_EMAIL_NAME_PREFIX) for t in _LOYALTY_CARD_SMS)

    def test_the_core_finds_the_card_sms_once_the_module_is_installed(self) -> None:
        for template in _LOYALTY_CARD_SMS:
            assert find_sms_template(template.key) == template

    def test_the_module_ships_its_minimum_set(self) -> None:
        assert len(_first_emails()) >= 3
        assert len(_follow_up_emails()) >= 2
        sms_categories = [template.category for template in _LOYALTY_CARD_SMS]
        assert sms_categories.count(SmsTemplateCategory.FIRST_CONTACT) >= 2
        assert sms_categories.count(SmsTemplateCategory.FOLLOW_UP) >= 2

    def test_emails_share_the_email_library_dict_shape(self) -> None:
        known_categories = {category.value for category in EmailTemplateCategory}
        for template in _LOYALTY_CARD_EMAILS:
            assert set(template) == {"name", "category", "sort_order", "subject", "body_html"}, template["name"]
            assert template["category"] in known_categories, template["name"]
            assert _sort_order_of(template) > 0, template["name"]

    def test_the_library_hook_hands_over_copies(self) -> None:
        handed_over = AppleWalletModule().email_template_library()
        handed_over[0]["subject"] = "changed by a caller"
        assert LOYALTY_CARD_EMAIL_TEMPLATES[0]["subject"] != "changed by a caller"

    def test_sms_link_no_video_so_they_need_no_fallback(self) -> None:
        for template in _LOYALTY_CARD_SMS:
            assert isinstance(template.category, SmsTemplateCategory), template.key
            assert template.fallback_key is None, template.key

    def test_the_frank_templates_are_pinned_first(self) -> None:
        by_name = {str(template["name"]): template for template in _LOYALTY_CARD_EMAILS}
        first_contact = by_name["Carte fidélité - premier contact franc"]
        frank_follow_up = by_name["Carte fidélité - relance franche"]
        assert _sort_order_of(first_contact) == max(map(_sort_order_of, _first_emails()))
        assert _sort_order_of(frank_follow_up) == max(map(_sort_order_of, _follow_up_emails()))


class TestCopyRules:
    @pytest.mark.parametrize(("name", "text"), _texts_a_prospect_reads())
    def test_plain_assured_words(self, name: str, text: str) -> None:
        assert not any(dash in text for dash in _LONG_DASHES), name
        assert _FORBIDDEN_WORDS.search(text) is None, name
        assert "http" not in text, name
        assert all(ord(char) < 0x2000 or char == "€" for char in text), f"{name}: emoji or typographic sign"
        lowered = text.lower()
        assert not any(phrase in lowered for phrase in _UNSURE_PHRASES), name

    @pytest.mark.parametrize(("name", "text"), _texts_a_prospect_reads())
    def test_white_label_and_honest_about_the_device(self, name: str, text: str) -> None:
        lowered = text.lower()
        assert "devleadhunter" not in lowered, name
        assert "android" not in lowered and "google" not in lowered, name
        assert "iPhone" in text, name

    @pytest.mark.parametrize(("name", "body"), _template_bodies())
    def test_one_link_and_the_monthly_price(self, name: str, body: str) -> None:
        assert body.count("{lien_carte}") == 1, name
        assert not any(link in body for link in _OTHER_MODULES_LINK_VARIABLES), name
        assert "{prix_carte}" in body, name
        assert "{prix}" not in body and "{prix_assistant}" not in body, name

    def test_every_email_gives_the_withdrawal_day(self) -> None:
        for template in _LOYALTY_CARD_EMAILS:
            assert "{date_expiration}" in str(template["body_html"]), template["name"]

    def test_every_variable_is_a_known_one(self) -> None:
        for template in _LOYALTY_CARD_EMAILS:
            used = _variables_used_in(f"{template['subject']} {template['body_html']}")
            assert used <= _ALLOWED_EMAIL_VARIABLES, f"{template['name']}: {used - _ALLOWED_EMAIL_VARIABLES}"
        for template in _LOYALTY_CARD_SMS:
            used = _variables_used_in(template.body)
            assert used <= _ALLOWED_SMS_VARIABLES, f"{template.key}: {used - _ALLOWED_SMS_VARIABLES}"


class TestEmailRules:
    def test_subjects_are_short_lower_case_and_brand_free(self) -> None:
        for template in _LOYALTY_CARD_EMAILS:
            subject = str(template["subject"])
            assert subject[0].islower() or subject.startswith("{"), subject
            assert len(subject) <= 60, subject
            assert not any(brand in subject.lower() for brand in _SUBJECT_BRANDS), subject

    def test_bodies_end_nude_on_a_way_out(self) -> None:
        for template in _LOYALTY_CARD_EMAILS:
            body = str(template["body_html"])
            assert "{signature}" not in body, template["name"]
            assert body.endswith("</p>"), template["name"]
            assert "non" in body.rsplit("<p>", 1)[1], template["name"]

    def test_every_email_states_the_monthly_terms(self) -> None:
        for template in _LOYALTY_CARD_EMAILS:
            body = str(template["body_html"])
            assert "{prix_carte} par mois" in body, template["name"]
            assert "sans engagement" in body and "premier mois" in body, template["name"]

    def test_the_first_emails_say_who_writes(self) -> None:
        for template in _first_emails():
            assert "Je fais des outils web pour les commerçants" in str(template["body_html"]), template["name"]

    def test_the_merchant_prints_the_counter_qr_code_himself(self) -> None:
        by_name = {str(template["name"]): str(template["body_html"]) for template in _LOYALTY_CARD_EMAILS}
        assert "vous imprimez vous-même le QR code ou l'affiche" in by_name["Carte fidélité - premier contact franc"]
        assert "Vous imprimez vous-même le QR code ou l'affiche" in by_name["Carte fidélité - relance franche"]
        assert not any("je vous fournis" in body.lower() for body in by_name.values())

    def test_the_frank_follow_up_gives_time_instead_of_pressing(self) -> None:
        by_name = {str(template["name"]): template for template in _LOYALTY_CARD_EMAILS}
        body = str(by_name["Carte fidélité - relance franche"]["body_html"])
        assert "Besoin d'y réfléchir ? Prenez votre temps : elle reste en ligne jusqu'au {date_expiration}." in body


class TestSmsRules:
    @pytest.mark.parametrize("template", _LOYALTY_CARD_SMS, ids=lambda template: template.key)
    def test_written_in_gsm7_so_the_send_changes_nothing(self, template: SmsTemplate) -> None:
        assert to_gsm7(template.body) == template.body
        assert is_gsm7(template.body)

    @pytest.mark.parametrize("template", _LOYALTY_CARD_SMS, ids=lambda template: template.key)
    def test_names_the_number_to_answer_to_and_signs(self, template: SmsTemplate) -> None:
        assert template.uses("telephone")
        assert template.body.endswith("{signature}, {telephone}")
        assert "{prix_carte}/mois" in template.body
        assert "STOP" not in template.body and "36180" not in template.body and "36034" not in template.body

    def test_first_contacts_claim_no_prior_email(self) -> None:
        for template in _LOYALTY_CARD_SMS:
            if template.category is SmsTemplateCategory.FIRST_CONTACT:
                assert "email" not in template.body, template.key

    def test_a_rendered_first_contact_reads_the_full_offer(self) -> None:
        template = find_sms_template("carte-direct")
        assert template is not None
        body = sms_service.compose_from_template(template, _TYPICAL_VARIABLES)
        assert body.count("demo.dibodev.fr/s/c/boulangerie-martin") == 1
        assert "19 €/mois" in body and "iPhone" in body
        assert body.endswith("Marc, 06 12 34 56 78")


class TestSmsTwoSegmentBudget:
    @pytest.mark.parametrize("country", ["FR", "CH"])
    @pytest.mark.parametrize("variables", [_TYPICAL_VARIABLES, _LONG_SLUG_VARIABLES], ids=["typical", "long-slug"])
    @pytest.mark.parametrize("template", _LOYALTY_CARD_SMS, ids=lambda template: template.key)
    def test_every_sms_fits_two_segments_opt_out_mention_included(
        self, template: SmsTemplate, variables: dict[str, str], country: str
    ) -> None:
        body = sms_service.compose_from_template(template, _as_read_in(country, variables))
        assert is_gsm7(body), body
        segments = sms_service.marketing_segment_count(body, country=country)
        assert segments <= _PROSPECTING_SEGMENT_BUDGET, f"{len(body)} characters: {body}"
