<template>
  <section id="notifications" class="px-5 py-24 md:px-8 md:py-36">
    <div class="mx-auto max-w-6xl">
      <div class="grid items-center gap-14 lg:grid-cols-[1.15fr_1fr] lg:gap-20">
        <div v-reveal="{ delay: 150 }" class="order-2 lg:order-1">
          <div class="mx-auto max-w-sm lg:mx-0">
            <p class="font-label text-[0.65rem] font-medium tracking-[0.18em] text-[#6b6355] uppercase">
              {{ $t('walletLanding.notifications.card.label') }}
            </p>
            <div
              class="landing-tilt mt-4 rounded-[2rem] bg-gradient-to-b from-[#1b1813] to-[#262119] p-6 pb-10 md:p-7 md:pb-12"
            >
              <p class="font-display text-center text-6xl font-semibold text-[#fcfaf5]">
                {{ $t('walletLanding.notifications.card.time') }}
              </p>
              <p class="mt-1 text-center text-sm text-[#f6f3ec]/60">
                {{ $t('walletLanding.notifications.card.date') }}
              </p>

              <div class="mt-8 space-y-3">
                <div class="rounded-2xl bg-white/10 p-4">
                  <div class="flex items-center justify-between gap-3">
                    <p
                      class="font-label inline-flex items-center gap-1.5 text-[0.6rem] tracking-[0.14em] text-[#f6f3ec]/60 uppercase"
                    >
                      <i class="fa-solid fa-wallet text-[0.6rem]" aria-hidden="true"></i>
                      {{ $t('walletLanding.notifications.card.notifSource') }}
                    </p>
                    <p class="font-label text-[0.6rem] text-[#f6f3ec]/50">
                      {{ $t('walletLanding.notifications.card.notif1Meta') }}
                    </p>
                  </div>
                  <p class="mt-2 text-sm font-semibold text-[#fcfaf5]">
                    {{ $t('walletLanding.notifications.card.notif1Title') }}
                  </p>
                  <p class="mt-1 text-sm leading-relaxed text-[#f6f3ec]/75">
                    {{ $t('walletLanding.notifications.card.notif1Body') }}
                  </p>
                </div>

                <div class="rounded-2xl bg-white/10 p-4 opacity-70">
                  <div class="flex items-center justify-between gap-3">
                    <p
                      class="font-label inline-flex items-center gap-1.5 text-[0.6rem] tracking-[0.14em] text-[#f6f3ec]/60 uppercase"
                    >
                      <i class="fa-solid fa-wallet text-[0.6rem]" aria-hidden="true"></i>
                      {{ $t('walletLanding.notifications.card.notifSource') }}
                    </p>
                    <p class="font-label text-[0.6rem] text-[#f6f3ec]/50">
                      {{ $t('walletLanding.notifications.card.notif2Meta') }}
                    </p>
                  </div>
                  <p class="mt-2 text-sm font-semibold text-[#fcfaf5]">
                    {{ $t('walletLanding.notifications.card.notif2Title') }}
                  </p>
                  <p class="mt-1 text-sm leading-relaxed text-[#f6f3ec]/75">
                    {{ $t('walletLanding.notifications.card.notif2Body') }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="order-1 lg:order-2">
          <p v-reveal class="landing-eyebrow">{{ $t('walletLanding.notifications.eyebrow') }}</p>
          <h2
            v-reveal="{ delay: 80 }"
            class="font-display mt-6 text-4xl leading-[1.06] font-semibold tracking-[-0.015em] text-[#1b1813] md:text-5xl"
          >
            {{ $t('walletLanding.notifications.title') }}
          </h2>
          <p v-reveal="{ delay: 160 }" class="mt-5 max-w-lg text-lg leading-relaxed text-[#6b6355]">
            {{ $t('walletLanding.notifications.description') }}
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
      </div>
    </div>
  </section>
</template>

<script lang="ts" setup>
/** i18n keys of the four notification bullets. */
const bulletKeys: string[] = [
  'walletLanding.notifications.bullet1',
  'walletLanding.notifications.bullet2',
  'walletLanding.notifications.bullet3',
  'walletLanding.notifications.bullet4',
]
</script>
