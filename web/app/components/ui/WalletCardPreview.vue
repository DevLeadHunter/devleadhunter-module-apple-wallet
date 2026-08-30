<template>
  <div class="wallet-card" :style="{ backgroundColor: background, color: foreground }">
    <div class="wallet-card__sheen" aria-hidden="true" />

    <header class="wallet-card__header">
      <div class="wallet-card__brand">
        <img v-if="logoUrl" :src="logoUrl" :alt="organizationName" class="wallet-card__logo" />
        <span v-else class="wallet-card__logo wallet-card__logo--fallback" :style="{ borderColor: label }">
          {{ initial }}
        </span>
        <span class="wallet-card__org">{{ organizationName }}</span>
      </div>
      <span class="wallet-card__kind" :style="{ color: label }">Carte de fidélité</span>
    </header>

    <div class="wallet-card__primary">
      <span class="wallet-card__field-label" :style="{ color: label }">Tampons</span>
      <span class="wallet-card__field-value">{{ stamps }} / {{ stampsRequired }}</span>
    </div>

    <div class="wallet-card__stamps">
      <span
        v-for="slot in stampCount"
        :key="slot"
        class="wallet-card__stamp"
        :class="{ 'wallet-card__stamp--filled': slot <= stamps }"
        :style="stampStyle(slot)"
      />
    </div>

    <div v-if="rewardLabel || offer" class="wallet-card__secondary">
      <div v-if="rewardLabel" class="wallet-card__field">
        <span class="wallet-card__field-label" :style="{ color: label }">Récompense</span>
        <span class="wallet-card__field-text">{{ rewardLabel }}</span>
      </div>
      <div v-if="offer" class="wallet-card__field wallet-card__field--end">
        <span class="wallet-card__field-label" :style="{ color: label }">Offre</span>
        <span class="wallet-card__field-text">{{ offer }}</span>
      </div>
    </div>

    <div class="wallet-card__barcode">
      <svg class="wallet-card__qr" :viewBox="`0 0 ${qrSize} ${qrSize}`" role="img" aria-label="QR code de la carte">
        <rect v-for="cell in qrCells" :key="`${cell.x}-${cell.y}`" :x="cell.x" :y="cell.y" width="1" height="1" />
      </svg>
      <span class="wallet-card__serial">{{ serialLabel }}</span>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, PropType } from 'vue'
import { computed } from 'vue'
import type { UiWalletCardPreviewProps, WalletCardQrCell } from '~/types/UiWalletCardPreview'

/** Faithful preview of a merchant's Apple Wallet loyalty store card. */
const props: UiWalletCardPreviewProps = defineProps({
  organizationName: {
    type: String,
    required: true,
  },
  stamps: {
    type: Number,
    required: true,
  },
  stampsRequired: {
    type: Number,
    required: true,
  },
  rewardLabel: {
    type: String as PropType<string | null>,
    default: null,
  },
  offer: {
    type: String as PropType<string | null>,
    default: null,
  },
  logoUrl: {
    type: String as PropType<string | null>,
    default: null,
  },
  backgroundColor: {
    type: String as PropType<string | null>,
    default: null,
  },
  foregroundColor: {
    type: String as PropType<string | null>,
    default: null,
  },
  labelColor: {
    type: String as PropType<string | null>,
    default: null,
  },
  serialNumber: {
    type: String as PropType<string | null>,
    default: null,
  },
})

const _DEFAULT_BACKGROUND: string = 'rgb(23, 23, 23)'
const _DEFAULT_FOREGROUND: string = 'rgb(255, 255, 255)'
const _DEFAULT_LABEL: string = 'rgba(255, 255, 255, 0.62)'
const qrSize: number = 21
const qrFinder: number = 7

/** Card background color (brand, with a dark default). */
const background: ComputedRef<string> = computed((): string => props.backgroundColor?.trim() || _DEFAULT_BACKGROUND)

/** Text color (brand foreground, with a light default). */
const foreground: ComputedRef<string> = computed((): string => props.foregroundColor?.trim() || _DEFAULT_FOREGROUND)

/** Label color (brand label, with a muted default). */
const label: ComputedRef<string> = computed((): string => props.labelColor?.trim() || _DEFAULT_LABEL)

/** First letter of the merchant name, shown when no logo is set. */
const initial: ComputedRef<string> = computed(
  (): string => props.organizationName.trim().charAt(0).toUpperCase() || '?',
)

/** Number of stamp slots to render (guarded to a sensible range). */
const stampCount: ComputedRef<number> = computed((): number => Math.min(Math.max(props.stampsRequired, 0), 12))

/** Serial shown under the barcode, mimicking the real pass. */
const serialLabel: ComputedRef<string> = computed((): string => props.serialNumber?.trim() || 'apercu-0001')

