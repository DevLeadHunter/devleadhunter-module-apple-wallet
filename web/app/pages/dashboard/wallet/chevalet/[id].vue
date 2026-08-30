<template>
  <div class="app-theme" data-theme="light">
    <div class="min-h-screen p-6" :style="{ backgroundColor: 'var(--app-bg)' }">
      <div class="no-print mx-auto mb-6 flex max-w-md items-center justify-between">
        <NuxtLink
          :to="`/dashboard/wallet/${programId}`"
          class="inline-flex items-center gap-1.5 text-xs font-medium text-[var(--app-ink-soft)] transition-colors hover:text-[var(--app-ink)]"
        >
          <UIcon name="i-lucide-arrow-left" class="h-3.5 w-3.5" />
          Retour
        </NuxtLink>
        <button type="button" class="app-btn-primary h-9 text-xs" :disabled="!qrDataUrl" @click="printPoster">
          <UIcon name="i-lucide-printer" class="h-4 w-4" />
          Imprimer
        </button>
      </div>

      <div v-if="isLoading" class="flex justify-center py-24">
        <UiLoader />
      </div>

      <div v-else-if="program" class="chevalet mx-auto">
        <div class="chevalet__brand">
          <img v-if="program.logoUrl" :src="program.logoUrl" :alt="program.organizationName" class="chevalet__logo" />
          <span class="chevalet__name">{{ program.organizationName }}</span>
        </div>
        <p class="chevalet__eyebrow">Carte de fidélité</p>
        <img v-if="qrDataUrl" :src="qrDataUrl" alt="QR code d'ajout de la carte" class="chevalet__qr" />
        <p class="chevalet__cta">Scannez pour ajouter votre carte</p>
        <p class="chevalet__reward">
          {{ program.stampsRequired }} tampons = {{ program.rewardLabel || 'une récompense' }}
        </p>
        <p class="chevalet__foot">Ajout gratuit à Apple Wallet · iPhone</p>
      </div>

      <div v-else class="app-card mx-auto max-w-md p-8 text-center">
        <p class="text-sm text-[var(--app-ink-soft)]">Programme introuvable.</p>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import { ref, onMounted } from 'vue'
import type { WalletProgram } from '~/types/WalletProgram'
import { WalletProgramService } from '~/services/walletProgramService'
import { useWalletEnrollLink } from '~/composables/useWalletEnrollLink'

definePageMeta({
  layout: false,
  middleware: ['auth'],
})

useSeoMeta({
  robots: 'noindex, nofollow',
})

const route: ReturnType<typeof useRoute> = useRoute()
const programId: number = Number(route.params.id)
const { buildQr }: ReturnType<typeof useWalletEnrollLink> = useWalletEnrollLink()

const program: Ref<WalletProgram | null> = ref(null)
const qrDataUrl: Ref<string> = ref('')
const isLoading: Ref<boolean> = ref(true)

/** Print the poster (the on-screen controls are hidden by the print stylesheet). */
function printPoster(): void {
  window.print()
}

onMounted(async (): Promise<void> => {
  try {
    const loaded: WalletProgram = await WalletProgramService.get(programId)
    program.value = loaded
    if (loaded.publicToken) {
      qrDataUrl.value = await buildQr(loaded.publicToken)
    }
  } catch {
    program.value = null
  } finally {
    isLoading.value = false
  }
})
</script>

<style scoped>
.chevalet {
  max-width: 22rem;
  text-align: center;
  background: var(--app-surface);
  border: 1px solid var(--app-line);
  border-radius: 1rem;
  padding: 2.5rem 2rem;
}

.chevalet__brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
}

.chevalet__logo {
  height: 2.5rem;
  width: 2.5rem;
  border-radius: 0.5rem;
  object-fit: cover;
}

.chevalet__name {
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--app-ink);
}

.chevalet__eyebrow {
  margin-top: 0.35rem;
  font-family: var(--app-font-mono);
  font-size: 0.7rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
  color: var(--app-ink-soft);
}

.chevalet__qr {
  width: 15rem;
  height: 15rem;
  margin: 1.5rem auto;
  display: block;
}

.chevalet__cta {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--app-ink);
}

.chevalet__reward {
  margin-top: 0.4rem;
  font-size: 0.9rem;
  color: var(--app-ink-soft);
}

.chevalet__foot {
  margin-top: 1.5rem;
  font-size: 0.72rem;
  color: var(--app-faint);
}

@media print {
  .no-print {
    display: none !important;
  }

  .chevalet {
    border: none;
  }
}
</style>
