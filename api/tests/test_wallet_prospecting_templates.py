"""Locks the copy rules of the loyalty-card module's prospecting templates, email and SMS.

Every template is frank (who writes, one link, the monthly price, the withdrawal day, how to say no),
assured, honest about the device (an iPhone card) and white-label. Every SMS fits two GSM-7 segments
once smsmode appends its opt-out mention, with French and Swiss values; the helpers below count like the
SMS sender (GSM 03.38 alphabet, the euro sign and the extension table take two characters).
"""

from __future__ import annotations

import re

import pytest

from enums.email_template_category import EmailTemplateCategory
from seeders.wallet_email_template_library import WALLET_EMAIL_TEMPLATE_LIBRARY
from services.sms.wallet_templates import WALLET_SMS_TEMPLATE_LIBRARY

_VARIABLE_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")
_REPEATED_SPACES = re.compile(r" {2,}")
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
_SMS_CATEGORIES = ("first_contact", "follow_up")
_PROSPECTING_SEGMENT_BUDGET = 2

# TODO: import these GSM-7 rules from services.sms.gsm_segments and services.sms.opt_out_mention.
_GSM7_BASIC: frozenset[str] = frozenset(
    "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ ÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
    "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà"
)
_GSM7_EXTENDED: frozenset[str] = frozenset("^{}\\[~]|€")
_TRANSLITERATIONS: dict[str, str] = {
    "â": "a", "ê": "e", "î": "i", "ô": "o", "û": "u",
    "Â": "A", "Ê": "E", "Î": "I", "Ô": "O", "Û": "U",
    "ë": "e", "ï": "i", "Ë": "E", "Ï": "I", "ÿ": "y", "Ÿ": "Y",
    "ç": "c", "á": "a", "í": "i", "ó": "o", "ú": "u", "ã": "a", "õ": "o",
    "Á": "A", "Í": "I", "Ó": "O", "Ú": "U", "Ã": "A", "Õ": "O",
    "œ": "oe", "Œ": "OE",
    "’": "'", "‘": "'", "“": '"', "”": '"', "«": '"', "»": '"',
    "–": "-", "—": "-", "…": "...", "•": "-", "≈": "env.",
    "\u00a0": " ", "\u202f": " ",
}  # fmt: skip
_GSM7_SINGLE_SMS_LENGTH = 160
_GSM7_LONG_SMS_SEGMENT_LENGTH = 153
_UCS2_SINGLE_SMS_LENGTH = 70
_UCS2_LONG_SMS_SEGMENT_LENGTH = 67
_OPT_OUT_RESERVE_BY_COUNTRY: dict[str, int] = {"FR": 14, "CH": 25}

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
_SWISS_PROSPECT_VALUES: dict[str, str] = {"prix_carte": "≈ 18 CHF", "telephone": "+33 6 12 34 56 78"}


def _to_gsm7(text: str) -> str:
    """Replace the characters missing from GSM-7 by their closest equivalent, as the sender does before a send."""
    return "".join(_TRANSLITERATIONS.get(char, char) for char in text)


def _is_gsm7(text: str) -> bool:
    return all(char in _GSM7_BASIC or char in _GSM7_EXTENDED for char in text)


