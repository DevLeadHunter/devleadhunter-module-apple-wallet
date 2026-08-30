import type { WalletEnrollBody, WalletEnrollProgram } from '~/types/WalletEnroll'

/** Resolve the API base URL from runtime config. */
function getApiUrl(): string {
  const config: ReturnType<typeof useRuntimeConfig> = useRuntimeConfig()
  return config.public.apiBase
}

/** Public (unauthenticated) enrollment: read a program's branding and add its card to Wallet. */
export class WalletEnrollService {
  /**
   * Fetch a program's public branding by its enrollment token.
   * @param token - Public enrollment token.
   * @returns The program branding.
   * @throws If the token matches no live program.
   */
  static async getProgram(token: string): Promise<WalletEnrollProgram> {
    const response: Response = await fetch(`${getApiUrl()}/api/v1/wallet/enroll/${encodeURIComponent(token)}`)
    if (!response.ok) {
      throw new Error('Programme introuvable')
    }
    return response.json()
  }

  /**
   * Enroll the customer and return the signed `.pkpass` as a blob.
   * @param token - Public enrollment token.
   * @param body - Optional customer details + marketing consent.
   * @returns The `.pkpass` blob to hand to Apple Wallet.
   * @throws If enrollment fails.
   */
  static async addCard(token: string, body: WalletEnrollBody): Promise<Blob> {
    const response: Response = await fetch(`${getApiUrl()}/api/v1/wallet/add/${encodeURIComponent(token)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (!response.ok) {
      throw new Error("Impossible d'ajouter la carte")
    }
    return response.blob()
  }
}
