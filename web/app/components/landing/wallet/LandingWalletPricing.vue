<template>
  <section id="pricing" class="px-5 py-24 md:px-8 md:py-36">
    <div class="mx-auto max-w-6xl">
      <div class="mx-auto max-w-2xl text-center">
        <p v-reveal class="landing-eyebrow">{{ $t('walletLanding.pricing.eyebrow') }}</p>
        <h2
          v-reveal="{ delay: 80 }"
          class="font-display mt-6 text-4xl leading-[1.06] font-semibold tracking-[-0.015em] text-[#1b1813] md:text-5xl"
        >
          {{ $t('walletLanding.pricing.title') }}
        </h2>
        <p v-reveal="{ delay: 160 }" class="mt-5 text-lg leading-relaxed text-[#6b6355]">
          {{ $t('walletLanding.pricing.subtitle') }}
        </p>
      </div>

      <div
        v-reveal="{ delay: 220 }"
        class="landing-card mx-auto mt-14 max-w-3xl overflow-hidden md:grid md:grid-cols-2"
      >
        <div class="flex flex-col justify-between gap-10 p-8 md:border-r md:border-[#e3dccd] md:p-10">
          <blockquote class="font-display text-2xl leading-snug font-medium text-[#1b1813] italic md:text-[1.7rem]">
            «&nbsp;{{ $t('walletLanding.pricing.roiNote') }}&nbsp;»
          </blockquote>
          <div>
            <NuxtLink
              :to="localePath('/signup')"
              class="landing-btn-primary w-full text-center md:w-auto"
              @click="track('site_cta_click', { location: 'wallet_pricing', label: 'signup' })"
            >
              {{ $t('walletLanding.pricing.cta') }}
            </NuxtLink>
          </div>
        </div>

        <div class="bg-[#f6f3ec]/60 p-8 md:p-10">
          <dl>
            <div
              v-for="(stat, index) in pricingStats"
              :key="stat.labelKey"
              class="border-dashed border-[#e3dccd] py-5 first:pt-0 last:pb-0"
              :class="index < pricingStats.length - 1 ? 'border-b' : ''"
            >
              <dt class="font-label order-2 text-[0.7rem] tracking-[0.14em] text-[#6b6355] uppercase">
                {{ $t(stat.labelKey) }}
              </dt>
              <dd class="font-display order-1 text-3xl font-semibold text-[#1b1813]">{{ $t(stat.valueKey) }}</dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  </section>
</template>

<script lang="ts" setup>
import type { LandingWalletPricingStat } from '~/types/LandingWalletPricing'

const localePath: ReturnType<typeof useLocalePath> = useLocalePath()
const { track }: { track: (event: string, properties?: Record<string, unknown> | undefined) => void } =
  useSiteTracking()

/** The four static metrics of the subscription offer. */
const pricingStats: LandingWalletPricingStat[] = [
  { valueKey: 'walletLanding.pricing.stat1Value', labelKey: 'walletLanding.pricing.stat1Label' },
  { valueKey: 'walletLanding.pricing.stat2Value', labelKey: 'walletLanding.pricing.stat2Label' },
  { valueKey: 'walletLanding.pricing.stat3Value', labelKey: 'walletLanding.pricing.stat3Label' },
  { valueKey: 'walletLanding.pricing.stat4Value', labelKey: 'walletLanding.pricing.stat4Label' },
]
</script>
