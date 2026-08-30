<template>
  <div class="app-theme" data-theme="light">
    <div class="flex min-h-screen items-center justify-center px-4 py-10" :style="{ backgroundColor: 'var(--app-bg)' }">
      <div class="w-full max-w-sm">
        <div class="mb-8 text-center">
          <div class="mb-4 flex items-center justify-center gap-2">
            <span class="font-display text-lg font-semibold tracking-tight text-[var(--app-ink)]">devleadhunter</span>
            <span
              class="font-label rounded-full border border-[var(--app-line)] px-2 py-0.5 text-[0.62rem] tracking-[0.08em] text-[var(--app-ink-soft)] uppercase"
            >
              Fidélité
            </span>
          </div>
          <h1 class="app-page-title">Espace commerçant</h1>
          <p class="mt-1.5 text-sm text-[var(--app-ink-soft)]">Connectez-vous pour suivre votre carte de fidélité.</p>
        </div>

        <form class="app-card space-y-4 p-6" @submit.prevent="handleSubmit">
          <div
            v-if="generalError"
            class="rounded-lg border border-[var(--app-red)]/30 bg-[var(--app-red)]/8 px-3 py-2 text-sm text-[var(--app-red)]"
          >
            {{ generalError }}
          </div>

          <div class="space-y-1.5">
            <label class="app-label" for="merchant-email">Identifiant</label>
            <input
              id="merchant-email"
              v-model="email"
              class="input-field"
              type="email"
              autocomplete="username"
              required
              placeholder="votre-commerce-xxxx@merchant.dibodev.fr"
            />
          </div>

          <div class="space-y-1.5">
            <label class="app-label" for="merchant-password">Mot de passe</label>
            <UiPasswordInput id="merchant-password" v-model="password" required />
          </div>

          <UiDlhButton type="submit" class="w-full" :loading="isLoading">Se connecter</UiDlhButton>
        </form>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import { ref, onMounted } from 'vue'
import { useMerchantStore } from '~/stores/merchant'

definePageMeta({
  layout: false,
  sitemap: false,
})

useSeoMeta({
  title: 'Espace commerçant — DevLeadHunter',
  robots: 'noindex, nofollow',
})

const merchantStore: ReturnType<typeof useMerchantStore> = useMerchantStore()
const router: ReturnType<typeof useRouter> = useRouter()

const email: Ref<string> = ref('')
const password: Ref<string> = ref('')
const isLoading: Ref<boolean> = ref(false)
const generalError: Ref<string> = ref('')

// Already signed in (valid token) → straight to the dashboard.
onMounted(async (): Promise<void> => {
  merchantStore.initialize()
  if (merchantStore.isAuthenticated && (await merchantStore.validate())) {
    router.push('/merchant')
  }
})

/** Submit the credentials and enter the dashboard on success. */
async function handleSubmit(): Promise<void> {
  generalError.value = ''
  if (!email.value || !password.value) {
    generalError.value = 'Renseignez votre identifiant et votre mot de passe.'
    return
  }
  isLoading.value = true
  try {
    await merchantStore.login({ email: email.value, password: password.value })
    router.push('/merchant')
  } catch (error) {
    generalError.value = error instanceof Error ? error.message : 'Connexion refusée.'
  } finally {
    isLoading.value = false
  }
}
</script>
