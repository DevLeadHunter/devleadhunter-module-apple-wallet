<template>
  <div class="app-theme" data-theme="light">
    <div class="flex min-h-screen flex-col items-center px-4 py-10" :style="{ backgroundColor: 'var(--app-bg)' }">
      <div class="w-full max-w-sm">
        <div v-if="isLoading" class="flex justify-center py-24">
          <UiLoader />
        </div>

        <div v-else-if="!program" class="app-card mt-16 p-8 text-center">
          <span class="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--app-surface-2)]">
            <UIcon name="i-lucide-search-x" class="h-6 w-6 text-[var(--app-ink-soft)]" />
          </span>
          <p class="text-sm font-medium text-[var(--app-ink)]">Carte introuvable</p>
          <p class="mt-1.5 text-xs text-[var(--app-ink-soft)]">
            Ce lien n'est plus valide. Demandez le QR code à jour au commerce.
          </p>
        </div>

        <template v-else>
          <div class="mb-7 flex justify-center">
            <UiWalletCardPreview
              :organization-name="program.organizationName"
              :stamps="0"
              :stamps-required="program.stampsRequired"
              :reward-label="program.rewardLabel"
              :logo-url="program.logoUrl"
              :background-color="program.backgroundColor"
              :foreground-color="program.foregroundColor"
              :label-color="program.labelColor"
              serial-number="votre-carte"
            />
          </div>

          <div class="text-center">
            <h1 class="app-page-title">{{ program.organizationName }}</h1>
            <p class="mt-1.5 text-sm text-[var(--app-ink-soft)]">
              {{ program.stampsRequired }} tampons =
              <span class="font-medium text-[var(--app-ink)]">{{ program.rewardLabel || 'une récompense' }}</span
              >. Ajoutez votre carte, elle vous suit dans votre téléphone.
            </p>
          </div>

          <div v-if="added" class="app-card mt-7 flex flex-col items-center gap-2 p-6 text-center">
            <span class="flex h-11 w-11 items-center justify-center rounded-full bg-[var(--app-green-soft)]">
              <UIcon name="i-lucide-check" class="h-5 w-5 text-[var(--app-green)]" />
            </span>
            <p class="text-sm font-medium text-[var(--app-ink)]">Carte prête !</p>
            <p class="text-xs text-[var(--app-ink-soft)]">
              Validez l'ajout à Apple Wallet. Si rien ne s'ouvre, vérifiez vos téléchargements.
            </p>
            <button type="button" class="app-btn-secondary mt-2 h-9 text-xs" @click="added = false">
              Ajouter à un autre téléphone
            </button>
          </div>

          <form v-else class="mt-7 space-y-4" @submit.prevent="addToWallet">
            <div
              v-if="errorMessage"
              class="rounded-lg border border-[var(--app-red)]/30 bg-[var(--app-red)]/8 px-3 py-2 text-sm text-[var(--app-red)]"
            >
              {{ errorMessage }}
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div class="space-y-1.5">
                <label class="app-label" for="enroll-name">Prénom</label>
                <input id="enroll-name" v-model="firstName" class="input-field" type="text" maxlength="40" />
              </div>
              <div class="space-y-1.5">
                <label class="app-label" for="enroll-email">Email</label>
                <input id="enroll-email" v-model="email" class="input-field" type="email" autocomplete="email" />
              </div>
            </div>

            <label class="flex cursor-pointer items-start gap-2.5">
              <input v-model="consent" type="checkbox" class="mt-0.5 h-4 w-4 accent-[var(--app-ink)]" />
              <span class="text-xs leading-relaxed text-[var(--app-ink-soft)]">
                J'accepte de recevoir les offres de {{ program.organizationName }} sur ma carte.
              </span>
            </label>

            <button type="submit" class="app-btn-primary h-11 w-full" :disabled="isAdding">
              <UIcon
                :name="isAdding ? 'i-lucide-loader-circle' : 'i-lucide-wallet'"
                :class="['h-4 w-4', isAdding && 'animate-spin']"
              />
              Ajouter à Apple Wallet
            </button>

            <p class="text-center text-[11px] text-[var(--app-ink-soft)]">
              Compatible iPhone. Le prénom et l'email sont facultatifs, mais retrouvent votre carte si besoin.
            </p>
          </form>
        </template>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import { ref, onMounted } from 'vue'
import type { WalletEnrollProgram } from '~/types/WalletEnroll'
import { WalletEnrollService } from '~/services/walletEnrollService'

definePageMeta({
  layout: false,
  sitemap: false,
})

useSeoMeta({
  title: 'Votre carte de fidélité',
  robots: 'noindex, nofollow',
})

const route: ReturnType<typeof useRoute> = useRoute()
const token: string = String(route.params.token)

const program: Ref<WalletEnrollProgram | null> = ref(null)
const isLoading: Ref<boolean> = ref(true)
const isAdding: Ref<boolean> = ref(false)
const added: Ref<boolean> = ref(false)
const errorMessage: Ref<string> = ref('')

const firstName: Ref<string> = ref('')
const email: Ref<string> = ref('')
const consent: Ref<boolean> = ref(false)

/** Add the customer's card to Apple Wallet, handing off the signed `.pkpass`. */
async function addToWallet(): Promise<void> {
  if (!program.value) {
    return
  }
  isAdding.value = true
  errorMessage.value = ''
  try {
    const blob: Blob = await WalletEnrollService.addCard(token, {
      holderName: firstName.value.trim() || null,
      holderEmail: email.value.trim() || null,
      consent: consent.value,
    })
    const url: string = URL.createObjectURL(blob)
    const anchor: HTMLAnchorElement = document.createElement('a')
    anchor.href = url
    anchor.download = 'carte-fidelite.pkpass'
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    setTimeout((): void => URL.revokeObjectURL(url), 60000)
    added.value = true
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : "Impossible d'ajouter la carte"
  } finally {
    isAdding.value = false
  }
}

onMounted(async (): Promise<void> => {
  try {
    program.value = await WalletEnrollService.getProgram(token)
  } catch {
    program.value = null
  } finally {
    isLoading.value = false
  }
})
</script>
