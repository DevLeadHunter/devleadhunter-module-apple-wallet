<template>
  <section id="merchant-dashboard" class="px-5 py-24 md:px-8 md:py-36">
    <div class="mx-auto max-w-6xl">
      <div class="grid items-center gap-14 lg:grid-cols-[1fr_1.15fr] lg:gap-20">
        <div>
          <p v-reveal class="landing-eyebrow">{{ $t('walletLanding.merchant.eyebrow') }}</p>
          <h2
            v-reveal="{ delay: 80 }"
            class="font-display mt-6 text-4xl leading-[1.06] font-semibold tracking-[-0.015em] text-[#1b1813] md:text-5xl"
          >
            {{ $t('walletLanding.merchant.title') }}
          </h2>
          <p v-reveal="{ delay: 160 }" class="mt-5 max-w-lg text-lg leading-relaxed text-[#6b6355]">
            {{ $t('walletLanding.merchant.description') }}
          </p>
          <ul class="mt-8 max-w-lg">
            <li
              v-for="(bulletKey, index) in bulletKeys"
              :key="bulletKey"
              v-reveal="{ delay: 220 + index * 70 }"
              class="flex items-start gap-3 border-t border-[#e3dccd] py-4 text-base text-[#1b1813]"
            >
              <i class="fa-solid fa-check mt-1 text-sm text-[#e8a33c]" aria-hidden="true"></i>
              {{ $t(bulletKey) }}
            </li>
          </ul>
        </div>

        <div v-reveal="{ delay: 150 }">
          <div class="landing-card landing-tilt mx-auto max-w-md p-6 md:p-7 lg:mx-0 lg:ml-auto">
            <div class="flex items-start justify-between gap-4">
              <p class="font-label text-[0.65rem] font-medium tracking-[0.18em] text-[#6b6355] uppercase">
                {{ $t('walletLanding.merchant.card.label') }}
              </p>
              <span
                class="font-display inline-flex h-7 w-7 items-center justify-center rounded-full bg-[#2b1e16] text-xs font-semibold text-[#fcfaf5]"
                aria-hidden="true"
              >
                {{ merchantInitial }}
              </span>
            </div>
            <p class="font-display mt-2 text-2xl font-semibold text-[#1b1813]">
              {{ $t('walletLanding.merchant.card.name') }}
            </p>

            <dl class="mt-5 grid grid-cols-3 gap-3">
              <div
                v-for="stat in stats"
                :key="stat.labelKey"
                class="rounded-xl border border-[#e3dccd] bg-[#f6f3ec] p-3"
              >
                <dd class="font-display text-xl font-semibold text-[#1b1813]">{{ $t(stat.valueKey) }}</dd>
                <dt class="font-label mt-1 text-[0.6rem] tracking-[0.1em] text-[#6b6355] uppercase">
                  {{ $t(stat.labelKey) }}
                </dt>
              </div>
            </dl>

            <ul class="mt-6 space-y-4 border-t border-dashed border-[#e3dccd] pt-5">
              <li
                v-for="row in clientRows"
                :key="row.nameKey"
                class="flex items-center justify-between gap-4 text-sm text-[#1b1813]"
              >
                <div class="min-w-0">
                  <p class="font-semibold">{{ $t(row.nameKey) }}</p>
                  <p class="font-label mt-0.5 text-[0.7rem] text-[#6b6355]">{{ $t(row.metaKey) }}</p>
                </div>
                <span
                  class="font-label shrink-0 rounded-full px-3 py-1 text-[0.65rem] font-semibold"
                  :class="
                    row.isRewardDue
                      ? 'bg-[#1b1813] text-[#fcfaf5]'
                      : 'border border-[#e3dccd] bg-[#fcfaf5] text-[#1b1813]'
                  "
                >
                  {{
                    $t(
                      row.isRewardDue
                        ? 'walletLanding.merchant.card.actionRedeem'
                        : 'walletLanding.merchant.card.actionStamp',
                    )
                  }}
                </span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script lang="ts" setup>
import type { LandingWalletMerchantStat, LandingWalletMerchantClientRow } from '~/types/LandingWalletMerchantDashboard'
import type { ComputedRef } from 'vue'
import { computed } from 'vue'

const { t }: { t: (key: string, params?: Record<string, unknown>) => string } = useI18n()

/** i18n keys of the four merchant bullets. */
const bulletKeys: string[] = [
  'walletLanding.merchant.bullet1',
  'walletLanding.merchant.bullet2',
  'walletLanding.merchant.bullet3',
  'walletLanding.merchant.bullet4',
]

/** The three headline stats of the mock merchant dashboard. */
const stats: LandingWalletMerchantStat[] = [
  { valueKey: 'walletLanding.merchant.card.stat1Value', labelKey: 'walletLanding.merchant.card.stat1Label' },
  { valueKey: 'walletLanding.merchant.card.stat2Value', labelKey: 'walletLanding.merchant.card.stat2Label' },
  { valueKey: 'walletLanding.merchant.card.stat3Value', labelKey: 'walletLanding.merchant.card.stat3Label' },
]

/** The three mock client rows (the reward-due row shows the redeem action). */
const clientRows: LandingWalletMerchantClientRow[] = [
  {
    nameKey: 'walletLanding.merchant.card.client1Name',
    metaKey: 'walletLanding.merchant.card.client1Meta',
    isRewardDue: false,
  },
  {
    nameKey: 'walletLanding.merchant.card.client2Name',
    metaKey: 'walletLanding.merchant.card.client2Meta',
    isRewardDue: true,
  },
  {
    nameKey: 'walletLanding.merchant.card.client3Name',
    metaKey: 'walletLanding.merchant.card.client3Meta',
    isRewardDue: false,
  },
]

/** First letter of the mock merchant name (avatar fallback). */
const merchantInitial: ComputedRef<string> = computed((): string =>
  t('walletLanding.merchant.card.name').trim().charAt(0).toUpperCase(),
)
</script>
