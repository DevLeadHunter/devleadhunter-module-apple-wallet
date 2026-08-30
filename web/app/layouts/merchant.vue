<template>
  <div class="app-theme" data-theme="light">
    <div class="flex min-h-screen flex-col" :style="{ backgroundColor: 'var(--app-bg)' }">
      <header
        class="sticky top-0 z-10 border-b border-[var(--app-line)] bg-[var(--app-surface)] px-4 pt-[calc(0.75rem+env(safe-area-inset-top))] pb-3 md:px-6"
      >
        <div class="mx-auto flex w-full max-w-6xl items-center justify-between gap-3">
          <div class="flex min-w-0 items-center gap-2.5">
            <img
              v-if="logoUrl"
              :src="logoUrl"
              :alt="organizationName"
              class="h-7 w-7 shrink-0 rounded-md object-cover"
            />
            <span
              v-else
              class="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-[var(--app-ink)] text-sm font-semibold text-[var(--app-surface)]"
            >
              {{ initial }}
            </span>
            <span class="font-display truncate text-base font-semibold tracking-tight text-[var(--app-ink)]">
              {{ organizationName || 'Espace commerçant' }}
            </span>
            <span
              class="font-label hidden shrink-0 rounded-full border border-[var(--app-line)] px-2 py-0.5 text-[0.62rem] tracking-[0.08em] text-[var(--app-ink-soft)] uppercase sm:inline"
            >
              Fidélité
            </span>
          </div>

          <UiDlhButton variant="secondary" size="md" class="shrink-0" @click="handleLogout">
            <UIcon name="i-lucide-log-out" class="h-4 w-4" aria-hidden="true" />
            <span class="hidden sm:inline">Déconnexion</span>
          </UiDlhButton>
        </div>
      </header>

      <main class="mx-auto w-full max-w-6xl flex-1 px-4 pt-6 pb-[calc(2rem+env(safe-area-inset-bottom))] md:px-6">
        <slot />
      </main>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef } from 'vue'
import { computed } from 'vue'
import { useMerchantStore } from '~/stores/merchant'

const merchantStore: ReturnType<typeof useMerchantStore> = useMerchantStore()
const router: ReturnType<typeof useRouter> = useRouter()

// Dedicated merchant surface — never indexed (authenticated tool, no SEO value).
useSeoMeta({
  robots: 'noindex, nofollow',
})

/** Logged-in merchant's organization name, shown as the surface brand. */
const organizationName: ComputedRef<string> = computed((): string => merchantStore.program?.organizationName ?? '')

/** Merchant logo, shown in the top bar when the program has one. */
const logoUrl: ComputedRef<string | null> = computed((): string | null => merchantStore.program?.logoUrl ?? null)

/** First letter of the merchant name, shown when there is no logo. */
const initial: ComputedRef<string> = computed(
  (): string => organizationName.value.trim().charAt(0).toUpperCase() || '·',
)

/** Log out and return to the merchant login. */
function handleLogout(): void {
  merchantStore.logout()
  router.push('/merchant/login')
}
</script>
