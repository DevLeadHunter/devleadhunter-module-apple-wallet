/**
 * Props for {@link UiWalletCardPreview} — a faithful preview of a merchant's Apple
 * Wallet loyalty store card. Colors are the program's brand colors (rgb()/hex strings),
 * applied inline so the card looks like the real pass, not the app theme.
 */
export type UiWalletCardPreviewProps = {
  organizationName: string
  stamps: number
  stampsRequired: number
  rewardLabel?: string | null
  offer?: string | null
  logoUrl?: string | null
  backgroundColor?: string | null
  foregroundColor?: string | null
  labelColor?: string | null
  serialNumber?: string | null
}

/**
 * One filled module of the preview's faux QR code (grid coordinates).
 */
export type WalletCardQrCell = {
  x: number
  y: number
}
