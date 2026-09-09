<template>
  <div>
    <LandingWalletHero @discover="scrollToSection('#how-it-works')" />
    <LandingWalletStory />
    <LandingSectionDivider />
    <LandingWalletNotifications />
    <LandingSectionDivider />
    <LandingWalletMerchantDashboard />
    <LandingWalletFeatureGrid />
    <LandingWalletPricing />
    <LandingSectionDivider />
    <LandingWalletFaq />
    <LandingWalletFinalCta />
  </div>
</template>

<script lang="ts" setup>
/**
 * Apple Wallet loyalty module page — the landing's editorial marketing layout applied to the module.
 */
definePageMeta({
  layout: 'marketing',
  // Desktop app: skip the marketing pages and go to the dashboard (web keeps them).
  middleware: ['desktop-redirect'],
})

const { t }: { t: (key: string, params?: Record<string, unknown>) => string } = useI18n()
const scrollToSection: (selector: string) => void = useScrollToSection()

useSectionViewTracking({ page: 'apple_wallet' })

useHead(() => ({
  title: t('walletLanding.seo.title'),
  meta: [
    { name: 'description', content: t('walletLanding.seo.description') },
    { property: 'og:title', content: t('walletLanding.seo.title') },
    { property: 'og:description', content: t('walletLanding.seo.description') },
    { property: 'og:type', content: 'website' },
    { name: 'twitter:title', content: t('walletLanding.seo.title') },
    { name: 'twitter:description', content: t('walletLanding.seo.description') },
  ],
}))
</script>
