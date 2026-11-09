"""The SMS templates of the loyalty card (``carte-…``), added by the core to its SMS library.

Frank and short like the core's: what was prepared, through ONE link (``{lien_carte}``), the monthly price
(``{prix_carte}``) and how to answer — the alphanumeric sender receives no reply, so every SMS ends on the sender's
first name and public phone. They name the iPhone (the card lives in Apple Wallet) and never leave without the
prospect's card demo. Written in GSM-7: smsmode appends the opt-out mention at send time, never written here.

The campaigns store a template by its key: a key never changes here.
"""

from enums.sms_template_category import SmsTemplateCategory
from services.sms.templates import SmsTemplate

_SIGN_OFF: str = "{signature}, {telephone}"

LOYALTY_CARD_SMS_TEMPLATES: list[SmsTemplate] = [
    SmsTemplate(
        key="carte-direct",
        name="Carte fidélité - premier contact franc",
        category=SmsTemplateCategory.FIRST_CONTACT,
        body=(
            "{salutation}, j'ai créé votre carte fidélité iPhone : {lien_carte} {prix_carte}/mois, 1er mois offert. "
            + _SIGN_OFF
        ),
    ),
    SmsTemplate(
        key="carte-sans-appli",
        name="Carte fidélité - sans appli",
        category=SmsTemplateCategory.FIRST_CONTACT,
        body=(
            "{salutation}, votre carte fidélité iPhone sans appli : {lien_carte} {prix_carte}/mois, essai 1 mois. "
            + _SIGN_OFF
        ),
    ),
    SmsTemplate(
        key="carte-relance",
        name="Carte fidélité - relance franche",
        category=SmsTemplateCategory.FOLLOW_UP,
        body=(
            "{salutation}, la carte fidélité iPhone de mon email : {lien_carte} {prix_carte}/mois, 1er mois offert. "
            + _SIGN_OFF
        ),
        recalls_an_email=True,
    ),
    SmsTemplate(
        key="carte-rappel-court",
        name="Carte fidélité - rappel court",
        category=SmsTemplateCategory.FOLLOW_UP,
        body=(
            "{salutation}, votre carte fidélité iPhone : {lien_carte} {prix_carte}/mois sans engagement. " + _SIGN_OFF
        ),
    ),
]