/** Filled modules of the faux QR for the current serial. */
const qrCells: ComputedRef<WalletCardQrCell[]> = computed((): WalletCardQrCell[] => buildQrCells(serialLabel.value))

/**
 * Build the filled modules of a faux QR: three finder patterns plus a stable
 * scatter derived from the serial, so the preview reads as a real barcode.
 *
 * @param seed - String the scatter is derived from (the card serial).
 * @returns The filled grid cells.
 */
function buildQrCells(seed: string): WalletCardQrCell[] {
  let hash: number = 0
  for (let index: number = 0; index < seed.length; index += 1) {
    hash = (hash * 31 + seed.charCodeAt(index)) % 2147483647
  }
  const cells: WalletCardQrCell[] = []
  for (let y: number = 0; y < qrSize; y += 1) {
    for (let x: number = 0; x < qrSize; x += 1) {
      const inFinder: boolean =
        (x < qrFinder && y < qrFinder) ||
        (x >= qrSize - qrFinder && y < qrFinder) ||
        (x < qrFinder && y >= qrSize - qrFinder)
      if (inFinder) {
        const localX: number = x < qrFinder ? x : x - (qrSize - qrFinder)
        const localY: number = y < qrFinder ? y : y - (qrSize - qrFinder)
        const onRing: boolean = localX === 0 || localX === 6 || localY === 0 || localY === 6
        const inCore: boolean = localX >= 2 && localX <= 4 && localY >= 2 && localY <= 4
        if (onRing || inCore) {
          cells.push({ x, y })
        }
        continue
      }
      if ((hash + x * 7 + y * 13 + x * y) % 3 === 0) {
        cells.push({ x, y })
      }
    }
  }
  return cells
}

/**
 * Inline style for one stamp dot — filled dots use the foreground color, empty
 * ones show a faint ring in the label color.
 *
 * @param slot - 1-based index of the stamp slot.
 * @returns The style bindings for the dot.
 */
function stampStyle(slot: number): Record<string, string> {
  if (slot <= props.stamps) {
    return { backgroundColor: foreground.value, borderColor: foreground.value }
  }
  return { borderColor: label.value }
}
</script>

<style scoped>
.wallet-card {
  position: relative;
  width: 100%;
  max-width: 20rem;
  border-radius: 1.25rem;
  padding: 1.15rem 1.25rem 1.35rem;
  box-shadow:
    0 1px 1px rgba(0, 0, 0, 0.14),
    0 18px 40px -18px rgba(0, 0, 0, 0.55);
  overflow: hidden;
  font-family: 'Inter', sans-serif;
}

/* Subtle top sheen for depth, independent of the brand color. */
.wallet-card__sheen {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(0, 0, 0, 0) 42%, rgba(0, 0, 0, 0.12));
  pointer-events: none;
}

.wallet-card > *:not(.wallet-card__sheen) {
  position: relative;
}

.wallet-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.wallet-card__brand {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  min-width: 0;
}

.wallet-card__logo {
  width: 1.6rem;
  height: 1.6rem;
  border-radius: 0.5rem;
  object-fit: cover;
  flex-shrink: 0;
}

.wallet-card__logo--fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid;
  font-size: 0.85rem;
  font-weight: 700;
}

.wallet-card__org {
  font-size: 0.9rem;
  font-weight: 600;
  letter-spacing: 0.01em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wallet-card__kind {
  font-size: 0.62rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  white-space: nowrap;
}

.wallet-card__primary {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  margin-top: 1.4rem;
}

.wallet-card__field-label {
  font-size: 0.6rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.09em;
}

.wallet-card__field-value {
  font-size: 1.9rem;
  font-weight: 700;
  line-height: 1.05;
  font-variant-numeric: tabular-nums;
}

.wallet-card__stamps {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin-top: 0.85rem;
}

.wallet-card__stamp {
  width: 0.85rem;
  height: 0.85rem;
  border-radius: 999px;
  border: 1.5px solid;
  box-sizing: border-box;
}

.wallet-card__secondary {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  margin-top: 1.25rem;
}

.wallet-card__field {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  min-width: 0;
}

.wallet-card__field--end {
  text-align: right;
}

.wallet-card__field-text {
  font-size: 0.8rem;
  font-weight: 600;
}

.wallet-card__barcode {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
  margin-top: 1.35rem;
  padding: 0.7rem;
  border-radius: 0.75rem;
  background: #ffffff;
}

.wallet-card__qr {
  width: 5.2rem;
  height: 5.2rem;
  shape-rendering: crispEdges;
  fill: #05070d;
}

.wallet-card__serial {
  font-size: 0.6rem;
  font-weight: 500;
  letter-spacing: 0.04em;
  color: #6b7280;
  font-variant-numeric: tabular-nums;
}
</style>
