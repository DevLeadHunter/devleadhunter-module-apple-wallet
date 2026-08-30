/** What fires an automation. */
export type WalletAutomationTrigger = 'on_scan' | 'broadcast'

/** A merchant automation, as returned by the operator automation API. */
export type WalletAutomation = {
  id: number
  name: string | null
  triggerType: WalletAutomationTrigger
  delayMinutes: number
  fieldValue: string | null
  changeMessage: string | null
  isActive: boolean
}

/** Payload to create an automation. */
export type WalletAutomationCreatePayload = {
  name: string | null
  triggerType: WalletAutomationTrigger
  delayMinutes: number
  fieldValue: string | null
  changeMessage: string | null
}

/** Payload to edit an automation (only the sent fields change). */
export type WalletAutomationUpdatePayload = Partial<WalletAutomationCreatePayload & { isActive: boolean }>

/** Editable form state of an automation. */
export type WalletAutomationForm = {
  name: string
  triggerType: WalletAutomationTrigger
  delayMinutes: number
  fieldValue: string
  changeMessage: string
}
