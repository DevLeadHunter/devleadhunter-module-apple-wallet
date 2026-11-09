<template>
  <div
    class="relative overflow-hidden border-y border-[#e3dccd] py-3.5"
    :aria-label="t('walletLanding.ticker.ariaLabel')"
  >
    <div
      class="pointer-events-none absolute inset-y-0 left-0 z-10 w-16 bg-gradient-to-r from-[#f6f3ec] to-transparent md:w-32"
    ></div>
    <div
      class="pointer-events-none absolute inset-y-0 right-0 z-10 w-16 bg-gradient-to-l from-[#f6f3ec] to-transparent md:w-32"
    ></div>

    <div class="landing-ticker-track flex w-max items-center">
      <div v-for="copy in 2" :key="copy" class="flex items-center" :aria-hidden="copy === 2 ? 'true' : undefined">
        <span v-for="item in tickerItems" :key="`${copy}-${item}`" class="flex items-center">
          <span class="font-label px-6 text-sm whitespace-nowrap text-[#6b6355]">{{ item }}</span>
          <LandingAsterisk class="text-xs text-[#e8a33c]" />
        </span>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
/**
 * The wallet landing's infinite « business · city » marquee: the core's trades ticker, fed with the businesses that
 * hand out a loyalty card (the core's ticker reads its own trades and takes no other list).
 */
import type { ComputedRef } from 'vue'
import { computed } from 'vue'

const { t }: { t: (key: string, params?: Record<string, unknown>) => string } = useI18n()

/** Number of business examples in the `walletLanding.ticker` i18n namespace. */
const tickerItemCount: number = 8

/** « Business · city » examples scrolled in the ticker. */
const tickerItems: ComputedRef<string[]> = computed((): string[] =>
  Array.from({ length: tickerItemCount }, (_: unknown, index: number): string =>
    t(`walletLanding.ticker.item${index + 1}`),
  ),
)
</script>
