/** One headline KPI tile on the merchant dashboard (value + a semantic colored icon). */
export type MerchantStatTile = {
  key: string
  label: string
  value: number
  hint: string
  icon: string
  iconColorClass: string
  iconBackgroundClass: string
}

/** Visual descriptor for a loyalty card's status badge (label + `app-badge` variant classes). */
export type MerchantCardStatusBadge = {
  label: string
  badgeClass: string
}

/** Tone of a transient action confirmation. */
export type MerchantFlashTone = 'success' | 'error' | 'warn' | 'neutral'

/** A transient confirmation shown after a stamp/redeem action. */
export type MerchantFlash = {
  text: string
  tone: MerchantFlashTone
}
