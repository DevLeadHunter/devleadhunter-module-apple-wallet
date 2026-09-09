<template>
  <div v-if="props.actIndex === 0" v-bind="$attrs" class="landing-card p-6 md:p-7">
    <p class="font-label text-[0.65rem] font-medium tracking-[0.18em] text-[#6b6355] uppercase">
      {{ $t('walletLanding.story.visual.programLabel') }}
    </p>
    <p class="font-display mt-3 text-2xl font-semibold text-[#1b1813] md:text-3xl">
      {{ $t('walletLanding.story.visual.programName') }}
    </p>

    <dl class="mt-6 space-y-4 border-t border-dashed border-[#e3dccd] pt-5">
      <div class="flex items-center justify-between gap-4">
        <dt class="font-label text-[0.7rem] tracking-[0.14em] text-[#6b6355] uppercase">
          {{ $t('walletLanding.story.visual.programColorsLabel') }}
        </dt>
        <dd class="flex items-center gap-1.5" aria-hidden="true">
          <span class="h-4 w-4 rounded-full border border-[#e3dccd] bg-[#2b1e16]"></span>
          <span class="h-4 w-4 rounded-full border border-[#e3dccd] bg-[#e8a33c]"></span>
          <span class="h-4 w-4 rounded-full border border-[#e3dccd] bg-[#fcfaf5]"></span>
        </dd>
      </div>
      <div class="flex items-center justify-between gap-4">
        <dt class="font-label text-[0.7rem] tracking-[0.14em] text-[#6b6355] uppercase">
          {{ $t('walletLanding.story.visual.programGoalLabel') }}
        </dt>
        <dd class="text-sm font-semibold text-[#1b1813]">
          {{ $t('walletLanding.story.visual.programGoalValue') }}
        </dd>
      </div>
      <div class="flex items-center justify-between gap-4">
        <dt class="font-label text-[0.7rem] tracking-[0.14em] text-[#6b6355] uppercase">
          {{ $t('walletLanding.story.visual.programRewardLabel') }}
        </dt>
        <dd class="text-sm font-semibold text-[#1b1813]">
          {{ $t('walletLanding.story.visual.programRewardValue') }}
        </dd>
      </div>
    </dl>

    <p
      class="font-label mt-6 inline-flex items-center gap-1.5 rounded-full border border-[#e3dccd] bg-[#f6f3ec] px-2.5 py-1 text-[0.65rem] text-[#6b6355]"
    >
      <i class="fa-solid fa-check text-[0.55rem] text-[#2f7d4e]" aria-hidden="true"></i>
      {{ $t('walletLanding.story.visual.programChip') }}
    </p>
  </div>

  <div v-else-if="props.actIndex === 1" v-bind="$attrs" class="landing-card mx-auto max-w-sm p-6 text-center md:p-7">
    <p class="font-label text-[0.65rem] font-medium tracking-[0.18em] text-[#6b6355] uppercase">
      {{ $t('walletLanding.story.visual.counterLabel') }}
    </p>
    <svg
      class="mx-auto mt-5 h-36 w-36 text-[#1b1813]"
      :viewBox="`0 0 ${qrSize} ${qrSize}`"
      fill="currentColor"
      role="img"
      :aria-label="$t('walletLanding.story.visual.counterHeadline')"
    >
      <rect v-for="cell in qrCells" :key="`${cell.x}-${cell.y}`" :x="cell.x" :y="cell.y" width="1" height="1" />
    </svg>
    <p class="font-display mt-5 text-xl font-semibold text-[#1b1813]">
      {{ $t('walletLanding.story.visual.counterHeadline') }}
    </p>
    <p class="font-label mt-2 text-[0.7rem] tracking-[0.14em] text-[#6b6355] uppercase">
      {{ $t('walletLanding.story.visual.counterHint') }}
    </p>
    <img
      src="/add-to-apple-wallet.svg"
      :alt="$t('walletLanding.story.visual.counterBadgeAlt')"
      class="mx-auto mt-5 h-11"
    />
  </div>

  <div v-else-if="props.actIndex === 2" v-bind="$attrs" class="relative mx-auto max-w-xs sm:max-w-sm">
    <UiWalletCardPreview
      :organization-name="$t('walletLanding.story.visual.programName')"
      :stamps="9"
      :stamps-required="10"
      :reward-label="$t('walletLanding.story.visual.programRewardValue')"
      background-color="rgb(43, 30, 22)"
    />
    <span
      class="font-label absolute -top-3 -right-2 rotate-2 rounded-full bg-[#2f7d4e] px-3 py-1 text-[0.65rem] font-semibold text-[#fcfaf5]"
    >
      {{ $t('walletLanding.story.visual.stampChip') }}
    </span>
  </div>

  <div v-else v-bind="$attrs" class="mx-auto max-w-sm rounded-[1.5rem] bg-[#1b1813] p-6 md:p-7">
    <p class="font-label text-[0.65rem] font-medium tracking-[0.18em] text-[#f6f3ec]/50 uppercase">
      {{ $t('walletLanding.story.visual.notifLabel') }}
    </p>
    <div class="mt-5 rounded-2xl bg-white/10 p-4">
      <div class="flex items-center justify-between gap-3">
        <p
          class="font-label inline-flex items-center gap-1.5 text-[0.6rem] tracking-[0.14em] text-[#f6f3ec]/60 uppercase"
        >
          <i class="fa-solid fa-wallet text-[0.6rem]" aria-hidden="true"></i>
          {{ $t('walletLanding.story.visual.notifSource') }}
        </p>
        <p class="font-label text-[0.6rem] text-[#f6f3ec]/50">
          {{ $t('walletLanding.story.visual.notifMeta') }}
        </p>
      </div>
      <p class="mt-2 text-sm font-semibold text-[#fcfaf5]">
        {{ $t('walletLanding.story.visual.notifTitle') }}
      </p>
      <p class="mt-1 text-sm leading-relaxed text-[#f6f3ec]/75">
        {{ $t('walletLanding.story.visual.notifBody') }}
      </p>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { PropType } from 'vue'
