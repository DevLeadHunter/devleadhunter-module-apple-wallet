<template>
  <section id="faq" class="px-5 py-24 md:px-8 md:py-36">
    <div class="mx-auto max-w-3xl">
      <p v-reveal class="landing-eyebrow">{{ $t('walletLanding.faq.eyebrow') }}</p>
      <h2
        v-reveal="{ delay: 80 }"
        class="font-display mt-6 text-4xl leading-[1.06] font-semibold tracking-[-0.015em] text-[#1b1813] md:text-5xl"
      >
        {{ $t('walletLanding.faq.title') }}
      </h2>

      <div class="mt-10">
        <div
          v-for="(entry, index) in faqEntries"
          :key="entry.questionKey"
          v-reveal="{ delay: index * 40 }"
          class="border-b border-[#e3dccd]"
        >
          <button
            type="button"
            class="flex w-full items-center justify-between gap-6 py-6 text-left"
            :aria-expanded="openIndex === index"
            :aria-controls="`wallet-faq-answer-${index}`"
            @click="toggleEntry(index)"
          >
            <span class="font-display text-lg font-medium text-[#1b1813] md:text-xl">
              {{ $t(entry.questionKey) }}
            </span>
            <i
              class="fa-solid fa-plus shrink-0 text-sm text-[#1b1813] transition-transform duration-300"
              :class="openIndex === index ? 'rotate-45' : ''"
              aria-hidden="true"
            ></i>
          </button>
          <div
            :id="`wallet-faq-answer-${index}`"
            class="grid transition-[grid-template-rows] duration-300 ease-out"
            :class="openIndex === index ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'"
          >
            <div class="overflow-hidden">
              <p class="max-w-2xl pb-6 text-base leading-relaxed text-[#6b6355]">
                {{ $t(entry.answerKey) }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script lang="ts" setup>
import type { LandingFaqEntry } from '~/types/LandingFaq'
import type { Ref } from 'vue'
import { ref } from 'vue'

const { track }: { track: (event: string, properties?: Record<string, unknown> | undefined) => void } =
  useSiteTracking()

/** FAQ entries (keys q1..q6 / a1..a6). */
const faqEntries: LandingFaqEntry[] = Array.from(
  { length: 6 },
  (_: unknown, index: number): LandingFaqEntry => ({
    questionKey: `walletLanding.faq.q${index + 1}`,
    answerKey: `walletLanding.faq.a${index + 1}`,
  }),
)

/** Index of the currently open entry (null when all are collapsed). */
const openIndex: Ref<number | null> = ref(0)

/**
 * Open an entry, or collapse it when it is already open.
 * @param index - Index of the clicked entry.
 */
function toggleEntry(index: number): void {
  const willOpen: boolean = openIndex.value !== index
  openIndex.value = willOpen ? index : null
  if (willOpen) {
    track('site_faq_open', { index, question: faqEntries[index]?.questionKey })
  }
}
</script>
