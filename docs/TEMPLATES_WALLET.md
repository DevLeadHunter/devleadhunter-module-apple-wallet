# Modèles de prospection : cartes de fidélité (Apple Wallet)

Document de relecture des modèles d'email et de SMS du module 3. Rien ne part et rien n'est semé en base : les modèles vivent dans deux fichiers de données que rien n'importe, et leurs règles sont verrouillées par des tests.

- Emails : `api/seeders/wallet_email_template_library.py` (`WALLET_EMAIL_TEMPLATE_LIBRARY`, même forme de dict que `EMAIL_TEMPLATE_LIBRARY` de main).
- SMS : `api/services/sms/wallet_templates.py` (`WALLET_SMS_TEMPLATE_LIBRARY`, des dicts `key` / `name` / `category` / `body`, les champs de `SmsTemplate` sur main).
- Tests : `api/tests/test_wallet_prospecting_templates.py`.

Main a réécrit ses bibliothèques d'emails et de SMS après la création de la branche du module : des fichiers neufs fusionnent sans conflit. Pour la même raison, `api/services/sms/` n'a pas d'`__init__.py` sur la branche ; celui de main le rejoint à la fusion.

## 1. Ce que fait vraiment le module

Les textes ne promettent que ce qui existe dans le code de la branche `feat/apple-wallet-module`.

| Fonction | Ce que ça fait réellement | Source |
| --- | --- | --- |
| Carte dans Apple Wallet | Un `.pkpass` signé par carte client : nom, logo et couleurs du commerce, nombre de tampons, récompense, offre en cours, QR propre à chaque client. iPhone uniquement. | `api/services/wallet_pass_service.py`, `api/models/loyalty_program.py`, `api/models/loyalty_card.py` |
| Ajout en un scan, sans appli | Page publique `/carte/{token}` : aperçu de la carte, prénom et email facultatifs, case de consentement aux offres, badge officiel « Ajouter à Apple Wallet », mention « Compatible iPhone ». | `web/app/pages/carte/[token].vue`, `api/api/v1/routes/wallet.py` (`GET /wallet/enroll/{token}`, `POST /wallet/add/{token}`), `api/services/wallet_enrollment_service.py` |
| Chevalet QR du comptoir | Affiche imprimable : logo, QR d'ajout, « 10 tampons = … », « Ajout gratuit à Apple Wallet · iPhone ». Elle s'imprime côté opérateur. | `web/app/pages/dashboard/wallet/chevalet/[id].vue`, `web/app/composables/useWalletEnrollLink.ts` |
| Tampons et récompense | Un tampon par action (anti double tampon de 15 s). Au dernier tampon, la carte passe « récompense prête » ; « Remettre » remet le compteur à zéro. | `api/services/wallet_scan_service.py`, `api/api/v1/routes/merchant.py` (`/merchant/cards/{serial}/stamp` et `/redeem`) |
| Mise à jour et écran verrouillé | Push APNs : l'iPhone recharge la carte, et le champ modifié s'affiche en notification sur l'écran verrouillé (`changeMessage`). | `api/services/wallet_push_service.py`, `api/services/wallet_passkit_service.py`, `api/api/v1/routes/wallet.py` (web service PassKit) |
| Automatisations | Diffusion d'une offre à toutes les cartes actives, ou relance après chaque tampon avec un délai (jusqu'à 7 jours dans l'écran). Le commerçant les crée lui-même. L'envoi ne filtre pas sur le consentement coché à l'ajout de la carte. | `api/services/wallet_automation_service.py`, `api/models/loyalty_automation.py`, `web/app/pages/merchant/automations.vue` |
| Espace du commerçant | Connexion dédiée, à son nom : cartes émises, cartes installées, récompenses prêtes, tampons cumulés, liste des clients avec boutons « Tampon » et « Remettre ». La liste n'a ni recherche ni scan du QR de la carte ; un client qui n'a pas donné son prénom y apparaît « Client ». | `api/api/v1/routes/merchant.py`, `api/services/merchant_dashboard_service.py`, `web/app/pages/merchant/index.vue`, `web/app/pages/merchant/login.vue` |
| Abonnement | Stripe en mode abonnement avec essai gratuit ; accès coupé si l'abonnement est impayé ou annulé (plus d'ajout ni de tampon). | `api/services/wallet_subscription_service.py`, `api/enums/wallet_subscription_status.py` |

