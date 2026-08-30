/**
 * Merchant authentication middleware — protects the dedicated merchant surface.
 * Validates the merchant token client-side and redirects to the merchant login otherwise.
 * @module middleware/merchant-auth
 */

export default defineNuxtRouteMiddleware(async () => {
  const merchantStore: ReturnType<typeof useMerchantStore> = useMerchantStore()

  // localStorage is client-only; on SSR let the client run the validation.
  if (!import.meta.client) {
    return
  }

  if (!merchantStore.isAuthenticated) {
    merchantStore.initialize()
  }

  const isValid: boolean = await merchantStore.validate()
  if (!isValid) {
    return navigateTo('/merchant/login')
  }
})
