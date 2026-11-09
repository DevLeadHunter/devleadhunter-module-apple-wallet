import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const layerDirectory: string = dirname(fileURLToPath(import.meta.url))

// No import of `defineNuxtConfig`: Nuxt provides it while it loads a layer, which has no node_modules of its own.
export default defineNuxtConfig({
  $meta: {
    name: 'apple-wallet',
  },

  // Absolute paths: in a layer, `~/components` is the host app's folder, never this one.
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
      walletEnrollBase: process.env.NUXT_PUBLIC_WALLET_ENROLL_BASE || '',
    },
  },

  i18n: {
    locales: [
      { code: 'en', language: 'en-US', file: 'en.json' },
      { code: 'fr', language: 'fr-FR', file: 'fr.json' },
    ],
    langDir: 'locales',
  },
})
