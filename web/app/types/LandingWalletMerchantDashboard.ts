/** One headline stat of the mock merchant dashboard card. */
export type LandingWalletMerchantStat = {
  valueKey: string
  labelKey: string
}

/** One mock client row of the merchant dashboard card. */
export type LandingWalletMerchantClientRow = {
  nameKey: string
  metaKey: string
  isRewardDue: boolean
}
