"""Cold-email library of the loyalty-card module (Apple Wallet), written frank.

Every email says who writes (« je fais des outils web pour les commerçants », never the platform's name),
what was prepared through one link (the prospect's own card), the monthly price, the day the demo goes
offline, how to say no, and a single light ask. Rules every template keeps:
  - Subjects: short, lower-case, like a mail between two people, without « Apple », « Wallet », « iPhone »
    or « Google » (Apple bounces mails naming Google in the subject). « Apple Wallet » may appear in the body.
  - Bodies end nude: no sign-off and no ``{signature}``, the signature block is appended at send time.
  - Plain words: no em or en dash, no emoji, never « voici », « cliquez » or « ici ».
  - The card lives in Apple Wallet: every email speaks of the iPhone, none of Android.
  - Assured tone: no « dernier message, promis » (an SMS may follow), no « même un non merci me va », no
    « je range mes démos »; a follow-up gives time instead (« Besoin d'y réfléchir ? Prenez votre temps »).
  - « Premier mois offert » and « sans engagement » hold while the Stripe subscription keeps its free trial
    of ``WALLET_SUBSCRIPTION_TRIAL_DAYS`` (30) and its immediate cancellation.

Variables: {salutation} {entreprise} {date_expiration} {lien_carte} {prix_carte}. ``{lien_carte}`` is the
prospect's card demo, rendered like ``{lien_demo}``; ``{prix_carte}`` is ``WALLET_SUBSCRIPTION_PRICE_CENTS``
as the prospect reads it in his country (« 19 € »), written « {prix_carte} par mois ».

Same dict shape as ``EMAIL_TEMPLATE_LIBRARY`` (name, category, sort_order, subject, body_html); the highest
``sort_order`` of each category pins the module's frank template first.
"""

from __future__ import annotations

from enums.email_template_category import EmailTemplateCategory

_FIRST_EMAIL = EmailTemplateCategory.FIRST_EMAIL.value
_FOLLOW_UP = EmailTemplateCategory.FOLLOW_UP.value

_PRICE_LINE = "<p>C'est {prix_carte} par mois, sans engagement, et le premier mois est offert.</p>"
_EXPIRY_LINE = "<p>Je la garde en ligne jusqu'au {date_expiration}. Après, je la retire.</p>"
_SINGLE_ASK_WITH_EXIT = (
    "<p>Un mot me suffit : oui, non, ou une question. Si c'est non, dites-le-moi et je ne vous recontacte plus.</p>"
)
_TAKE_YOUR_TIME_LINE = (
    "<p>Besoin d'y réfléchir ? Prenez votre temps : elle reste en ligne jusqu'au {date_expiration}.</p>"
)
_SHORT_ASK_WITH_EXIT = "<p>Un mot me suffit, même un non.</p>"

WALLET_EMAIL_TEMPLATE_LIBRARY: list[dict[str, object]] = [
    {
        "name": "Carte fidélité - premier contact franc",
        "category": _FIRST_EMAIL,
        "sort_order": 22,
        "subject": "la carte de fidélité de {entreprise}",
        "body_html": (
            "<p>{salutation},</p>"
            "<p>Je fais des outils web pour les commerçants, et j'ai préparé la carte de fidélité de {entreprise}. "
            "Vos clients l'ajoutent à Apple Wallet sur leur iPhone, sans appli à installer, et vous la tamponnez "
            "à chaque passage. Elle est déjà prête : {lien_carte}</p>"
            "<p>C'est {prix_carte} par mois, sans engagement, et le premier mois est offert. Rien à acheter : je "
            "vous fournis le QR code à poser sur le comptoir.</p>" + _EXPIRY_LINE + _SINGLE_ASK_WITH_EXIT
        ),
    },
    {
        "name": "Carte fidélité - vos clients reviennent",
        "category": _FIRST_EMAIL,
        "sort_order": 21,
        "subject": "faire revenir vos clients",
        "body_html": (
            "<p>{salutation},</p>"
            "<p>Une carte de fidélité en carton, on l'oublie ou on la perd. Une carte dans l'iPhone, vos clients "
            "l'ont toujours sur eux. Et quand vous lancez une offre, elle s'affiche sur leur écran verrouillé : de "
            "quoi les faire revenir.</p>"
            "<p>Je fais des outils web pour les commerçants, et j'ai préparé celle de {entreprise}. Elle est déjà "
            "prête : {lien_carte}</p>" + _PRICE_LINE + _EXPIRY_LINE + _SINGLE_ASK_WITH_EXIT
        ),
    },
    {
        "name": "Carte fidélité - en bref",
        "category": _FIRST_EMAIL,
        "sort_order": 20,
        "subject": "la carte de {entreprise}, en bref",
        "body_html": (
            "<p>{salutation},</p>"
            "<p>Je fais des outils web pour les commerçants, et j'ai préparé la carte de fidélité de {entreprise}. "
            "En bref :</p>"
            "<ul>"
            "<li>dans Apple Wallet, sur l'iPhone de vos clients ;</li>"
            "<li>ajoutée en un scan, avec le QR code du comptoir, sans appli ;</li>"
            "<li>un tampon à chaque passage, depuis votre espace ;</li>"
            "<li>la récompense de votre choix au dernier tampon ;</li>"
            "<li>vos offres sur leur écran verrouillé, envoyées à tous ou après un passage.</li>"
            "</ul>"
            "<p>Elle est déjà prête : {lien_carte}</p>" + _PRICE_LINE + _EXPIRY_LINE + _SINGLE_ASK_WITH_EXIT
        ),
    },
    {
        "name": "Carte fidélité - relance franche",
        "category": _FOLLOW_UP,
        "sort_order": 22,
        "subject": "votre carte de fidélité, toujours prête",
        "body_html": (
            "<p>{salutation},</p>"
            "<p>Je fais des outils web pour les commerçants. Il y a quelques jours, je vous ai envoyé la carte de "
            "fidélité que j'ai préparée pour {entreprise}. Vos clients l'ajoutent sur leur iPhone en un scan. Elle "
            "est toujours prête : {lien_carte}</p>"
            "<p>C'est {prix_carte} par mois, sans engagement, et le premier mois est offert. Je vous fournis aussi "
            "le QR code à poser sur le comptoir.</p>" + _TAKE_YOUR_TIME_LINE + _SHORT_ASK_WITH_EXIT
        ),
    },
    {
        "name": "Carte fidélité - rappel court",
        "category": _FOLLOW_UP,
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
