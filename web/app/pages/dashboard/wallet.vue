<template>
  <div class="space-y-5">
    <div>
      <p class="app-label flex items-center gap-2">
        <UIcon name="i-lucide-wallet" class="h-3.5 w-3.5 text-[var(--app-accent)]" />
        Apple Wallet
      </p>
      <h1 class="app-page-title mt-2">Carte de fidélité</h1>
      <p class="mt-1.5 max-w-2xl text-sm text-[var(--app-ink-soft)]">
        L'aperçu de la carte que le commerçant offre à ses clients — ses couleurs, ses tampons et son offre du moment.
        C'est ce que le client ajoute à son Wallet et voit sur son écran verrouillé.
      </p>
    </div>

    <div class="grid grid-cols-1 gap-5 @4xl:grid-cols-[minmax(0,1fr)_22rem]">
      <div class="app-card flex items-center justify-center overflow-hidden p-8" :style="stageStyle">
        <UiWalletCardPreview
          :organization-name="organizationName"
          :stamps="displayStamps"
          :stamps-required="stampsRequired"
          :reward-label="rewardLabel || null"
          :offer="offer || null"
          :background-color="selectedPalette.background"
          :foreground-color="selectedPalette.foreground"
          :label-color="selectedPalette.labelColor"
          serial-number="apercu-0001"
        />
      </div>

      <div class="app-card space-y-5 p-5">
        <div class="space-y-1.5">
          <label class="app-label" for="wallet-org">Nom du commerce</label>
          <input id="wallet-org" v-model="organizationName" class="input-field" type="text" maxlength="40" />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div class="space-y-1.5">
            <label class="app-label" for="wallet-required">Tampons requis</label>
            <input
              id="wallet-required"
              v-model.number="stampsRequired"
              class="input-field"
              type="number"
              min="1"
              max="12"
            />
          </div>
          <div class="space-y-1.5">
            <label class="app-label" for="wallet-stamps">Tampons acquis</label>
            <input
              id="wallet-stamps"
              v-model.number="stamps"
              class="input-field"
              type="number"
              min="0"
              :max="stampsRequired"
            />
          </div>
        </div>

        <input
          v-model.number="stamps"
          class="w-full accent-[var(--app-accent)]"
          type="range"
          min="0"
          :max="stampsRequired"
          aria-label="Tampons acquis"
        />

        <div class="space-y-1.5">
          <label class="app-label" for="wallet-reward">Récompense</label>
          <input id="wallet-reward" v-model="rewardLabel" class="input-field" type="text" maxlength="40" />
        </div>

        <div class="space-y-1.5">
          <label class="app-label" for="wallet-offer">Offre du moment (optionnel)</label>
          <input
            id="wallet-offer"
            v-model="offer"
            class="input-field"
            type="text"
            maxlength="40"
            placeholder="-10% sur ta prochaine visite"
          />
        </div>

        <div class="space-y-2">
          <span class="app-label">Ambiance</span>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="palette in palettes"
              :key="palette.id"
              type="button"
              class="flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors"
              :class="
                palette.id === selectedPaletteId
                  ? 'border-[var(--app-ink)] text-[var(--app-ink)]'
                  : 'border-[var(--app-line)] text-[var(--app-ink-soft)] hover:border-[var(--app-ink-soft)]'
              "
              @click="selectedPaletteId = palette.id"
            >
              <span
                class="h-3.5 w-3.5 rounded-full border border-black/10"
                :style="{ backgroundColor: palette.background }"
              />
              {{ palette.label }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import { computed, ref } from 'vue'
import type { WalletCardPalette } from '~/types/WalletPreviewPage'

/** Default palette, used as the fallback when no preset matches. */
const _FALLBACK_PALETTE: WalletCardPalette = {
  id: 'kebab',
  label: 'Kebab',
  background: 'rgb(23, 23, 23)',
  foreground: 'rgb(255, 255, 255)',
  labelColor: 'rgba(255, 255, 255, 0.62)',
}

/** Brand palette presets showcasing the card's dynamic colors. */
const palettes: WalletCardPalette[] = [
  _FALLBACK_PALETTE,
  {
    id: 'cafe',
    label: 'Café',
    background: 'rgb(60, 42, 33)',
    foreground: 'rgb(245, 236, 224)',
    labelColor: 'rgba(245, 236, 224, 0.6)',
  },
  {
    id: 'barber',
    label: 'Barbier',
    background: 'rgb(17, 24, 39)',
    foreground: 'rgb(233, 213, 160)',
    labelColor: 'rgba(233, 213, 160, 0.6)',
  },
  {
    id: 'institut',
    label: 'Institut',
    background: 'rgb(244, 232, 236)',
    foreground: 'rgb(60, 22, 44)',
    labelColor: 'rgba(60, 22, 44, 0.55)',
  },
  {
    id: 'primeur',
    label: 'Primeur',
    background: 'rgb(20, 83, 45)',
    foreground: 'rgb(240, 253, 244)',
    labelColor: 'rgba(240, 253, 244, 0.6)',
  },
]

const organizationName: Ref<string> = ref('Kebab Istanbul')
const stampsRequired: Ref<number> = ref(10)
const stamps: Ref<number> = ref(3)
const rewardLabel: Ref<string> = ref('1 kebab offert')
const offer: Ref<string> = ref('')
const selectedPaletteId: Ref<string> = ref('kebab')

/** The currently selected palette, falling back to the first preset. */
const selectedPalette: ComputedRef<WalletCardPalette> = computed(
  (): WalletCardPalette =>
    palettes.find((palette: WalletCardPalette) => palette.id === selectedPaletteId.value) ?? _FALLBACK_PALETTE,
)

/** Stamps clamped to the required count, so the card never shows an impossible tally. */
const displayStamps: ComputedRef<number> = computed((): number =>
  Math.min(Math.max(stamps.value, 0), Math.max(stampsRequired.value, 0)),
)

/** Soft stage backdrop tinted with the palette so the card sits on its own ground. */
const stageStyle: ComputedRef<Record<string, string>> = computed(
  (): Record<string, string> => ({
    background: `radial-gradient(120% 120% at 50% 0%, ${selectedPalette.value.background}22, transparent 70%)`,
  }),
)
</script>
