<template>
  <div class="space-y-5">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 class="app-page-title">Votre carte de fidélité</h1>
        <p class="mt-1.5 max-w-xl text-sm text-[var(--app-ink-soft)]">
          Suivez les cartes de vos clients et l'état de votre programme, en direct.
        </p>
      </div>
      <span
        class="font-label inline-flex items-center gap-1.5 rounded-full border border-[var(--app-line)] px-2.5 py-1 text-[0.62rem] tracking-[0.08em] text-[var(--app-ink-soft)] uppercase"
      >
        <span class="h-1.5 w-1.5 rounded-full" :style="{ backgroundColor: subscriptionDotColor }" />
        {{ subscriptionLabel }}
      </span>
    </div>

    <div v-if="isLoading" class="flex justify-center py-20">
      <UiLoader />
    </div>

    <template v-else-if="program">
      <div class="grid grid-cols-1 gap-5 @3xl:grid-cols-[22rem_minmax(0,1fr)]">
        <div class="app-card flex items-center justify-center overflow-hidden p-8" :style="stageStyle">
          <UiWalletCardPreview
            :organization-name="program.organizationName"
            :stamps="sampleStamps"
            :stamps-required="program.stampsRequired"
            :reward-label="program.rewardLabel"
            :logo-url="program.logoUrl"
            :background-color="program.backgroundColor"
            :foreground-color="program.foregroundColor"
            :label-color="program.labelColor"
            serial-number="apercu-0001"
          />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div v-for="tile in statTiles" :key="tile.key" class="app-card flex flex-col justify-between p-4">
            <p class="app-label">{{ tile.label }}</p>
            <p class="font-display mt-3 text-3xl font-semibold text-[var(--app-ink)]">{{ tile.value }}</p>
            <p class="mt-1 text-xs text-[var(--app-ink-soft)]">{{ tile.hint }}</p>
          </div>
        </div>
      </div>

      <div class="app-card overflow-hidden">
        <div class="flex items-center justify-between border-b border-[var(--app-line)] px-4 py-3">
          <p class="font-display text-sm font-semibold text-[var(--app-ink)]">Vos clients</p>
          <span class="text-xs text-[var(--app-ink-soft)]"
            >{{ cards.length }} carte{{ cards.length > 1 ? 's' : '' }}</span
          >
        </div>

        <p v-if="cards.length === 0" class="px-4 py-10 text-center text-sm text-[var(--app-ink-soft)]">
          Aucune carte pour l'instant. Elles apparaîtront ici dès qu'un client ajoutera la vôtre à son Wallet.
        </p>

        <div v-else class="overflow-x-auto">
          <table class="w-full min-w-[32rem] text-sm">
            <thead>
              <tr class="border-b border-[var(--app-line)] text-left">
                <th class="app-label px-4 py-2.5 font-medium">Client</th>
                <th class="app-label px-4 py-2.5 font-medium">Tampons</th>
                <th class="app-label px-4 py-2.5 font-medium">Statut</th>
                <th class="app-label px-4 py-2.5 font-medium">Dernier tampon</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="card in cards"
                :key="card.serialNumber"
                class="border-b border-[var(--app-line)] last:border-0"
              >
                <td class="px-4 py-2.5 text-[var(--app-ink)]">{{ card.holderName || 'Client' }}</td>
                <td class="px-4 py-2.5 text-[var(--app-ink)]">
                  <span class="tabular-nums">{{ card.stamps }}</span>
                  <span class="text-[var(--app-ink-soft)]"> / {{ program.stampsRequired }}</span>
                </td>
                <td class="px-4 py-2.5">
                  <span class="inline-flex items-center gap-1.5 text-[var(--app-ink-soft)]">
                    <span
                      class="h-1.5 w-1.5 rounded-full"
                      :style="{ backgroundColor: statusBadge(card.status).dotColor }"
                    />
                    {{ statusBadge(card.status).label }}
                  </span>
                </td>
                <td class="px-4 py-2.5 text-[var(--app-ink-soft)]">
                  {{ formatShortMonthDate(card.lastStampedAt) || '—' }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </template>

    <div v-else class="app-card p-10 text-center">
      <p class="text-sm text-[var(--app-ink-soft)]">Impossible de charger votre programme. Réessayez plus tard.</p>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import { computed, ref, onMounted } from 'vue'
import type { MerchantCard, MerchantProgram, MerchantStats } from '~/types/Merchant'
import type { MerchantCardStatusBadge, MerchantStatTile } from '~/types/MerchantDashboard'
import { useMerchantStore } from '~/stores/merchant'
import { MerchantService } from '~/services/merchantService'
import { formatShortMonthDate } from '~/utils/date'

definePageMeta({
  layout: 'merchant',
  middleware: ['merchant-auth'],
})

const merchantStore: ReturnType<typeof useMerchantStore> = useMerchantStore()

const stats: Ref<MerchantStats | null> = ref(null)
const cards: Ref<MerchantCard[]> = ref([])
const isLoading: Ref<boolean> = ref(true)

/** The logged-in merchant's program, from the session store. */
const program: ComputedRef<MerchantProgram | null> = computed((): MerchantProgram | null => merchantStore.program)

/** Illustrative stamp count on the preview, so the card reads as a live one. */
const sampleStamps: ComputedRef<number> = computed((): number => {
  const required: number = program.value?.stampsRequired ?? 0
  return Math.min(Math.max(1, Math.round(required * 0.4)), required)
})

/** The four headline counters, from the loaded stats. */
const statTiles: ComputedRef<MerchantStatTile[]> = computed((): MerchantStatTile[] => [
  { key: 'issued', label: 'Cartes créées', value: stats.value?.cardsIssued ?? 0, hint: 'Depuis le lancement' },
  {
    key: 'installed',
    label: 'Dans un Wallet',
    value: stats.value?.cardsInstalled ?? 0,
    hint: 'Ajoutées par vos clients',
  },
  { key: 'rewards', label: 'Récompenses prêtes', value: stats.value?.rewardsReady ?? 0, hint: 'À offrir en boutique' },
  { key: 'stamps', label: 'Tampons cumulés', value: stats.value?.totalStamps ?? 0, hint: 'Toutes cartes confondues' },
])

/** Subscription label shown as a pill in the header. */
const subscriptionLabel: ComputedRef<string> = computed((): string =>
  program.value?.subscriptionActive ? 'Programme actif' : 'Programme en pause',
)

/** Dot color reflecting whether the subscription currently grants access. */
const subscriptionDotColor: ComputedRef<string> = computed((): string =>
  program.value?.subscriptionActive ? 'var(--app-green)' : 'var(--app-ink-soft)',
)

/** Soft stage backdrop tinted with the brand color so the card sits on its own ground. */
const stageStyle: ComputedRef<Record<string, string>> = computed((): Record<string, string> => {
  const background: string = program.value?.backgroundColor?.trim() || 'rgb(23, 23, 23)'
  return { background: `radial-gradient(120% 120% at 50% 0%, ${background}22, transparent 70%)` }
})

/**
 * Map a card status to a French label and a semantic dot color.
 * @param status - Raw status from the API (`active`, `completed`, `revoked`).
 * @returns The badge descriptor.
 */
function statusBadge(status: string): MerchantCardStatusBadge {
  if (status === 'completed') {
    return { label: 'Récompense prête', dotColor: 'var(--app-green)' }
  }
  if (status === 'revoked') {
    return { label: 'Révoquée', dotColor: 'var(--app-red)' }
  }
  return { label: 'Active', dotColor: 'var(--app-ink-soft)' }
}

/** Load the stats and customer cards for the logged-in merchant. */
async function load(): Promise<void> {
  const token: string | null = merchantStore.token
  if (!token) {
    isLoading.value = false
    return
  }
  try {
    const [loadedStats, loadedCards]: [MerchantStats, MerchantCard[]] = await Promise.all([
      MerchantService.getStats(token),
      MerchantService.getCards(token),
    ])
    stats.value = loadedStats
    cards.value = loadedCards
  } catch {
    // Keep the zeroed defaults; the guard re-validates the session on the next navigation.
    stats.value = null
    cards.value = []
  } finally {
    isLoading.value = false
  }
}

onMounted(async (): Promise<void> => {
  await load()
})
</script>
