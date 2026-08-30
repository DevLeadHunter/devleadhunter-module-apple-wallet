/** Lifecycle status of a loyalty program. */
export type WalletProgramStatus = 'draft' | 'active' | 'archived'

/** A merchant's loyalty program, as returned by the operator `/wallet/programs` API. */
export type WalletProgram = {
  id: number
  organizationName: string
  description: string | null
  stampsRequired: number
  rewardLabel: string | null
  defaultChangeMessage: string | null
  logoUrl: string | null
  backgroundColor: string | null
  foregroundColor: string | null
  labelColor: string | null
  status: WalletProgramStatus
  publicToken: string | null
  createdAt: string | null
}

/** Payload to create a loyalty program. */
export type WalletProgramCreatePayload = {
  organizationName: string
  stampsRequired: number
  rewardLabel: string | null
  defaultChangeMessage: string | null
  logoUrl: string | null
  backgroundColor: string | null
  foregroundColor: string | null
  labelColor: string | null
}

/** Payload to edit a loyalty program (only the sent fields change). */
export type WalletProgramUpdatePayload = Partial<WalletProgramCreatePayload & { status: WalletProgramStatus }>

/** Freshly provisioned merchant login, shown once for handover. */
export type WalletMerchantCredentials = {
  email: string
  password: string
}

/** A brand-color preset offered when configuring a card. */
export type WalletColorPalette = {
  id: string
  label: string
  background: string
  foreground: string
  labelColor: string
}

/** Visual descriptor for a program's status badge (label + `app-badge` variant classes). */
export type WalletProgramStatusBadge = {
  label: string
  badgeClass: string
}

/** Editable form state of the operator's program configuration page. */
export type WalletProgramForm = {
  organizationName: string
  stampsRequired: number
  rewardLabel: string
  defaultChangeMessage: string
  logoUrl: string
  backgroundColor: string
  foregroundColor: string
  labelColor: string
  status: WalletProgramStatus
}
