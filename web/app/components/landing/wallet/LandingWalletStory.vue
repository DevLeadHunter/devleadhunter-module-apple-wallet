<template>
  <section id="how-it-works" class="relative pt-28 md:pt-40">
    <div class="mx-auto max-w-6xl px-5 md:px-8">
      <p v-reveal class="landing-eyebrow">{{ $t('walletLanding.story.eyebrow') }}</p>
      <h2
        v-reveal="{ delay: 80 }"
        class="font-display mt-6 max-w-3xl text-4xl leading-[1.06] font-semibold tracking-[-0.015em] text-[#1b1813] md:text-5xl"
      >
        {{ $t('walletLanding.story.title') }}
      </h2>
      <p v-reveal="{ delay: 160 }" class="mt-5 max-w-xl text-lg leading-relaxed text-[#6b6355]">
        {{ $t('walletLanding.story.subtitle') }}
      </p>
    </div>

    <div ref="stickyWrapperRef" class="relative hidden h-[400vh] md:block">
      <div class="sticky top-0 flex h-screen items-center">
        <div class="mx-auto w-full max-w-6xl px-8">
          <div class="grid w-full grid-cols-2 items-center gap-12 xl:gap-20">
            <div class="relative pl-10">
              <div class="absolute top-2 bottom-2 left-0 w-px bg-[#e3dccd]" aria-hidden="true">
                <div
                  class="absolute inset-x-0 top-0 h-full origin-top bg-[#e8a33c]"
                  :style="{ transform: `scaleY(${storyProgress})` }"
                ></div>
              </div>
              <ol class="space-y-8">
                <li
                  v-for="act in storyActs"
                  :key="act.actIndex"
                  class="transition-opacity duration-500"
                  :class="act.actIndex === activeActIndex ? 'opacity-100' : 'opacity-30'"
                >
                  <p class="font-label text-xs font-medium text-[#e8a33c]">0{{ act.actIndex + 1 }}</p>
                  <h3 class="font-display mt-1 text-3xl font-semibold text-[#1b1813] xl:text-4xl">
                    {{ $t(act.verbKey) }}
                  </h3>
                  <div
                    class="grid transition-[grid-template-rows] duration-500 ease-out"
                    :class="act.actIndex === activeActIndex ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'"
                  >
                    <p class="max-w-md overflow-hidden text-base leading-relaxed text-[#6b6355]">
                      {{ $t(act.descriptionKey) }}
                    </p>
                  </div>
                </li>
              </ol>
            </div>

            <div class="relative h-[440px]">
              <div
                v-for="act in storyActs"
                :key="act.actIndex"
                class="absolute inset-0 flex items-center transition-all duration-500 ease-out"
                :class="stageCardClass(act.actIndex)"
              >
                <LandingWalletStoryVisual :act-index="act.actIndex" class="w-full" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="mx-auto max-w-6xl space-y-16 px-5 pt-16 pb-24 md:hidden">
      <div v-for="act in storyActs" :key="act.actIndex" class="grid gap-8">
        <div v-reveal>
          <p class="font-label text-xs font-medium text-[#e8a33c]">0{{ act.actIndex + 1 }}</p>
          <h3 class="font-display mt-1 text-3xl font-semibold text-[#1b1813]">
            {{ $t(act.verbKey) }}
          </h3>
          <p class="mt-3 max-w-md text-base leading-relaxed text-[#6b6355]">
            {{ $t(act.descriptionKey) }}
          </p>
        </div>
        <LandingWalletStoryVisual v-reveal="{ delay: 120 }" :act-index="act.actIndex" class="mx-auto w-full max-w-md" />
      </div>
    </div>
  </section>
</template>

<script lang="ts" setup>
import type { LandingStoryAct } from '~/types/LandingPipelineStory'
import type { Ref } from 'vue'
import { ref, onMounted, onBeforeUnmount } from 'vue'

/** The four acts of the loyalty-card story. */
const storyActs: LandingStoryAct[] = [
  { actIndex: 0, verbKey: 'walletLanding.story.act1.verb', descriptionKey: 'walletLanding.story.act1.description' },
  { actIndex: 1, verbKey: 'walletLanding.story.act2.verb', descriptionKey: 'walletLanding.story.act2.description' },
  { actIndex: 2, verbKey: 'walletLanding.story.act3.verb', descriptionKey: 'walletLanding.story.act3.description' },
  { actIndex: 3, verbKey: 'walletLanding.story.act4.verb', descriptionKey: 'walletLanding.story.act4.description' },
]

/** Tall wrapper whose scroll range drives the narrative (4 acts ≈ 75vh each). */
const stickyWrapperRef: Ref<HTMLElement | null> = ref(null)

/** Index of the act currently highlighted by the scroll position. */
const activeActIndex: Ref<number> = ref(0)

/** Scroll progress through the narrative, from 0 to 1 (drives the rail fill). */
const storyProgress: Ref<number> = ref(0)

/**
 * Compute the transition classes of a stage card relative to the active act.
 * @param index - Act index of the stage card.
 * @returns Tailwind classes describing the card state.
 */
function stageCardClass(index: number): string {
  if (index === activeActIndex.value) {
    return 'z-10 translate-y-0 scale-100 opacity-100'
  }
  if (index < activeActIndex.value) {
    return 'pointer-events-none z-0 -translate-y-10 scale-[0.96] opacity-0'
  }
  return 'pointer-events-none z-0 translate-y-10 scale-[0.96] opacity-0'
}

/**
 * Update the narrative progress from the sticky wrapper position.
 */
function handleStoryScroll(): void {
  const wrapper: HTMLElement | null = stickyWrapperRef.value
  if (!wrapper) {
    return
  }
  const rect: DOMRect = wrapper.getBoundingClientRect()
  const scrollableHeight: number = rect.height - window.innerHeight
  if (scrollableHeight <= 0) {
    return
  }
  const progress: number = Math.min(1, Math.max(0, -rect.top / scrollableHeight))
  storyProgress.value = progress
  activeActIndex.value = Math.min(storyActs.length - 1, Math.floor(progress * storyActs.length))
}

onMounted((): void => {
  window.addEventListener('scroll', handleStoryScroll, { passive: true })
  window.addEventListener('resize', handleStoryScroll, { passive: true })
  handleStoryScroll()
})

onBeforeUnmount((): void => {
  window.removeEventListener('scroll', handleStoryScroll)
  window.removeEventListener('resize', handleStoryScroll)
})
</script>
