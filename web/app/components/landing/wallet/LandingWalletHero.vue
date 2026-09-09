<template>
  <section class="relative overflow-hidden">
    <div class="mx-auto max-w-6xl px-5 pt-20 pb-16 md:px-8 md:pt-28 md:pb-24">
      <div class="grid items-center gap-14 lg:grid-cols-[1.15fr_1fr] lg:gap-20">
        <div>
          <p class="landing-eyebrow hero-rise" :style="{ animationDelay: '0ms' }">
            {{ $t('walletLanding.hero.eyebrow') }}
          </p>

          <h1
            class="hero-rise font-display mt-7 max-w-4xl text-[2.75rem] leading-[1.04] font-semibold tracking-[-0.02em] text-[#1b1813] md:text-6xl"
            :style="{ animationDelay: '90ms' }"
          >
            {{ $t('walletLanding.hero.titleStart') }}
            <em class="font-medium text-[#1b1813] italic">{{ $t('walletLanding.hero.titleAccent') }}</em
            ><span class="text-[#e8a33c]" aria-hidden="true">.</span>
          </h1>

          <p
            class="hero-rise mt-7 max-w-xl text-lg leading-relaxed text-[#6b6355] md:text-xl"
            :style="{ animationDelay: '180ms' }"
          >
            {{ $t('walletLanding.hero.subtitle') }}
          </p>

          <div
            class="hero-rise mt-10 flex flex-col items-stretch gap-3 sm:flex-row sm:items-center"
            :style="{ animationDelay: '270ms' }"
          >
            <NuxtLink
              :to="localePath('/signup')"
              class="landing-btn-primary"
              @click="track('site_cta_click', { location: 'wallet_hero', label: 'signup' })"
            >
              {{ $t('walletLanding.hero.ctaPrimary') }}
              <i class="fa-solid fa-arrow-right text-sm" aria-hidden="true"></i>
            </NuxtLink>
            <button type="button" class="landing-btn-ghost" @click="handleDiscover">
              {{ $t('walletLanding.hero.ctaSecondary') }}
            </button>
          </div>

          <ul
            class="hero-rise mt-9 flex flex-wrap items-center gap-x-6 gap-y-4 sm:gap-y-2"
            :style="{ animationDelay: '360ms' }"
          >
            <li
              v-for="trustKey in trustKeys"
              :key="trustKey"
              class="font-label inline-flex items-center gap-2 text-xs tracking-wide text-[#6b6355] uppercase"
            >
              <i class="fa-solid fa-check text-[0.65rem] text-[#e8a33c]" aria-hidden="true"></i>
              {{ $t(trustKey) }}
            </li>
          </ul>
        </div>

        <div class="hero-rise flex justify-center lg:justify-end" :style="{ animationDelay: '360ms' }">
          <div class="w-full max-w-xs rotate-2 transition-transform duration-500 hover:rotate-0 sm:max-w-sm">
            <UiWalletCardPreview
              :organization-name="$t('walletLanding.hero.card.organization')"
              :stamps="7"
              :stamps-required="10"
              :reward-label="$t('walletLanding.hero.card.reward')"
              :offer="$t('walletLanding.hero.card.offer')"
              background-color="rgb(43, 30, 22)"
            />
          </div>
        </div>
      </div>
    </div>

    <div class="hero-rise" :style="{ animationDelay: '450ms' }">
      <LandingTradesTicker key-prefix="walletLanding.ticker" :item-count="8" />
    </div>
  </section>
</template>

<script lang="ts" setup>
const emit: {
  (e: 'discover'): void
} = defineEmits<{
  (e: 'discover'): void
}>()

const localePath: ReturnType<typeof useLocalePath> = useLocalePath()
const { track }: { track: (event: string, properties?: Record<string, unknown> | undefined) => void } =
  useSiteTracking()

/** i18n keys of the three trust markers under the CTAs. */
const trustKeys: string[] = ['walletLanding.hero.trust1', 'walletLanding.hero.trust2', 'walletLanding.hero.trust3']

/**
 * Track the secondary hero CTA, then emit the discover event.
 */
function handleDiscover(): void {
  track('site_cta_click', { location: 'wallet_hero', label: 'discover' })
  emit('discover')
}
</script>

<style scoped>
/* Staggered editorial entrance on page load */
.hero-rise {
  opacity: 0;
  transform: translateY(22px);
  animation: hero-rise 0.9s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

@keyframes hero-rise {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .hero-rise {
    animation: none;
    opacity: 1;
    transform: none;
  }
}
</style>
