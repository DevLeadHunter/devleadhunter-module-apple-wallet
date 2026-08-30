import type {
  MerchantCard,
  MerchantLoginCredentials,
  MerchantProgram,
  MerchantStats,
  MerchantTokenResponse,
} from '~/types/Merchant'

/** Resolve the API base URL from runtime config. */
function getApiUrl(): string {
  const config: ReturnType<typeof useRuntimeConfig> = useRuntimeConfig()
  return config.public.apiBase
}

/**
 * Read views and login for the dedicated merchant surface (a merchant managing their own
 * loyalty program), authenticated by a merchant JWT — separate from the operator `AuthService`.
 */
export class MerchantService {
  /**
   * Authenticate a merchant with their email and password.
   * @param credentials - Merchant email and password.
   * @returns The access token.
   * @throws If the credentials are rejected.
   */
  static async login(credentials: MerchantLoginCredentials): Promise<MerchantTokenResponse> {
    const response: Response = await fetch(`${getApiUrl()}/api/v1/merchant/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    })

    if (!response.ok) {
      const error: { detail: string } = await response.json().catch(() => ({ detail: 'Connexion refusée' }))
      throw new Error(error.detail || 'Connexion refusée')
    }

    return response.json()
  }

  /**
   * Fetch the merchant's own program config (drives the card preview and header).
   * @param token - Merchant JWT.
   * @returns The program.
   * @throws If the token is invalid or the program is gone.
   */
  static async getProgram(token: string): Promise<MerchantProgram> {
    return MerchantService.authorizedGet<MerchantProgram>('/api/v1/merchant/me', token)
  }

  /**
   * Fetch the headline counters for the merchant's program.
   * @param token - Merchant JWT.
   * @returns The stats.
   * @throws If the request fails.
   */
  static async getStats(token: string): Promise<MerchantStats> {
    return MerchantService.authorizedGet<MerchantStats>('/api/v1/merchant/summary', token)
  }

  /**
   * Fetch the merchant's customer cards, most recently stamped first.
   * @param token - Merchant JWT.
   * @returns The cards.
   * @throws If the request fails.
   */
  static async getCards(token: string): Promise<MerchantCard[]> {
    return MerchantService.authorizedGet<MerchantCard[]>('/api/v1/merchant/cards', token)
  }

  /**
   * Perform an authenticated GET and parse the JSON body.
   * @param path - API path, starting with `/api/v1`.
   * @param token - Merchant JWT sent as a bearer token.
   * @returns The parsed response body.
   * @throws If the response is not ok.
   */
  private static async authorizedGet<T>(path: string, token: string): Promise<T> {
    const response: Response = await fetch(`${getApiUrl()}${path}`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error('Requête refusée')
    }

    return response.json()
  }
}
