import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

/**
 * Nuxt layer of the Apple Wallet module, extended by the core's `web/` (see the core's `product-modules.mjs`).
 *
 * In a layer, `~/` is the host app (the core): the paths declared here are absolute, built from this file's folder,
 * so they never resolve against the core. The component folders keep the core's prefixes: `ui/` → `Ui…`, the rest
 * without one, so `components/ui/WalletCardPreview.vue` stays `UiWalletCardPreview`. `defineNuxtConfig` is the global
 * Nuxt provides while it loads a layer, so the layer needs no Nuxt install of its own.
 */

/** Folder of this layer. */
const layerDirectory: string = dirname(fileURLToPath(import.meta.url))

export default defineNuxtConfig({
  $meta: {
    name: 'apple-wallet',
  },

  components: [
    {
      path: join(layerDirectory, 'app/components/ui'),
      prefix: 'Ui',
    },
    {
      path: join(layerDirectory, 'app/components'),
      pathPrefix: false,
      ignore: ['**/ui/**'],
    },
  ],

  runtimeConfig: {
    public: {
      // Public base URL of the wallet enrollment landing (QR codes and shareable links). Empty → same-origin
      // "/carte". Set to e.g. https://fid.dibodev.fr (with a rewrite to /carte/:token) for a short QR.
      walletEnrollBase: process.env.NUXT_PUBLIC_WALLET_ENROLL_BASE || '',
    },
  },

  // Merged with the core's own locale files, which win on a shared key (`i18n/locales/*.json` of this layer).
  i18n: {
    locales: [
      { code: 'en', language: 'en-US', file: 'en.json' },
      { code: 'fr', language: 'fr-FR', file: 'fr.json' },
    ],
    langDir: 'locales',
  },
})
