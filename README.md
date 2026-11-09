# DevLeadHunter · module Cartes Apple Wallet

Module produit optionnel de DevLeadHunter (clé `apple-wallet`, libellé « Cartes Apple Wallet ») : une carte de fidélité
à tampons que les clients d'un commerçant ajoutent à Apple Wallet en un scan. Le commerçant la tamponne au comptoir,
pousse ses offres sur l'écran verrouillé de ses clients et paie un abonnement mensuel (Stripe, premier mois offert).
L'opérateur crée le programme et remet au commerçant son accès à son propre espace.

## État : installé, désactivé par défaut

- `enabled_by_default = False` : l'interrupteur `apple-wallet` reste à `false` dans `product_modules` tant que le super
  admin ne l'allume pas (Paramètres → Administration → Modules). Coupé, le module ne touche à rien : ses routes
  répondent 404, son worker d'automatisations est arrêté, et le cœur retient tout email ou SMS « Carte fidélité »
  (« Module « Cartes Apple Wallet » désactivé »). Les webhooks Stripe de ses abonnements restent traités.
- Allumé, il ne lie aucune démo de carte (aucune page ne montre sa carte à un prospect) : tout modèle qui contient
  `{lien_carte}` est retenu (« Pas de démo de carte de fidélité pour ce prospect »), et `{prix_carte}` affiche le prix
  de la plateforme dans la devise du prospect (`WALLET_SUBSCRIPTION_PRICE_CENTS`, 1900 centimes, soit « 19 € »).
- Les maquettes et le rappel produit sont dans [`design/wallet/`](design/wallet/README.md).

## Contenu

| Dossier | Rôle |
| --- | --- |
| `api/` | Paquet Python `devleadhunter-apple-wallet` (`devleadhunter_apple_wallet/`) : modèles, enums, services, routes, schémas, migrations, `settings.py`, `module.py` (`AppleWalletModule`), `campaigns/` (offre carte, 5 emails, 4 SMS). |
| `web/` | Layer Nuxt du dashboard (`$meta.name: apple-wallet`) : page `/apple-wallet`, page client `/carte/[token]`, pages opérateur `/dashboard/wallet/**`, espace commerçant `/merchant/**`, textes FR et EN. |
| `design/wallet/` | Maquettes HTML des surfaces client et commerçant. |

## Branchement au cœur

Le contrat est décrit dans `docs/PRODUCT_MODULES.md` du cœur : le cœur n'importe jamais le module, il le découvre.

- **API** : le `pyproject.toml` déclare l'entry point `devleadhunter.product_modules` :
  `apple-wallet = "devleadhunter_apple_wallet.module:AppleWalletModule"`. Le module fournit ses routers, son worker,
  ses migrations (lancées après celles du cœur), son offre de campagne, ses emails et son traitement des événements
  Stripe de ses abonnements (reconnus à la métadonnée `type: wallet_subscription` que pose son checkout). Il importe
  le cœur par ses noms habituels (`from core.database import Base`) et lui-même par `devleadhunter_apple_wallet.…`.
- **Réglages** : `settings.py` lit les variables `WALLET_*` du même `.env` que le cœur : `WALLET_PASS_TYPE_IDENTIFIER`,
  `WALLET_TEAM_ID`, `WALLET_APNS_KEY_ID`, `WALLET_SIGNING_CERTIFICATE`, `WALLET_SIGNING_PRIVATE_KEY`,
  `WALLET_WWDR_CERTIFICATE`, `WALLET_APNS_AUTH_KEY` (les certificats et clés ne servent qu'à amorcer leur copie
  chiffrée en base), `WALLET_SUBSCRIPTION_PRICE_CENTS` (1900) et `WALLET_SUBSCRIPTION_TRIAL_DAYS` (30).
- **Web** : le `web/` du cœur étend ce layer (`productModuleLayers('web')`). Dans le layer, les imports vers le cœur
  restent en `~/…`, ceux entre fichiers du module sont relatifs. Le layer dépend de `qrcode` (QR d'enrôlement) et
  lit `NUXT_PUBLIC_WALLET_ENROLL_BASE` (adresse publique de la page client, `/carte` du site par défaut).

## Développer et tester

Cloner ce dépôt à côté du cœur, puis depuis le dossier `api/` du cœur, dans son venv :

```bash
pip install -e ../../devleadhunter-module-apple-wallet/api
python -m pytest ../../devleadhunter-module-apple-wallet/api/tests -q
python -m ruff check ../../devleadhunter-module-apple-wallet/api
python -m ruff format --check ../../devleadhunter-module-apple-wallet/api
```

Les tests réutilisent les fixtures du cœur (`tests/conftest.py` du cœur, base SQLite en mémoire) : leur dossier n'a
pas de `__init__.py`, pour que `tests` reste le paquet de tests du cœur. Le module y est installé et coupé, comme en
production ; un test qui le veut allumé demande la fixture `apple_wallet_module_switched_on`.
