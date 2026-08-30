import { ApiClient } from './api'
import type {
  WalletAutomation,
  WalletAutomationCreatePayload,
  WalletAutomationUpdatePayload,
} from '~/types/WalletAutomation'

/** Operator-side CRUD + broadcast for a program's loyalty automations. */
export class WalletAutomationService {
  /**
   * List a program's automations.
   * @param programId - The program.
   * @returns Its automations.
   */
  static list(programId: number): Promise<WalletAutomation[]> {
    return ApiClient.get<WalletAutomation[]>(`/api/v1/wallet/merchant/programs/${programId}/automations`)
  }

  /**
   * Create an automation for a program.
   * @param programId - The program.
   * @param payload - The automation configuration.
   * @returns The created automation.
   */
  static create(programId: number, payload: WalletAutomationCreatePayload): Promise<WalletAutomation> {
    return ApiClient.post<WalletAutomation>(`/api/v1/wallet/merchant/programs/${programId}/automations`, payload)
  }

  /**
   * Edit an automation.
   * @param automationId - The automation to edit.
   * @param payload - The fields to change.
   * @returns The updated automation.
   */
  static update(automationId: number, payload: WalletAutomationUpdatePayload): Promise<WalletAutomation> {
    return ApiClient.patch<WalletAutomation>(`/api/v1/wallet/merchant/automations/${automationId}`, payload)
  }

  /**
   * Delete an automation.
   * @param automationId - The automation to delete.
   */
  static async remove(automationId: number): Promise<void> {
    await ApiClient.delete(`/api/v1/wallet/merchant/automations/${automationId}`)
  }

  /**
   * Fan a broadcast automation out to every active card of its program.
   * @param automationId - The broadcast automation.
   * @returns How many cards it was scheduled for.
   */
  static broadcast(automationId: number): Promise<{ scheduled: number }> {
    return ApiClient.post<{ scheduled: number }>(`/api/v1/wallet/merchant/automations/${automationId}/broadcast`, {})
  }
}