## 2. Prix, essai, démo, Android

- **Prix** : `WALLET_SUBSCRIPTION_PRICE_CENTS`, 1900 par défaut, soit 19 € par mois (`api/core/config.py`). Il se change par variable d'environnement : un prix unique pour toute la plateforme, figé sur l'abonnement au moment du paiement (`price_cents`). Il n'existe ni prix par opérateur ni prix par commerce, alors que la page `/apple-wallet` dit « Vous fixez le prix » et « prix libre ».
- **Essai** : `WALLET_SUBSCRIPTION_TRIAL_DAYS`, 30 jours par défaut, d'où « le premier mois est offert ». Stripe Checkout demande la carte bancaire dès l'inscription (comportement par défaut, `payment_method_collection` n'est pas réglé). « Premier mois offert » est écrit en dur dans les modèles : si l'essai change, les textes changent avec.
- **Sans engagement** : la résiliation est immédiate (`POST /wallet/merchant/subscription/{program_id}/cancel`). C'est l'opérateur qui la fait : l'espace du commerçant n'a pas de bouton de résiliation.
- **Démo pour le prospect** : aucune. `LoyaltyProgram.prospect_id` existe, mais rien ne le remplit. `/carte/{token}` est la page d'ajout destinée aux clients du commerçant : le prospect peut y voir sa propre carte et l'ajouter à son iPhone, mais la page ne parle ni de prix, ni de date, ni de ce que le commerçant obtient.
- **Date de fin de démo** : aucune. Le programme n'a pas de champ d'expiration. Fermer un programme (`deleted_at`) coupe déjà tout : la page affiche « Carte introuvable », l'ajout et les tampons sont refusés.
- **Android** : pas de Google Wallet, aucun code (la FAQ de `/apple-wallet` le dit « prévu »). Les textes parlent donc d'iPhone partout, et un test le vérifie pour chaque modèle.

## 3. Règles appliquées

Règle n° 1 (« messages francs », décision du 02/10/2026, reprise de `docs/TEMPLATES_FRANCS.md` sur main). Chaque email et chaque SMS dit :

1. qui écrit : « Je fais des outils web pour les commerçants » (emails) ; « je fais des outils web pour les commerces » (SMS, car le « ç » n'existe pas en GSM-7 et deviendrait « commercants ») ; jamais le nom de la plateforme ;
2. ce qui a été préparé, avec un seul lien : `{lien_carte}` ;
3. le prix : `{prix_carte}` par mois (plus « sans engagement » et « le premier mois est offert » dans tous les emails) ;
4. la date de retrait de la démo : `{date_expiration}`, y compris dans les SMS ;
5. comment refuser : « Si c'est non, dites-le-moi et je ne vous recontacte plus », « Un mot me suffit, même un non », ou en SMS « Un mot me suffit, oui ou non, au {telephone} » ;
6. une seule demande, légère.

Retours du 03/10/2026, appliqués partout :

- jamais « Dernier message, promis » : une relance SMS peut suivre ;
- jamais « Même un « non merci » me va » ni rien de peu sûr de soi ; à la place, dans la relance franche : « Besoin d'y réfléchir ? Prenez votre temps : elle reste en ligne jusqu'au {date_expiration}. » ;
- pas de « Je range mes démos », pas d'auto-dévalorisation.

Forme : pas de tiret cadratin ni demi-cadratin, pas d'emoji, jamais « voici », « cliquez » ou « ici » ; sujets courts en minuscules, sans « Apple », « Wallet », « iPhone » ni « Google » (« Apple Wallet » apparaît seulement dans le corps) ; corps d'email terminés nus, la signature est ajoutée à l'envoi ; ton « je », phrases courtes. SMS : 2 segments GSM-7 au plus, mention STOP comprise, un seul lien sans https, numéro de l'expéditeur par `{telephone}` et prénom par `{signature}` ; les corps sont écrits en GSM-7, la translittération de l'envoi ne change donc rien à ce que lit le prospect.

Ce que vérifient les tests (67 cas) : forme des données, préfixes, catégories, mots et signes interdits, formules peu sûres, marque blanche, mention de l'iPhone, un seul lien, prix, date, sortie facile, fin nue, « qui écrit » dans les premiers contacts, rappel de l'email dans les relances SMS, et le budget de 2 segments en France (14 caractères réservés à la mention STOP) comme en Suisse (25), avec un cas courant et un cas lourd.

## 4. Variables

Reprises de main : `{salutation}`, `{entreprise}`, `{date_expiration}` (format « 12 novembre »), et en SMS `{telephone}` et `{signature}`.

Nouvelles, propres au module :

| Variable | Contenu | Rendu |
| --- | --- | --- |
| `{lien_carte}` | La démo de carte du prospect | Email : lien suivi comme `{lien_demo}` (texte = `hôte/chemin`). SMS : forme courte sans https, 47 caractères au plus (le budget testé, comme le lien SMS le plus long de main). |
| `{prix_carte}` | Le prix mensuel | `WALLET_SUBSCRIPTION_PRICE_CENTS` formaté selon le pays du prospect : « 19 € », « ≈ 18 CHF » (« env. 18 CHF » en SMS). Les textes écrivent « {prix_carte} par mois » (email) et « {prix_carte}/mois » (SMS). |

## 5. Les modèles

Valeurs d'exemple : prospect « Boulangerie Martin », salutation « Bonjour M. Martin », prix 19 €, démo retirée le 12 novembre, téléphone public 06 12 34 56 78, prénom d'expéditeur « Marc ». Le lien de démo suit la forme des liens de démo de site : `demo.dibodev.fr/c/boulangerie-martin` en email, `demo.dibodev.fr/s/c/boulangerie-martin` en SMS. Les corps d'email s'affichent sans la signature. Pour les SMS, le compte de caractères inclut les 14 réservés à la mention STOP en France, et le « € » compte double en GSM-7.

### Emails

#### Carte fidélité - premier contact franc

- Catégorie : Premier email (recommandé) ; `sort_order` 22
- Sujet : `la carte de fidélité de Boulangerie Martin`

```
Bonjour M. Martin,

Je fais des outils web pour les commerçants, et j'ai préparé la carte de fidélité de Boulangerie Martin. Vos clients l'ajoutent à Apple Wallet sur leur iPhone, sans appli à installer, et vous la tamponnez à chaque passage. Elle est déjà prête : demo.dibodev.fr/c/boulangerie-martin

C'est 19 € par mois, sans engagement, et le premier mois est offert. Rien à acheter : je vous fournis le QR code à poser sur le comptoir.

Je la garde en ligne jusqu'au 12 novembre. Après, je la retire.

Un mot me suffit : oui, non, ou une question. Si c'est non, dites-le-moi et je ne vous recontacte plus.
```

#### Carte fidélité - vos clients reviennent

- Catégorie : Premier email ; `sort_order` 21
- Sujet : `faire revenir vos clients`

```
Bonjour M. Martin,

Une carte de fidélité en carton, on l'oublie ou on la perd. Une carte dans l'iPhone, vos clients l'ont toujours sur eux. Et quand vous lancez une offre, elle s'affiche sur leur écran verrouillé : de quoi les faire revenir.

Je fais des outils web pour les commerçants, et j'ai préparé celle de Boulangerie Martin. Elle est déjà prête : demo.dibodev.fr/c/boulangerie-martin

C'est 19 € par mois, sans engagement, et le premier mois est offert.

Je la garde en ligne jusqu'au 12 novembre. Après, je la retire.

Un mot me suffit : oui, non, ou une question. Si c'est non, dites-le-moi et je ne vous recontacte plus.
```

#### Carte fidélité - en bref

- Catégorie : Premier email ; `sort_order` 20
- Sujet : `la carte de Boulangerie Martin, en bref`

```
Bonjour M. Martin,

Je fais des outils web pour les commerçants, et j'ai préparé la carte de fidélité de Boulangerie Martin. En bref :

- Dans Apple Wallet, sur l'iPhone de vos clients
- Ajoutée en un scan, avec le QR code du comptoir, sans appli
- Un tampon à chaque passage, depuis votre espace
- La récompense de votre choix au dernier tampon
- Vos offres sur leur écran verrouillé, envoyées à tous ou après un passage

Elle est déjà prête : demo.dibodev.fr/c/boulangerie-martin

C'est 19 € par mois, sans engagement, et le premier mois est offert.

Je la garde en ligne jusqu'au 12 novembre. Après, je la retire.

Un mot me suffit : oui, non, ou une question. Si c'est non, dites-le-moi et je ne vous recontacte plus.
```

La liste est une vraie liste HTML (`<ul>`), rendue avec des puces par les messageries.

#### Carte fidélité - relance franche

- Catégorie : Relance (recommandé) ; `sort_order` 22
- Sujet : `votre carte de fidélité, toujours prête`

```
Bonjour M. Martin,

Je fais des outils web pour les commerçants. Il y a quelques jours, je vous ai envoyé la carte de fidélité que j'ai préparée pour Boulangerie Martin. Vos clients l'ajoutent sur leur iPhone en un scan. Elle est toujours prête : demo.dibodev.fr/c/boulangerie-martin

C'est 19 € par mois, sans engagement, et le premier mois est offert. Je vous fournis aussi le QR code à poser sur le comptoir.

Besoin d'y réfléchir ? Prenez votre temps : elle reste en ligne jusqu'au 12 novembre.

Un mot me suffit, même un non.
```

#### Carte fidélité - rappel court

- Catégorie : Relance ; `sort_order` 21
- Sujet : `vous avez vu votre carte ?`

```
Bonjour M. Martin,

La carte de fidélité iPhone que j'ai préparée pour Boulangerie Martin est toujours prête : demo.dibodev.fr/c/boulangerie-martin

C'est 19 € par mois, sans engagement, premier mois offert. Je la retire le 12 novembre.

Un mot me suffit, même un non.
```

### SMS

#### Carte fidélité - premier contact franc (`carte-direct`)

- Catégorie : Premier contact ; 2 segments, 273 caractères (mention STOP comprise) ; pire cas testé (Suisse, slug de 27 caractères, 30 septembre) : 302 sur 306

```
Bonjour M. Martin, je fais des outils web pour les commerces et j'ai préparé votre carte fidélité iPhone : demo.dibodev.fr/s/c/boulangerie-martin 19 €/mois, 1er mois offert. En ligne jusqu'au 12 novembre. Un mot me suffit, oui ou non, au 06 12 34 56 78. Marc
```

#### Carte fidélité - sans appli (`carte-sans-appli`)

- Catégorie : Premier contact ; 2 segments, 265 caractères (mention STOP comprise) ; pire cas testé : 294 sur 306

```
Bonjour M. Martin, je fais des outils web pour les commerces. Votre carte fidélité iPhone, sans appli à installer : demo.dibodev.fr/s/c/boulangerie-martin 19 €/mois. En ligne jusqu'au 12 novembre. Un mot me suffit, oui ou non, au 06 12 34 56 78. Marc
```

#### Carte fidélité - relance franche (`carte-relance`)

- Catégorie : Relance ; 2 segments, 268 caractères (mention STOP comprise) ; pire cas testé : 297 sur 306

```
Bonjour M. Martin, votre carte fidélité iPhone, envoyée par email : demo.dibodev.fr/s/c/boulangerie-martin 19 €/mois, 1er mois offert. Besoin d'y réfléchir ? Elle reste en ligne jusqu'au 12 novembre. Un mot me suffit, oui ou non, au 06 12 34 56 78. Marc
```

#### Carte fidélité - rappel court (`carte-rappel-court`)

- Catégorie : Relance ; 2 segments, 249 caractères (mention STOP comprise) ; pire cas testé : 278 sur 306

```
Bonjour M. Martin, la carte fidélité iPhone envoyée par email est toujours en ligne : demo.dibodev.fr/s/c/boulangerie-martin 19 €/mois sans engagement. Je la retire le 12 novembre. Un mot me suffit, oui ou non, au 06 12 34 56 78. Marc
```

Les SMS portent en plus la date de retrait, une trentaine de caractères que n'ont pas ceux de main. Pour tenir en 2 segments dans le pire cas, ils disent « carte fidélité » au lieu de « carte de fidélité » et ne gardent qu'une des deux conditions (« 1er mois offert » ou « sans engagement ») ; le SMS « sans appli » donne le prix seul. Au-delà de 2 segments, le service d'envoi de main remplace la salutation par un simple « Bonjour », puis refuse l'envoi si le SMS reste trop long.
