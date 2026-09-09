<template>
  <section class="px-5 pb-24 md:px-8 md:pb-28">
    <div
      v-reveal
      class="relative mx-auto max-w-6xl overflow-hidden rounded-[2rem] bg-[#1b1813] px-6 py-20 text-center md:py-28"
    >
      <LandingAsterisk class="pointer-events-none absolute -top-14 -left-10 text-[9rem] text-[#e8a33c]/20" />
      <LandingAsterisk
        class="pointer-events-none absolute -right-12 -bottom-16 rotate-12 text-[11rem] text-[#e8a33c]/15"
      />

      <div class="relative">
        <h2
          class="font-display mx-auto max-w-3xl text-4xl leading-[1.05] font-semibold tracking-[-0.015em] text-[#fcfaf5] md:text-6xl"
        >
          {{ $t('walletLanding.finalCta.title') }}
        </h2>
        <p class="mx-auto mt-6 max-w-xl text-lg leading-relaxed text-[#f6f3ec]/75">
          {{ $t('walletLanding.finalCta.subtitle') }}
        </p>
        <NuxtLink
          :to="localePath('/signup')"
          class="mt-10 inline-flex items-center gap-2.5 rounded-full bg-[#fcfaf5] px-8 py-4 text-base font-semibold text-[#1b1813] transition-all duration-300 hover:-translate-y-0.5 hover:bg-white"
          @click="track('site_cta_click', { location: 'wallet_final_cta', label: 'signup' })"
        >
          {{ $t('walletLanding.finalCta.cta') }}
          <i class="fa-solid fa-arrow-right text-sm" aria-hidden="true"></i>
        </NuxtLink>
        <p class="font-label mt-6 text-xs tracking-[0.18em] text-[#f6f3ec]/60 uppercase">
          {{ $t('walletLanding.finalCta.note') }}
        </p>
      </div>
    </div>
  </section>
</template>

<script lang="ts" setup>
const localePath: ReturnType<typeof useLocalePath> = useLocalePath()
const { track }: { track: (event: string, properties?: Record<string, unknown> | undefined) => void } =
  useSiteTracking()
</script>
