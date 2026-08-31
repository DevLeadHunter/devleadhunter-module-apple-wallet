<template>
  <div class="space-y-8">
    <div class="flex flex-col gap-4 @2xl:flex-row @2xl:items-end @2xl:justify-between">
      <div>
        <p class="app-label flex items-center gap-2">
          <LandingAsterisk class="text-[0.6rem] text-[var(--app-accent)]" />
          Fidélité
        </p>
        <h1 class="app-page-title mt-2">Votre carte de fidélité</h1>
        <p class="mt-1.5 text-sm text-[var(--app-ink-soft)]">
          Suivez les cartes de vos clients et l'état de votre programme, en direct.
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <NuxtLink to="/merchant/automations" class="app-btn-secondary h-9 text-xs">
          <UIcon name="i-lucide-megaphone" class="h-4 w-4" />
          Vos offres
        </NuxtLink>
        <span class="app-badge" :class="subscriptionActive ? 'app-badge--success' : ''">
          <span class="h-1.5 w-1.5 rounded-full" :style="{ backgroundColor: subscriptionDotColor }" />
          {{ subscriptionLabel }}
        </span>
      </div>
    </div>

    <div v-if="isLoading" class="space-y-8">
      <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div v-for="n in 4" :key="n" class="app-card h-24 animate-pulse"></div>
      </div>
      <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div class="app-card h-80 animate-pulse lg:col-span-2"></div>
        <div class="app-card h-80 animate-pulse"></div>
      </div>
    </div>

    <template v-else-if="program">
      <section class="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div v-for="tile in statTiles" :key="tile.key" class="app-card flex flex-col gap-1.5 p-4">
          <div class="flex items-center justify-between">
            <p class="app-label">{{ tile.label }}</p>
            <span :class="['flex h-8 w-8 items-center justify-center rounded-lg', tile.iconBackgroundClass]">
              <UIcon :name="tile.icon" :class="['h-4 w-4', tile.iconColorClass]" />
            </span>
          </div>
          <p class="text-2xl font-bold text-[var(--app-ink)] tabular-nums">{{ tile.value }}</p>
          <p class="text-[11px] leading-snug text-[var(--app-ink-soft)]">{{ tile.hint }}</p>
        </div>
      </section>

      <section class="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div class="app-card overflow-hidden p-0 lg:col-span-2">
          <div class="flex items-center justify-between border-b border-[var(--app-line)] px-4 py-3 md:px-5">
            <h2 class="text-sm font-semibold text-[var(--app-ink)]">Vos clients</h2>
            <span class="text-xs text-[var(--app-ink-soft)]">
              {{ cards.length }} carte{{ cards.length > 1 ? 's' : '' }}
            </span>
          </div>

          <p v-if="cards.length === 0" class="px-4 py-12 text-center text-sm text-[var(--app-ink-soft)]">
            Aucune carte pour l'instant. Elles apparaîtront ici dès qu'un client ajoutera la vôtre à son Wallet.
          </p>

          <BaseTable v-else min-width="42rem">
            <template #head>
              <BaseTableTh>Client</BaseTableTh>
              <BaseTableTh>Tampons</BaseTableTh>
              <BaseTableTh>Statut</BaseTableTh>
              <BaseTableTh align="right">Dernier tampon</BaseTableTh>
              <BaseTableTh align="right" sr-only>Actions</BaseTableTh>
            </template>

            <BaseTableTr v-for="card in cards" :key="card.serialNumber">
              <BaseTableTd label="Client">
                <div class="flex items-center gap-3">
                  <span
                    class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--app-surface-2)] text-xs font-semibold text-[var(--app-ink)]"
                  >
                    {{ cardInitial(card) }}
                  </span>
                  <span class="text-sm font-medium text-[var(--app-ink)]">{{ card.holderName || 'Client' }}</span>
                </div>
              </BaseTableTd>
              <BaseTableTd label="Tampons">
                <div class="flex items-center gap-2.5">
                  <div class="h-1.5 w-16 overflow-hidden rounded-full bg-[var(--app-surface-2)]">
                    <div class="h-full rounded-full bg-[var(--app-ink)]" :style="{ width: stampWidth(card) }"></div>
                  </div>
                  <span class="text-sm font-semibold text-[var(--app-ink)] tabular-nums">
                    {{ card.stamps }}/{{ program.stampsRequired }}
                  </span>
                </div>
              </BaseTableTd>
              <BaseTableTd label="Statut">
                <span :class="statusBadge(card.status).badgeClass">{{ statusBadge(card.status).label }}</span>
              </BaseTableTd>
              <BaseTableTd
                label="Dernier tampon"
                align="right"
                class="text-sm whitespace-nowrap text-[var(--app-ink-soft)]"
              >
                {{ formatShortMonthDate(card.lastStampedAt) || '—' }}
              </BaseTableTd>
              <BaseTableTd label="Actions" align="right">
                <button
                  v-if="card.status === 'completed'"
                  type="button"
                  class="app-btn-secondary h-8 px-3 text-xs"
                  :disabled="actingSerial === card.serialNumber"
                  @click="redeem(card)"
                >
                  <UIcon
                    :name="actingSerial === card.serialNumber ? 'i-lucide-loader-circle' : 'i-lucide-gift'"
                    :class="['h-3.5 w-3.5', actingSerial === card.serialNumber && 'animate-spin']"
                  />
                  Remettre
                </button>
                <button
                  v-else
                  type="button"
                  class="app-btn-secondary h-8 px-3 text-xs"
                  :disabled="actingSerial === card.serialNumber"
                  @click="stamp(card)"
                >
                  <UIcon
                    :name="actingSerial === card.serialNumber ? 'i-lucide-loader-circle' : 'i-lucide-plus'"
                    :class="['h-3.5 w-3.5', actingSerial === card.serialNumber && 'animate-spin']"
                  />
                  Tampon
                </button>
              </BaseTableTd>
            </BaseTableTr>
          </BaseTable>
        </div>

        <div class="app-card p-5">
          <div class="mb-4 flex items-center justify-between">
            <h2 class="text-sm font-semibold text-[var(--app-ink)]">Votre carte</h2>
            <span class="app-label">Aperçu client</span>
          </div>

          <div class="flex items-center justify-center overflow-hidden rounded-lg p-5" :style="stageStyle">
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

          <div class="mt-4 divide-y divide-[var(--app-line-soft)]">
            <div class="flex items-center gap-3 py-2.5 first:pt-0">
              <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--app-accent-soft)]">
                <UIcon name="i-lucide-stamp" class="h-4 w-4 text-[var(--app-accent-ink)]" />
              </span>
              <div class="min-w-0 flex-1">
                <p class="text-[11px] text-[var(--app-ink-soft)]">Objectif</p>
                <p class="text-sm font-medium text-[var(--app-ink)]">{{ program.stampsRequired }} tampons</p>
              </div>
            </div>
            <div v-if="program.rewardLabel" class="flex items-center gap-3 py-2.5">
              <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[var(--app-green-soft)]">
                <UIcon name="i-lucide-gift" class="h-4 w-4 text-[var(--app-green)]" />
              </span>
              <div class="min-w-0 flex-1">
                <p class="text-[11px] text-[var(--app-ink-soft)]">Récompense</p>
                <p class="truncate text-sm font-medium text-[var(--app-ink)]">{{ program.rewardLabel }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </template>

    <div v-else class="app-card p-10 text-center">
      <p class="text-sm text-[var(--app-ink-soft)]">Impossible de charger votre programme. Réessayez plus tard.</p>
    </div>

    <div
      v-if="flash"
      class="fixed bottom-5 left-1/2 z-50 -translate-x-1/2 rounded-full px-4 py-2 text-sm font-medium shadow-[var(--app-shadow-soft)]"
      :style="flashStyle"
      role="status"
    >
      {{ flash.text }}
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import { computed, ref, onMounted, onUnmounted } from 'vue'
import type { MerchantCard, MerchantCardAction, MerchantProgram, MerchantStats } from '~/types/Merchant'
import type {
  MerchantCardStatusBadge,
  MerchantFlash,
  MerchantFlashTone,
  MerchantStatTile,
} from '~/types/MerchantDashboard'
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
const actingSerial: Ref<string | null> = ref(null)
const flash: Ref<MerchantFlash | null> = ref(null)
let flashTimer: ReturnType<typeof setTimeout> | null = null

/** The logged-in merchant's program, from the session store. */
const program: ComputedRef<MerchantProgram | null> = computed((): MerchantProgram | null => merchantStore.program)

/** Whether the subscription currently grants access. */
const subscriptionActive: ComputedRef<boolean> = computed((): boolean => program.value?.subscriptionActive ?? false)

/** Subscription label shown as a badge in the header. */
const subscriptionLabel: ComputedRef<string> = computed((): string =>
  subscriptionActive.value ? 'Programme actif' : 'Programme en pause',
)

/** Dot color reflecting whether the subscription currently grants access. */
const subscriptionDotColor: ComputedRef<string> = computed((): string =>
  subscriptionActive.value ? 'var(--app-green)' : 'var(--app-ink-soft)',
)

/** Background/text style of the transient action flash, by tone. */
const flashStyle: ComputedRef<Record<string, string>> = computed((): Record<string, string> => {
  const tone: MerchantFlashTone = flash.value?.tone ?? 'neutral'
  if (tone === 'success') {
    return { backgroundColor: 'var(--app-green)', color: '#fbf9f3' }
  }
  if (tone === 'error') {
    return { backgroundColor: 'var(--app-red)', color: '#fbf9f3' }
  }
  if (tone === 'warn') {
    return { backgroundColor: 'var(--app-accent)', color: '#1d1a14' }
  }
  return { backgroundColor: 'var(--app-ink)', color: 'var(--app-surface)' }
})

/** Illustrative stamp count on the preview, so the card reads as a live one. */
const sampleStamps: ComputedRef<number> = computed((): number => {
  const required: number = program.value?.stampsRequired ?? 0
  return Math.min(Math.max(1, Math.round(required * 0.4)), required)
})

/** The four headline counters, each with a semantic colored icon. */
const statTiles: ComputedRef<MerchantStatTile[]> = computed((): MerchantStatTile[] => {
  const current: MerchantStats | null = stats.value
  const issued: number = current?.cardsIssued ?? 0
  const installed: number = current?.cardsInstalled ?? 0
  const installedHint: string =
    issued > 0 ? `${Math.round((installed / issued) * 100)} % des cartes créées` : 'Ajoutées par vos clients'
  return [
    {
      key: 'issued',
      label: 'Cartes créées',
      value: issued,
      hint: 'Depuis le lancement',
      icon: 'i-lucide-users',
      iconColorClass: 'text-[var(--app-blue)]',
      iconBackgroundClass: 'bg-[var(--app-blue-soft)]',
    },
    {
      key: 'installed',
      label: 'Dans un Wallet',
      value: installed,
      hint: installedHint,
      icon: 'i-lucide-wallet',
      iconColorClass: 'text-[var(--app-violet)]',
      iconBackgroundClass: 'bg-[var(--app-violet-soft)]',
    },
    {
      key: 'rewards',
      label: 'Récompenses prêtes',
      value: current?.rewardsReady ?? 0,
      hint: 'À offrir en boutique',
      icon: 'i-lucide-gift',
      iconColorClass: 'text-[var(--app-green)]',
      iconBackgroundClass: 'bg-[var(--app-green-soft)]',
    },
    {
      key: 'stamps',
      label: 'Tampons cumulés',
      value: current?.totalStamps ?? 0,
      hint: 'Toutes cartes confondues',
      icon: 'i-lucide-stamp',
      iconColorClass: 'text-[var(--app-accent-ink)]',
      iconBackgroundClass: 'bg-[var(--app-accent-soft)]',
    },
  ]
})

/** Soft stage backdrop tinted with the brand color so the card sits on its own ground. */
const stageStyle: ComputedRef<Record<string, string>> = computed((): Record<string, string> => {
  const background: string = program.value?.backgroundColor?.trim() || 'rgb(23, 23, 23)'
  return { background: `radial-gradient(120% 120% at 50% 0%, ${background}18, transparent 72%)` }
})

/**
 * First letter of a card holder's name, for the row avatar.
 * @param card - The customer card.
 * @returns The uppercase initial, or a neutral dot.
 */
function cardInitial(card: MerchantCard): string {
  return card.holderName?.trim().charAt(0).toUpperCase() || '·'
}

/**
 * Width of a card's stamp progress bar.
 * @param card - The customer card.
 * @returns A CSS width percentage, clamped to 100%.
 */
function stampWidth(card: MerchantCard): string {
  const required: number = program.value?.stampsRequired ?? 0
  if (required <= 0) {
    return '0%'
  }
  return `${Math.min((card.stamps / required) * 100, 100)}%`
}

/**
 * Map a card status to a French label and an `app-badge` variant.
 * @param status - Raw status from the API (`active`, `completed`, `revoked`).
 * @returns The badge descriptor.
 */
function statusBadge(status: string): MerchantCardStatusBadge {
  if (status === 'completed') {
    return { label: 'Récompense prête', badgeClass: 'app-badge app-badge--success' }
  }
  if (status === 'revoked') {
    return { label: 'Révoquée', badgeClass: 'app-badge app-badge--danger' }
  }
  return { label: 'Active', badgeClass: 'app-badge' }
}

/**
 * Flash a transient confirmation, auto-dismissed after a short delay.
 * @param text - The message.
 * @param tone - Its tone.
 */
function showFlash(text: string, tone: MerchantFlashTone): void {
  flash.value = { text, tone }
  if (flashTimer !== null) {
    clearTimeout(flashTimer)
  }
  flashTimer = setTimeout((): void => {
    flash.value = null
  }, 2600)
}

/**
 * Replace a card in the list with its refreshed state after an action.
 * @param action - The action response carrying the card's new state.
 */
function replaceCard(action: MerchantCardAction): void {
  const next: MerchantCard = {
    serialNumber: action.serialNumber,
    stamps: action.stamps,
    status: action.status,
    holderName: action.holderName,
    lastStampedAt: action.lastStampedAt,
    addedToWalletAt: action.addedToWalletAt,
  }
  cards.value = cards.value.map(
    (card: MerchantCard): MerchantCard => (card.serialNumber === action.serialNumber ? next : card),
  )
}

/** Refresh the headline counters after an action (best-effort). */
async function refreshStats(): Promise<void> {
  const token: string | null = merchantStore.token
  if (!token) {
    return
  }
  try {
    stats.value = await MerchantService.getStats(token)
  } catch {
    // Keep the previous counters; the next navigation re-validates the session.
  }
}

/**
 * Add a stamp to a customer's card and reflect the result.
 * @param card - The card to stamp.
 */
async function stamp(card: MerchantCard): Promise<void> {
  const token: string | null = merchantStore.token
  if (!token) {
    return
  }
  actingSerial.value = card.serialNumber
  try {
    const action: MerchantCardAction = await MerchantService.stampCard(token, card.serialNumber)
    replaceCard(action)
    if (action.throttled) {
      showFlash("Carte déjà tamponnée à l'instant", 'warn')
    } else if (action.rewardReady) {
      showFlash('Récompense atteinte !', 'success')
    } else {
      showFlash('Tampon ajouté', 'success')
    }
    await refreshStats()
  } catch (error) {
    showFlash(error instanceof Error ? error.message : 'Action impossible', 'error')
  } finally {
    actingSerial.value = null
  }
}

/**
 * Hand over the reward and reset a completed card.
 * @param card - The card to redeem.
 */
async function redeem(card: MerchantCard): Promise<void> {
  const token: string | null = merchantStore.token
  if (!token) {
    return
  }
  actingSerial.value = card.serialNumber
  try {
    const action: MerchantCardAction = await MerchantService.redeemCard(token, card.serialNumber)
    replaceCard(action)
    showFlash('Récompense remise', 'success')
    await refreshStats()
  } catch (error) {
    showFlash(error instanceof Error ? error.message : 'Action impossible', 'error')
  } finally {
    actingSerial.value = null
  }
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

onUnmounted((): void => {
  if (flashTimer !== null) {
    clearTimeout(flashTimer)
  }
})
</script>
