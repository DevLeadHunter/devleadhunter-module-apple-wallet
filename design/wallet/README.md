# Maquettes — Module Cartes de fidélité (Apple Wallet)

Maquettes HTML **autonomes et fidèles** des surfaces du module de cartes de fidélité, calées sur
le design system **« Atelier »** de l'app (tokens `--app-*`, IBM Plex Sans/Mono, DA noir & blanc,
l'ambre réservé aux annotations, le vert/rouge aux statuts). Ce sont des références de design —
le code qui fait foi est dans `web/app/`.

Ouvrir les fichiers directement dans un navigateur (double-clic). Ils sont mobiles-first et
contiennent un petit sélecteur en haut pour basculer entre les écrans.

## Fichiers

| Fichier | Contenu | Écrans (toggle en haut) |
|---|---|---|
| [`customer-enrollment.html`](./customer-enrollment.html) | **Côté client** — comment un client obtient sa carte | `Page client` (landing d'ajout) · `Chevalet comptoir` (affiche imprimable avec QR) |
| [`merchant-surface.html`](./merchant-surface.html) | **Côté commerçant** — l'espace où le commerçant pilote sa carte | `Connexion` (login split-poster) · `Tableau de bord` (KPI + clients + carte) |

## À quoi ça correspond dans le code réel

- **`customer-enrollment.html`**
  - Page client → `web/app/pages/carte/[token].vue` (public, sans login)
  - Chevalet → `web/app/pages/dashboard/wallet/chevalet/[id].vue` (imprimable)
- **`merchant-surface.html`**
  - Login → `web/app/pages/merchant/login.vue`
  - Dashboard → `web/app/pages/merchant/index.vue`
  - Carte → composant `web/app/components/ui/WalletCardPreview.vue`

Config opérateur (créer un programme, provisionner le login commerçant, section « Partager » avec
le QR) : `web/app/pages/dashboard/wallet/index.vue` + `[id].vue`.

## Rappel produit : 2 QR distincts

- **QR d'enrôlement** (sur le chevalet, au comptoir) → ouvre la page client → *installe* la carte. Le même pour tous.
- **QR de la carte** (sur le pass installé, propre à chaque client) → *scanné par le commerçant* pour tamponner.

## Détails de fidélité

- Le **QR des maquettes est décoratif** (faux-QR déterministe, juste pour le rendu). Le vrai QR
  scannable est généré dans l'app via la lib `qrcode`.
- Exemple de commerce fictif : **« Café Mirabeau »** (couleurs café). Aucune vraie enseigne.
- La marque de la surface commerçant est **personnalisée au commerce** (jamais « devleadhunter » côté
  client/commerçant) ; repère neutre « Fidélité · Apple Wallet » seulement avant connexion.

## Badge officiel « Ajouter à Apple Wallet » — en place ✅

La page client (`web/app/pages/carte/[token].vue`) affiche le **badge officiel Apple**.
Le fichier est déjà déposé : **`web/public/add-to-apple-wallet.svg`** (servi à `/add-to-apple-wallet.svg`).

Provenance : extrait de la **pack officiel Apple** (« Add to Apple Wallet Guidelines », 45 locales,
SVG/EPS), locale **FR/RGB** (`FR_Add_to_Apple_Wallet_RGB`). C'est l'artwork Apple d'origine —
**ne jamais le recréer soi-même**, Apple impose l'usage de son asset officiel.

Pour le remplacer (nouvelle version Apple) : re-télécharger le pack depuis
`developer.apple.com/wallet/add-to-apple-wallet-guidelines/`, prendre le SVG du dossier `FR/RGB/`,
et écraser le fichier en gardant **exactement** ce nom. La page a un repli neutre (`@error`) si le
fichier venait à manquer.

## Contexte

Suivi complet du module : ticket Asana « [IA Code] Wallet B3 » + la mémoire projet
`apple-wallet-module-branch-strategy`. Branche d'intégration : `feat/apple-wallet-module`.
