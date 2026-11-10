import type { ModuleEmailVariable } from '~/utils/emailVariables'

/** The variables of the API's loyalty card offer: keep both lists in step. */
export const WALLET_EMAIL_VARIABLES: ModuleEmailVariable[] = [
  {
    key: 'lien_carte',
    token: '{lien_carte}',
    label: 'Lien carte de fidélité',
    description: 'Lien vers la démo de carte de fidélité du prospect ; l’email n’est pas envoyé sans démo de carte.',
    example: 'https://demo.dibodev.fr/c/boulangerie-martin',
    placeAfterKey: 'vignette_video',
  },
  {
    key: 'prix_carte',
    token: '{prix_carte}',
    label: 'Prix carte de fidélité',
    description: 'Prix mensuel de la carte de fidélité, dans la monnaie du prospect : « 19 € », « 18 CHF ».',
    example: '19 €',
    placeAfterKey: 'prix',
  },
]
