import type { ProductModuleKey } from '~/types/ProductModule'
import type { DashboardModuleDefinition, UiSidebarGroup } from '~/types/UiSidebar'

export const WALLET_MODULE_KEY: ProductModuleKey = 'apple-wallet'

export const WALLET_SECTION_PATH: string = '/dashboard/wallet'

const WALLET_NAV_GROUPS: UiSidebarGroup[] = [
  {
    heading: 'Pilotage',
    links: [{ to: '/dashboard', label: 'Tableau de bord', icon: 'i-lucide-layout-dashboard' }],
  },
  {
    heading: 'Prospection',
    links: [
      { to: '/dashboard/my-prospects', label: 'Mes prospects', icon: 'i-lucide-users', counterKey: 'pendingLeads' },
      { to: '/dashboard/coverage', label: 'Carte de prospection', icon: 'i-lucide-map' },
      { to: WALLET_SECTION_PATH, label: 'Cartes de fidélité', icon: 'i-lucide-wallet-cards' },
      { to: '/dashboard/campaigns', label: 'Campagnes', icon: 'i-lucide-megaphone' },
      { to: '/dashboard/emails', label: 'Suivi des emails', icon: 'i-lucide-send' },
      { to: '/dashboard/sms', label: 'Suivi des SMS', icon: 'i-lucide-message-square-text' },
    ],
  },
]

export const WALLET_DASHBOARD_MODULE: DashboardModuleDefinition = {
  key: WALLET_MODULE_KEY,
  label: 'Cartes Apple Wallet',
  icon: 'i-lucide-wallet-cards',
  home: WALLET_SECTION_PATH,
  primaryCta: { label: 'Trouver des prospects', to: '/dashboard/search-prospects', icon: 'i-lucide-search' },
  navGroups: WALLET_NAV_GROUPS,
  describeProspectsWithoutOffer: (prospectNames: string[]): string =>
    `Pas en file d'attente (pas de démo de carte de fidélité) : ${prospectNames.join(', ')}.`,
}
