import type {
  WalletAutomation,
  WalletAutomationCreatePayload,
  WalletAutomationUpdatePayload,
} from '~/types/WalletAutomation'

/** Resolve the API base URL from runtime config. */
function getApiUrl(): string {
  const config: ReturnType<typeof useRuntimeConfig> = useRuntimeConfig()
  return config.public.apiBase
}

/** Merchant self-service CRUD + broadcast for their own program's automations (merchant JWT). */
export class MerchantAutomationService {
  /**
   * List the merchant's automations.
   * @param token - Merchant JWT.
   * @returns The automations.
   */
  static list(token: string): Promise<WalletAutomation[]> {
    return MerchantAutomationService.request<WalletAutomation[]>('GET', '/api/v1/merchant/automations', token)
  }

  /**
   * Create an automation for the merchant's program.
   * @param token - Merchant JWT.
   * @param payload - The automation configuration.
   * @returns The created automation.
   */
  static create(token: string, payload: WalletAutomationCreatePayload): Promise<WalletAutomation> {
    return MerchantAutomationService.request<WalletAutomation>('POST', '/api/v1/merchant/automations', token, payload)
  }

  /**
   * Edit one of the merchant's automations.
   * @param token - Merchant JWT.
   * @param automationId - The automation to edit.
   * @param payload - The fields to change.
   * @returns The updated automation.
   */
  static update(
    token: string,
    automationId: number,
    payload: WalletAutomationUpdatePayload,
  ): Promise<WalletAutomation> {
    return MerchantAutomationService.request<WalletAutomation>(
      'PATCH',
      `/api/v1/merchant/automations/${automationId}`,
      token,
      payload,
    )
  }

  /**
   * Delete one of the merchant's automations.
   * @param token - Merchant JWT.
   * @param automationId - The automation to delete.
   */
  static async remove(token: string, automationId: number): Promise<void> {
    await MerchantAutomationService.request<unknown>('DELETE', `/api/v1/merchant/automations/${automationId}`, token)
  }

  /**
   * Broadcast one of the merchant's automations to every active card.
   * @param token - Merchant JWT.
   * @param automationId - The broadcast automation.
   * @returns How many cards it was scheduled for.
   */
  static broadcast(token: string, automationId: number): Promise<{ scheduled: number }> {
    return MerchantAutomationService.request<{ scheduled: number }>(
      'POST',
      `/api/v1/merchant/automations/${automationId}/broadcast`,
      token,
      {},
    )
  }

  /**
   * Perform an authenticated request and parse the JSON body (empty on 204).
   * @param method - HTTP method.
   * @param path - API path, starting with `/api/v1`.
   * @param token - Merchant JWT sent as a bearer token.
   * @param body - Optional JSON body.
   * @returns The parsed response body.
   * @throws If the response is not ok (surfacing the API detail message).
   */
  private static async request<T>(method: string, path: string, token: string, body?: unknown): Promise<T> {
    const response: Response = await fetch(`${getApiUrl()}${path}`, {
      method,
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    })
    if (!response.ok) {
      const error: { detail: string } = await response.json().catch(() => ({ detail: 'Action refusée' }))
      throw new Error(error.detail || 'Action refusée')
    }
    if (response.status === 204) {
      return undefined as T
    }
    return response.json()
  }
}
