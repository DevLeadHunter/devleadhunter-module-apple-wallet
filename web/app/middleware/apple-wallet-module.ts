import type { RouteLocationNormalized } from 'vue-router'
import { useModuleStore } from '~/stores/moduleStore'
import { WALLET_MODULE_KEY, WALLET_SECTION_PATH } from '../constants/walletModule'

/** Sends the loyalty card pages to the dashboard while the module is off, and switches the sidebar to the module on them. */
export default defineNuxtRouteMiddleware(async (to: RouteLocationNormalized) => {
  const moduleStore: ReturnType<typeof useModuleStore> = useModuleStore()
  if (import.meta.client && !(await moduleStore.isModuleEnabled(WALLET_MODULE_KEY))) {
    return navigateTo('/dashboard')
  }

  const isModuleSectionPage: boolean = to.path === WALLET_SECTION_PATH || to.path.startsWith(`${WALLET_SECTION_PATH}/`)
  if (isModuleSectionPage) {
    moduleStore.setModule(WALLET_MODULE_KEY)
  }
})
