import { DashboardModuleRegistry } from '~/utils/dashboardModuleRegistry'
import { EmailVariables } from '~/utils/emailVariables'
import { WALLET_EMAIL_VARIABLES } from '../constants/walletEmailVariables'
import { WALLET_DASHBOARD_MODULE, WALLET_MODULE_KEY } from '../constants/walletModule'

/** Registers the loyalty cards in the module switcher and the card's email variables, on every request (idempotent). */
export default defineNuxtPlugin((): void => {
  DashboardModuleRegistry.register(WALLET_DASHBOARD_MODULE)
  EmailVariables.registerModuleVariables(WALLET_MODULE_KEY, WALLET_EMAIL_VARIABLES)
})