def _segment_count_with_reserve(text: str, reserved_characters: int) -> int:
    """Segments *text* costs once the opt-out mention's *reserved_characters* are appended after it."""
    if not text:
        return 0
    if _is_gsm7(text):
        length = sum(2 if char in _GSM7_EXTENDED else 1 for char in text) + reserved_characters
        single_sms_length, long_sms_segment_length = _GSM7_SINGLE_SMS_LENGTH, _GSM7_LONG_SMS_SEGMENT_LENGTH
    else:
        length = len(text) + reserved_characters
        single_sms_length, long_sms_segment_length = _UCS2_SINGLE_SMS_LENGTH, _UCS2_LONG_SMS_SEGMENT_LENGTH
    if length <= single_sms_length:
        return 1
    return -(-length // long_sms_segment_length)


def _render_sms(body: str, variables: dict[str, str]) -> str:
    """Render an SMS body as it is sent: variables substituted, spaces collapsed, GSM-7 transliterated."""
    rendered = _VARIABLE_PATTERN.sub(lambda match: variables.get(match.group(1), ""), body)
    return _to_gsm7(_REPEATED_SPACES.sub(" ", rendered).strip())


def _variables_used_in(text: str) -> set[str]:
    return set(_VARIABLE_PATTERN.findall(text))


def _first_emails() -> list[dict[str, object]]:
    return [t for t in WALLET_EMAIL_TEMPLATE_LIBRARY if t["category"] == EmailTemplateCategory.FIRST_EMAIL.value]


def _follow_up_emails() -> list[dict[str, object]]:
    return [t for t in WALLET_EMAIL_TEMPLATE_LIBRARY if t["category"] == EmailTemplateCategory.FOLLOW_UP.value]


def _sort_order_of(template: dict[str, object]) -> int:
    order = template["sort_order"]
    assert isinstance(order, int), template["name"]
    return order


def _texts_a_prospect_reads() -> list[tuple[str, str]]:
    """Each email's subject and body, and each SMS body, labelled by template."""
    emails = [(str(t["name"]), f"{t['subject']} {t['body_html']}") for t in WALLET_EMAIL_TEMPLATE_LIBRARY]
    sms = [(f"SMS {t['key']}", t["body"]) for t in WALLET_SMS_TEMPLATE_LIBRARY]
    return emails + sms


def _template_bodies() -> list[tuple[str, str]]:
    """Each email and SMS body without the subject: where the link, the price and the day must sit."""
    emails = [(str(t["name"]), str(t["body_html"])) for t in WALLET_EMAIL_TEMPLATE_LIBRARY]
    sms = [(f"SMS {t['key']}", t["body"]) for t in WALLET_SMS_TEMPLATE_LIBRARY]
    return emails + sms


class TestLibraryShape:
    def test_email_names_are_unique_and_carry_the_module_prefix(self) -> None:
        names = [str(template["name"]) for template in WALLET_EMAIL_TEMPLATE_LIBRARY]
        assert len(names) == len(set(names))
        assert all(name.startswith("Carte fidélité - ") for name in names)

    def test_sms_keys_and_names_are_unique_and_carry_the_module_prefix(self) -> None:
        keys = [template["key"] for template in WALLET_SMS_TEMPLATE_LIBRARY]
        names = [template["name"] for template in WALLET_SMS_TEMPLATE_LIBRARY]
        assert len(keys) == len(set(keys)) and len(names) == len(set(names))
        assert all(key.startswith("carte-") for key in keys)
        assert all(name.startswith("Carte fidélité - ") for name in names)

    def test_the_module_ships_its_minimum_set(self) -> None:
        assert len(_first_emails()) >= 3
        assert len(_follow_up_emails()) >= 2
        sms_categories = [template["category"] for template in WALLET_SMS_TEMPLATE_LIBRARY]
        assert sms_categories.count("first_contact") >= 2
        assert sms_categories.count("follow_up") >= 2

    def test_emails_share_the_email_library_dict_shape(self) -> None:
        known_categories = {category.value for category in EmailTemplateCategory}
        for template in WALLET_EMAIL_TEMPLATE_LIBRARY:
            assert set(template) == {"name", "category", "sort_order", "subject", "body_html"}, template["name"]
            assert template["category"] in known_categories, template["name"]
            assert _sort_order_of(template) > 0, template["name"]

    def test_sms_carry_a_key_a_name_a_category_and_a_body(self) -> None:
        for template in WALLET_SMS_TEMPLATE_LIBRARY:
            assert set(template) == {"key", "name", "category", "body"}, template["key"]
            assert template["category"] in _SMS_CATEGORIES, template["key"]

    def test_the_frank_templates_are_pinned_first(self) -> None:
        by_name = {str(template["name"]): template for template in WALLET_EMAIL_TEMPLATE_LIBRARY}
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
    def test_one_link_the_monthly_price_and_the_withdrawal_day(self, name: str, body: str) -> None:
        assert body.count("{lien_carte}") == 1, name
        assert not any(link in body for link in _OTHER_MODULES_LINK_VARIABLES), name
        assert "{prix_carte}" in body, name
        assert "{prix}" not in body and "{prix_assistant}" not in body, name
        assert "{date_expiration}" in body, name

    def test_every_variable_is_a_known_one(self) -> None:
        for template in WALLET_EMAIL_TEMPLATE_LIBRARY:
            used = _variables_used_in(f"{template['subject']} {template['body_html']}")
            assert used <= _ALLOWED_EMAIL_VARIABLES, f"{template['name']}: {used - _ALLOWED_EMAIL_VARIABLES}"
        for template in WALLET_SMS_TEMPLATE_LIBRARY:
            used = _variables_used_in(template["body"])
            assert used <= _ALLOWED_SMS_VARIABLES, f"{template['key']}: {used - _ALLOWED_SMS_VARIABLES}"


class TestEmailRules:
    def test_subjects_are_short_lower_case_and_brand_free(self) -> None:
        for template in WALLET_EMAIL_TEMPLATE_LIBRARY:
            subject = str(template["subject"])
            assert subject[0].islower() or subject.startswith("{"), subject
            assert len(subject) <= 60, subject
            assert not any(brand in subject.lower() for brand in _SUBJECT_BRANDS), subject

    def test_bodies_end_nude_on_a_way_out(self) -> None:
        for template in WALLET_EMAIL_TEMPLATE_LIBRARY:
            body = str(template["body_html"])
            assert "{signature}" not in body, template["name"]
            assert body.endswith("</p>"), template["name"]
            assert "non" in body.rsplit("<p>", 1)[1], template["name"]

    def test_every_email_states_the_monthly_terms(self) -> None:
        for template in WALLET_EMAIL_TEMPLATE_LIBRARY:
            body = str(template["body_html"])
            assert "{prix_carte} par mois" in body, template["name"]
            assert "sans engagement" in body and "premier mois" in body, template["name"]

    def test_the_first_emails_say_who_writes(self) -> None:
        for template in _first_emails():
            assert "Je fais des outils web pour les commerçants" in str(template["body_html"]), template["name"]

    def test_the_frank_follow_up_gives_time_instead_of_pressing(self) -> None:
        by_name = {str(template["name"]): template for template in WALLET_EMAIL_TEMPLATE_LIBRARY}
        body = str(by_name["Carte fidélité - relance franche"]["body_html"])
        assert "Besoin d'y réfléchir ? Prenez votre temps : elle reste en ligne jusqu'au {date_expiration}." in body


class TestSmsRules:
    @pytest.mark.parametrize("template", WALLET_SMS_TEMPLATE_LIBRARY, ids=lambda template: template["key"])
    def test_written_in_gsm7_so_the_send_changes_nothing(self, template: dict[str, str]) -> None:
        assert _to_gsm7(template["body"]) == template["body"]
        assert _is_gsm7(template["body"])

    @pytest.mark.parametrize("template", WALLET_SMS_TEMPLATE_LIBRARY, ids=lambda template: template["key"])
    def test_names_the_number_to_answer_to_and_signs(self, template: dict[str, str]) -> None:
        body = template["body"]
        assert "{telephone}" in body
        assert body.endswith("{signature}")
        assert "{prix_carte}/mois" in body
        assert "STOP" not in body and "36180" not in body and "36034" not in body

    def test_first_contacts_say_who_writes_and_claim_no_prior_email(self) -> None:
        for template in WALLET_SMS_TEMPLATE_LIBRARY:
            if template["category"] != "first_contact":
                continue
            assert "je fais des outils web pour les commerces" in template["body"], template["key"]
            assert "email" not in template["body"], template["key"]

    def test_follow_ups_recall_the_email(self) -> None:
        for template in WALLET_SMS_TEMPLATE_LIBRARY:
            if template["category"] == "follow_up":
                assert "email" in template["body"], template["key"]

    def test_a_rendered_first_contact_reads_the_full_offer(self) -> None:
        body = _render_sms(WALLET_SMS_TEMPLATE_LIBRARY[0]["body"], _TYPICAL_VARIABLES)
        assert body.count("demo.dibodev.fr/s/c/boulangerie-martin") == 1
        assert "19 €/mois" in body and "12 novembre" in body and "06 12 34 56 78" in body
        assert body.endswith("Marc")


class TestSmsTwoSegmentBudget:
    def test_the_count_reserves_the_opt_out_mention_and_doubles_the_euro_sign(self) -> None:
        assert _segment_count_with_reserve("a" * 160, 0) == 1
        assert _segment_count_with_reserve("a" * 161, 0) == 2
        assert _segment_count_with_reserve("a" * 146, 14) == 1
        assert _segment_count_with_reserve("a" * 147, 14) == 2
        assert _segment_count_with_reserve("€" * 80, 0) == 1
        assert _segment_count_with_reserve("€" * 81, 0) == 2
        assert _segment_count_with_reserve("a" * 293, 14) == 3
        assert _to_gsm7("≈ 18 CHF") == "env. 18 CHF"

    @pytest.mark.parametrize("country", ["FR", "CH"])
    @pytest.mark.parametrize("variables", [_TYPICAL_VARIABLES, _LONG_SLUG_VARIABLES], ids=["typical", "long-slug"])
    @pytest.mark.parametrize("template", WALLET_SMS_TEMPLATE_LIBRARY, ids=lambda template: template["key"])
    def test_every_sms_fits_two_segments_opt_out_mention_included(
        self, template: dict[str, str], variables: dict[str, str], country: str
    ) -> None:
        values = {**variables, **_SWISS_PROSPECT_VALUES} if country == "CH" else variables
        body = _render_sms(template["body"], values)
        assert _is_gsm7(body), body
        segments = _segment_count_with_reserve(body, _OPT_OUT_RESERVE_BY_COUNTRY[country])
        assert segments <= _PROSPECTING_SEGMENT_BUDGET, f"{len(body)} characters: {body}"
