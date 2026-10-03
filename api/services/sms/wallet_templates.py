"""Prospecting SMS library of the loyalty-card module (Apple Wallet), written frank.

A first-contact pair for prospects reached by SMS first, a follow-up pair for prospects who ignored the
email. Every SMS says who writes (« je fais des outils web pour les commerces », never the platform's
name), what was prepared through one link without scheme (``{lien_carte}``), the monthly price
(``{prix_carte}/mois``), the day the demo goes offline (``{date_expiration}``) and how to answer: the
alphanumeric sender receives no reply, so the SMS names the sender's public phone (``{telephone}``) and
ends with his first name (``{signature}``). « Un mot me suffit, oui ou non » is the single light ask and
the easy way out.

Rules every template keeps:
  - Two GSM-7 segments at most once smsmode appends its opt-out mention (14 characters reserved in
    France, 25 in Switzerland), with a link of up to 47 characters.
  - Written in GSM-7, so the transliteration at send time changes nothing the prospect reads:
    « commerces », never « commerçants ».
  - No opt-out mention written here, never « voici », « cliquez » or « ici », and the iPhone named: the
    card lives in Apple Wallet.
  - A first contact never mentions an email; a follow-up recalls it and never claims to be the last message.

Plain dicts: key, name, category (« first_contact » or « follow_up ») and body.
"""

from __future__ import annotations

_FIRST_CONTACT = "first_contact"
_FOLLOW_UP = "follow_up"

_ASK_WITH_PHONE = "Un mot me suffit, oui ou non, au {telephone}. {signature}"

WALLET_SMS_TEMPLATE_LIBRARY: list[dict[str, str]] = [
    {
        "key": "carte-direct",
        "name": "Carte fidélité - premier contact franc",
        "category": _FIRST_CONTACT,
        "body": (
            "{salutation}, je fais des outils web pour les commerces et j'ai préparé votre carte fidélité iPhone : "
            "{lien_carte} {prix_carte}/mois, 1er mois offert. En ligne jusqu'au {date_expiration}. " + _ASK_WITH_PHONE
        ),
    },
    {
        "key": "carte-sans-appli",
        "name": "Carte fidélité - sans appli",
        "category": _FIRST_CONTACT,
        "body": (
            "{salutation}, je fais des outils web pour les commerces. Votre carte fidélité iPhone, sans appli à "
            "installer : {lien_carte} {prix_carte}/mois. En ligne jusqu'au {date_expiration}. " + _ASK_WITH_PHONE
        ),
    },
    {
        "key": "carte-relance",
        "name": "Carte fidélité - relance franche",
        "category": _FOLLOW_UP,
        "body": (
            "{salutation}, votre carte fidélité iPhone, envoyée par email : {lien_carte} {prix_carte}/mois, 1er "
            "mois offert. Besoin d'y réfléchir ? Elle reste en ligne jusqu'au {date_expiration}. " + _ASK_WITH_PHONE
        ),
    },
    {
        "key": "carte-rappel-court",
        "name": "Carte fidélité - rappel court",
        "category": _FOLLOW_UP,
        "body": (
            "{salutation}, la carte fidélité iPhone envoyée par email est toujours en ligne : {lien_carte} "
            "{prix_carte}/mois sans engagement. Je la retire le {date_expiration}. " + _ASK_WITH_PHONE
        ),
    },
]
