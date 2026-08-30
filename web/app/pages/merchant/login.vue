<template>
  <div class="app-theme" data-theme="light">
    <div class="merchant-login">
      <aside class="merchant-login__poster">
        <div class="merchant-login__glow" aria-hidden="true" />

        <div class="merchant-login__brand">
          <span class="font-display text-lg font-semibold tracking-tight">Fidélité</span>
          <span class="merchant-login__tag">Apple Wallet</span>
        </div>

        <div class="merchant-login__body">
          <p class="merchant-login__eyebrow">Module cartes de fidélité</p>
          <h2 class="merchant-login__headline">Vos clients reviennent. Leur carte est déjà dans leur téléphone.</h2>
          <div class="merchant-login__card">
            <UiWalletCardPreview
              organization-name="Café Mirabeau"
              :stamps="7"
              :stamps-required="10"
              reward-label="1 café offert"
              background-color="rgb(60, 42, 33)"
              foreground-color="rgb(245, 236, 224)"
              label-color="rgba(245, 236, 224, 0.6)"
              serial-number="mirabeau-0042"
            />
          </div>
        </div>

        <p class="merchant-login__foot">Espace réservé aux commerces partenaires.</p>
      </aside>

      <main class="merchant-login__form">
        <div class="w-full max-w-sm">
          <div class="mb-6 flex items-center gap-2">
            <span class="font-display text-lg font-semibold tracking-tight text-[var(--app-ink)]">Fidélité</span>
            <span
              class="font-label rounded-full border border-[var(--app-line)] px-2 py-0.5 text-[0.62rem] tracking-[0.08em] text-[var(--app-ink-soft)] uppercase"
            >
              Apple Wallet
            </span>
          </div>

          <h1 class="app-page-title">Espace commerçant</h1>
          <p class="mt-1.5 text-sm text-[var(--app-ink-soft)]">Connectez-vous pour suivre votre carte de fidélité.</p>

          <form class="mt-6 space-y-4" @submit.prevent="handleSubmit">
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
      </main>
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
  title: 'Espace commerçant — Fidélité',
  robots: 'noindex, nofollow',
})

const merchantStore: ReturnType<typeof useMerchantStore> = useMerchantStore()
const router: ReturnType<typeof useRouter> = useRouter()

const email: Ref<string> = ref('')
const password: Ref<string> = ref('')
const isLoading: Ref<boolean> = ref(false)
const generalError: Ref<string> = ref('')

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

// Already signed in (valid token) → straight to the dashboard.
onMounted(async (): Promise<void> => {
  merchantStore.initialize()
  if (merchantStore.isAuthenticated && (await merchantStore.validate())) {
    router.push('/merchant')
  }
})
</script>

<style scoped>
.merchant-login {
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  min-height: 100vh;
}

.merchant-login__poster {
  position: relative;
  overflow: hidden;
  padding: 2.5rem;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  color: #f4efe7;
  background: radial-gradient(120% 90% at 50% 32%, #2b2620, #17130e 78%);
}

.merchant-login__glow {
  position: absolute;
  left: 50%;
  top: 38%;
  width: 26rem;
  height: 26rem;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, rgba(232, 163, 60, 0.16), transparent 62%);
  pointer-events: none;
}

.merchant-login__brand {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #f7f2e9;
}

.merchant-login__tag {
  font-family: var(--app-font-mono);
  font-size: 0.6rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(247, 242, 233, 0.7);
  border: 1px solid rgba(247, 242, 233, 0.2);
  border-radius: 999px;
  padding: 0.2rem 0.55rem;
}

.merchant-login__body {
  position: relative;
  z-index: 2;
  margin: auto 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 1.6rem;
}

.merchant-login__eyebrow {
  font-family: var(--app-font-mono);
  font-size: 0.62rem;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: rgba(247, 242, 233, 0.55);
}

.merchant-login__headline {
  font-size: 1.5rem;
  font-weight: 600;
  line-height: 1.3;
  letter-spacing: -0.01em;
  max-width: 22rem;
  color: #f7f2e9;
  text-wrap: balance;
}

.merchant-login__card {
  transform: rotate(-3deg);
  filter: drop-shadow(0 30px 50px rgba(0, 0, 0, 0.5));
}

.merchant-login__foot {
  position: relative;
  z-index: 2;
  font-size: 0.72rem;
  color: rgba(247, 242, 233, 0.45);
}

.merchant-login__form {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2.5rem 1.5rem;
  background-color: var(--app-bg);
}

@media (max-width: 880px) {
  .merchant-login {
    grid-template-columns: 1fr;
  }

  .merchant-login__poster {
    display: none;
  }
}
</style>
