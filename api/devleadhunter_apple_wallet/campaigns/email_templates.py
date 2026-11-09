"""The cold emails of the loyalty card (« Carte fidélité - … »), appended by the core's seeder to its shared library.

Written frank like the rest of the library: who writes, what was prepared for the prospect (one link, ``{lien_carte}``),
the monthly price (``{prix_carte}``) and its terms, the real withdrawal day (``{date_expiration}``), how to say no and a
single light ask. The card lives in Apple Wallet: the emails speak of the iPhone, never of Android, and their subjects
name neither Apple, Wallet nor iPhone. They never say « DevLeadHunter »: the merchant only knows the person who writes.
Three first emails and two follow-ups; ``sort_order`` pins the frank first contact and the frank follow-up first.

Matched by name by the seeder, which never rewrites a row it finds. The names and texts are the ones the core shipped
(and seeded in prod) before the module left it, kept word for word.
"""

from enums.email_template_category import EmailTemplateCategory

_FIRST: str = EmailTemplateCategory.FIRST_EMAIL.value
_FOLLOW: str = EmailTemplateCategory.FOLLOW_UP.value

# The ask that closes every email of the core's library. Copied, not imported: it is private to the core's seeder, and
# the card's emails must not change when the core rewords its own.
_SINGLE_ASK_WITH_EXIT: str = (
    "<p>Un mot me suffit : oui, non, ou une question. Si c'est non, dites-le-moi et je ne vous recontacte plus.</p>"
)
_SHORT_ASK_WITH_EXIT: str = "<p>Un mot me suffit, même un non.</p>"
_LOYALTY_CARD_PRICE_LINE: str = "<p>C'est {prix_carte} par mois, sans engagement, et le premier mois est offert.</p>"
_LOYALTY_CARD_EXPIRY_LINE: str = "<p>Je la garde en ligne jusqu'au {date_expiration}. Après, je la retire.</p>"
_LOYALTY_CARD_TIME_TO_THINK_LINE: str = (
    "<p>Besoin d'y réfléchir ? Prenez votre temps : elle reste en ligne jusqu'au {date_expiration}.</p>"
)

LOYALTY_CARD_EMAIL_TEMPLATES: list[dict[str, object]] = [
    {
        "name": "Carte fidélité - premier contact franc",
        "category": _FIRST,
        "sort_order": 22,
        "subject": "la carte de fidélité de {entreprise}",
        "body_html": (
            "<p>{salutation},</p>"
            "<p>Je fais des outils web pour les commerçants, et j'ai préparé la carte de fidélité de {entreprise}. "
            "Vos clients l'ajoutent à Apple Wallet sur leur iPhone, sans appli à installer, et vous la tamponnez "
            "à chaque passage. Elle est déjà prête : {lien_carte}</p>"
            "<p>C'est {prix_carte} par mois, sans engagement, et le premier mois est offert. Rien à acheter : vous "
            "imprimez vous-même le QR code ou l'affiche à poser sur le comptoir.</p>"
            + _LOYALTY_CARD_EXPIRY_LINE
            + _SINGLE_ASK_WITH_EXIT
        ),
    },
    {
        "name": "Carte fidélité - vos clients reviennent",
        "category": _FIRST,
        "sort_order": 21,
        "subject": "faire revenir vos clients",
        "body_html": (
            "<p>{salutation},</p>"
            "<p>Une carte de fidélité en carton, on l'oublie ou on la perd. Une carte dans l'iPhone, vos clients "
            "l'ont toujours sur eux. Et quand vous lancez une offre, elle s'affiche sur leur écran verrouillé : de "
            "quoi les faire revenir.</p>"
            "<p>Je fais des outils web pour les commerçants, et j'ai préparé celle de {entreprise}. Elle est déjà "
            "prête : {lien_carte}</p>" + _LOYALTY_CARD_PRICE_LINE + _LOYALTY_CARD_EXPIRY_LINE + _SINGLE_ASK_WITH_EXIT
        ),
    },
    {
        "name": "Carte fidélité - en bref",
        "category": _FIRST,
        "sort_order": 20,
        "subject": "la carte de {entreprise}, en bref",
        "body_html": (
            "<p>{salutation},</p>"
            "<p>Je fais des outils web pour les commerçants, et j'ai préparé la carte de fidélité de {entreprise}. "
            "En bref :</p>"
            "<ul>"
            "<li>Dans Apple Wallet, sur l'iPhone de vos clients</li>"
            "<li>Ajoutée en un scan, avec le QR code du comptoir, sans appli</li>"
            "<li>Un tampon à chaque passage, depuis votre espace</li>"
            "<li>La récompense de votre choix au dernier tampon</li>"
            "<li>Vos offres sur leur écran verrouillé, envoyées à tous ou après un passage</li>"
            "</ul>"
            "<p>Elle est déjà prête : {lien_carte}</p>"
            + _LOYALTY_CARD_PRICE_LINE
            + _LOYALTY_CARD_EXPIRY_LINE
            + _SINGLE_ASK_WITH_EXIT
        ),
    },
    {
        "name": "Carte fidélité - relance franche",
        "category": _FOLLOW,
        "sort_order": 22,
        "subject": "votre carte de fidélité, toujours prête",
        "body_html": (
            "<p>{salutation},</p>"
            "<p>Je fais des outils web pour les commerçants. Il y a quelques jours, je vous ai envoyé la carte de "
            "fidélité que j'ai préparée pour {entreprise}. Vos clients l'ajoutent sur leur iPhone en un scan. Elle "
            "est toujours prête : {lien_carte}</p>"
            "<p>C'est {prix_carte} par mois, sans engagement, et le premier mois est offert. Vous imprimez vous-même "
            "le QR code ou l'affiche à poser sur le comptoir.</p>"
            + _LOYALTY_CARD_TIME_TO_THINK_LINE
            + _SHORT_ASK_WITH_EXIT
        ),
    },
    {
        "name": "Carte fidélité - rappel court",
        "category": _FOLLOW,
        "sort_order": 21,
        "subject": "vous avez vu votre carte ?",
        "body_html": (
            "<p>{salutation},</p>"
            "<p>La carte de fidélité iPhone que j'ai préparée pour {entreprise} est toujours prête : {lien_carte}</p>"
            "<p>C'est {prix_carte} par mois, sans engagement, premier mois offert. Je la retire le "
            "{date_expiration}.</p>" + _SHORT_ASK_WITH_EXIT
        ),
    },
]
