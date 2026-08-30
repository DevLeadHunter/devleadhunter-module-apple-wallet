/** One headline counter tile on the merchant dashboard. */
export type MerchantStatTile = {
  key: string
  label: string
  value: number
  hint: string
}

/** Visual descriptor for a loyalty card's status badge. */
export type MerchantCardStatusBadge = {
  label: string
  dotColor: string
}