import type { LandingWalletStoryVisualProps } from '~/types/LandingWalletStoryVisual'
import type { LandingStoryActIndex } from '~/types/LandingStoryVisual'
import type { WalletCardQrCell } from '~/types/UiWalletCardPreview'

// A comment between two v-if roots desyncs SSR/client attribute inheritance.
defineOptions({ inheritAttrs: false })

const props: LandingWalletStoryVisualProps = defineProps({
  actIndex: {
    type: Number as PropType<LandingStoryActIndex>,
    required: true,
  },
})

const qrSize: number = 21
const qrFinder: number = 7

/**
 * Whether a module belongs to one of the three QR finder squares.
 * @param x - Module column.
 * @param y - Module row.
 * @returns True when the module is inside a finder area.
 */
function isInFinderArea(x: number, y: number): boolean {
  const span: number = qrFinder + 1
  const end: number = qrSize - span
  return (x < span && y < span) || (x >= end && y < span) || (x < span && y >= end)
}

/**
 * Whether a finder-square module is filled (outer ring + solid core).
 * @param localX - Column relative to the finder origin.
 * @param localY - Row relative to the finder origin.
 * @returns True when the module is drawn.
 */
function isFinderModuleFilled(localX: number, localY: number): boolean {
  const onRing: boolean = localX === 0 || localY === 0 || localX === qrFinder - 1 || localY === qrFinder - 1
  const inCore: boolean = localX >= 2 && localX <= 4 && localY >= 2 && localY <= 4
  return onRing || inCore
}

/** Deterministic faux-QR modules: three finder squares + hashed data cells. */
const qrCells: WalletCardQrCell[] = ((): WalletCardQrCell[] => {
  const cells: WalletCardQrCell[] = []
  const finderOrigins: WalletCardQrCell[] = [
    { x: 0, y: 0 },
    { x: qrSize - qrFinder, y: 0 },
    { x: 0, y: qrSize - qrFinder },
  ]
  for (const origin of finderOrigins) {
    for (let localY: number = 0; localY < qrFinder; localY += 1) {
      for (let localX: number = 0; localX < qrFinder; localX += 1) {
        if (isFinderModuleFilled(localX, localY)) {
          cells.push({ x: origin.x + localX, y: origin.y + localY })
        }
      }
    }
  }
  for (let y: number = 0; y < qrSize; y += 1) {
    for (let x: number = 0; x < qrSize; x += 1) {
      if (!isInFinderArea(x, y) && (x * 31 + y * 17 + x * y) % 5 < 2) {
        cells.push({ x, y })
      }
    }
  }
  return cells
})()
</script>
