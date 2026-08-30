/**
 * A merchant's loyalty program config, as returned by `GET /merchant/me` — everything
 * the card preview and the dashboard header need. Colors are brand strings (rgb()/hex).
 */
export type MerchantProgram = {
  organizationName: string
  stampsRequired: number
  rewardLabel: string | null
  defaultChangeMessage: string | null
  logoUrl: string | null
  backgroundColor: string | null
  foregroundColor: string | null
  labelColor: string | null
  publicToken: string | null
  subscriptionStatus: string
  subscriptionActive: boolean
}

/** Headline counters for a merchant's program (`GET /merchant/summary`). */
export type MerchantStats = {
  cardsIssued: number
  cardsInstalled: number
  rewardsReady: number
  totalStamps: number
}

/** One customer's loyalty card in the merchant's list (`GET /merchant/cards`). */
export type MerchantCard = {
  serialNumber: string
  stamps: number
  status: string
  holderName: string | null
  lastStampedAt: string | null
  addedToWalletAt: string | null
}

/** Credentials a merchant submits to `POST /merchant/login`. */
export type MerchantLoginCredentials = {
  email: string
  password: string
}

/** Access token returned by `POST /merchant/login`. */
export type MerchantTokenResponse = {
  access_token: string
  token_type: string
}
