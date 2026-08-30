/** A program's public branding, shown on its enrollment landing page. */
export type WalletEnrollProgram = {
  organizationName: string
  stampsRequired: number
  rewardLabel: string | null
  logoUrl: string | null
  backgroundColor: string | null
  foregroundColor: string | null
  labelColor: string | null
}

/** Optional customer details submitted when adding the card (with marketing opt-in). */
export type WalletEnrollBody = {
  holderName: string | null
  holderEmail: string | null
  consent: boolean
}
