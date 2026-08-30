import { defineStore } from 'pinia'
import type { ComputedRef, Ref } from 'vue'
import { ref, computed } from 'vue'
import type { MerchantLoginCredentials, MerchantProgram, MerchantTokenResponse } from '~/types/Merchant'
import { MerchantService } from '~/services/merchantService'

/** localStorage key for the merchant token — namespaced so it never collides with the operator session. */
const MERCHANT_TOKEN_KEY: string = 'merchant_token'

/** localStorage key for the cached merchant program. */
const MERCHANT_PROGRAM_KEY: string = 'merchant_program'

/** Pinia store for the dedicated merchant session (login to manage one loyalty program). */
// Pinia ne fournit pas de type nommé pour un store : TypeScript l'élide, il est inécrivable.
// eslint-disable-next-line @typescript-eslint/typedef
export const useMerchantStore = defineStore('merchant', () => {
  const program: Ref<MerchantProgram | null> = ref(null)
  const token: Ref<string | null> = ref(null)
  const isLoading: Ref<boolean> = ref(false)

  const isAuthenticated: ComputedRef<boolean> = computed(() => program.value !== null && token.value !== null)

  /**
   * Authenticate the merchant and load their program.
   * @param credentials - Merchant email and password.
   * @returns Promise that resolves once the session is established.
   * @throws If the credentials are rejected.
   */
  async function login(credentials: MerchantLoginCredentials): Promise<void> {
    try {
      isLoading.value = true
      const tokenResponse: MerchantTokenResponse = await MerchantService.login(credentials)
      token.value = tokenResponse.access_token
      program.value = await MerchantService.getProgram(token.value)
      persist()
    } finally {
      isLoading.value = false
    }
  }

  /** Clear the merchant session from memory and storage. */
  function logout(): void {
    program.value = null
    token.value = null
    if (import.meta.client) {
      localStorage.removeItem(MERCHANT_TOKEN_KEY)
      localStorage.removeItem(MERCHANT_PROGRAM_KEY)
    }
  }

  /** Rehydrate the session from localStorage (called before the first guard check). */
  function initialize(): void {
    if (!import.meta.client) {
      return
    }
    try {
      const storedToken: string | null = localStorage.getItem(MERCHANT_TOKEN_KEY)
      const storedProgram: string | null = localStorage.getItem(MERCHANT_PROGRAM_KEY)
      if (storedToken && storedProgram) {
        token.value = storedToken
        program.value = JSON.parse(storedProgram)
      }
    } catch {
      logout()
    }
  }

  /**
   * Validate the stored token against the API, refreshing the cached program.
   * @returns True when the token is still valid, false otherwise (session cleared).
   */
  async function validate(): Promise<boolean> {
    if (!import.meta.client) {
      return false
    }
    const storedToken: string | null = localStorage.getItem(MERCHANT_TOKEN_KEY)
    if (!storedToken) {
      logout()
      return false
    }
    try {
      token.value = storedToken
      program.value = await MerchantService.getProgram(storedToken)
      persist()
      return true
    } catch {
      logout()
      return false
    }
  }

  /** Write the current token and program to localStorage. */
  function persist(): void {
    if (!import.meta.client || !token.value || !program.value) {
      return
    }
    localStorage.setItem(MERCHANT_TOKEN_KEY, token.value)
    localStorage.setItem(MERCHANT_PROGRAM_KEY, JSON.stringify(program.value))
  }

  return {
    program,
    token,
    isLoading,
    isAuthenticated,
    login,
    logout,
    initialize,
    validate,
  }
})
