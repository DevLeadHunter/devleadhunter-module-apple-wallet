<template>
  <div class="space-y-8">
    <div class="flex flex-col gap-4 @2xl:flex-row @2xl:items-end @2xl:justify-between">
      <div>
        <p class="app-label flex items-center gap-2">
          <LandingAsterisk class="text-[0.6rem] text-[var(--app-accent)]" />
          Fidélité
        </p>
        <h1 class="app-page-title mt-2">Cartes de fidélité</h1>
        <p class="mt-1.5 max-w-2xl text-sm text-[var(--app-ink-soft)]">
          Configurez le programme Apple Wallet de chaque commerçant, puis remettez-lui son accès à l'espace commerçant.
        </p>
      </div>
      <NuxtLink to="/dashboard/wallet/new" class="app-btn-primary shrink-0">
        <UIcon name="i-lucide-plus" class="h-4 w-4" />
        Nouveau programme
      </NuxtLink>
    </div>

    <div v-if="isLoading" class="grid grid-cols-1 gap-4 @3xl:grid-cols-2">
      <div v-for="n in 4" :key="n" class="app-card h-40 animate-pulse"></div>
    </div>

    <div v-else-if="programs.length === 0" class="app-card flex flex-col items-center gap-3 p-12 text-center">
      <span class="flex h-12 w-12 items-center justify-center rounded-xl bg-[var(--app-surface-2)]">
        <UIcon name="i-lucide-wallet-cards" class="h-6 w-6 text-[var(--app-ink-soft)]" />
      </span>
      <p class="text-sm font-medium text-[var(--app-ink)]">Aucun programme de fidélité</p>
      <p class="max-w-sm text-xs text-[var(--app-ink-soft)]">
        Créez le premier programme d'un commerçant : ses tampons, sa récompense et ses couleurs de carte.
      </p>
      <NuxtLink to="/dashboard/wallet/new" class="app-btn-primary mt-2">
        <UIcon name="i-lucide-plus" class="h-4 w-4" />
        Nouveau programme
      </NuxtLink>
    </div>

    <div v-else class="grid grid-cols-1 gap-4 @3xl:grid-cols-2">
      <div v-for="program in programs" :key="program.id" class="app-card flex flex-col gap-4 p-5">
        <div class="flex items-start justify-between gap-3">
          <div class="flex min-w-0 items-center gap-3">
            <img
              v-if="program.logoUrl"
              :src="program.logoUrl"
              :alt="program.organizationName"
              class="h-10 w-10 shrink-0 rounded-lg object-cover"
            />
            <span
              v-else
              class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-sm font-semibold"
              :style="monogramStyle(program)"
            >
              {{ initial(program) }}
            </span>
            <div class="min-w-0">
              <p class="truncate text-sm font-semibold text-[var(--app-ink)]">{{ program.organizationName }}</p>
              <p class="truncate text-xs text-[var(--app-ink-soft)]">
                {{ program.stampsRequired }} tampons · {{ program.rewardLabel || 'récompense à définir' }}
              </p>
            </div>
          </div>
          <span :class="statusBadge(program.status).badgeClass">{{ statusBadge(program.status).label }}</span>
        </div>

        <div class="flex gap-2">
          <NuxtLink :to="`/dashboard/wallet/${program.id}`" class="app-btn-secondary h-9 flex-1 text-xs">
            <UIcon name="i-lucide-pencil" class="h-3.5 w-3.5" />
            Éditer
          </NuxtLink>
          <button
            type="button"
            class="app-btn-secondary h-9 flex-1 text-xs"
            :disabled="provisioningId === program.id"
            @click="provision(program)"
          >
            <UIcon
              :name="provisioningId === program.id ? 'i-lucide-loader-circle' : 'i-lucide-key-round'"
              :class="['h-3.5 w-3.5', provisioningId === program.id && 'animate-spin']"
            />
            Login commerçant
          </button>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div
        v-if="credentials"
        class="fixed inset-0 z-[60] flex items-center justify-center p-4"
        :style="{ backgroundColor: 'var(--app-overlay)' }"
        @click.self="closeCredentials"
      >
        <div class="app-card w-full max-w-md p-6 shadow-[var(--app-shadow-soft)]">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="app-label">Accès commerçant</p>
              <h2 class="app-page-title mt-1">{{ credentialsProgram?.organizationName }}</h2>
            </div>
            <button
              type="button"
              class="rounded-lg p-1.5 text-[var(--app-ink-soft)] transition-colors hover:bg-[var(--app-surface-2)]"
              aria-label="Fermer"
              @click="closeCredentials"
            >
              <UIcon name="i-lucide-x" class="h-4 w-4" />
            </button>
          </div>
          <p class="mt-2 text-sm text-[var(--app-ink-soft)]">
            Transmettez ces identifiants au commerçant. Le mot de passe ne sera plus affiché ensuite.
          </p>

          <div class="mt-5 space-y-3">
            <div class="space-y-1.5">
              <span class="app-label">Identifiant</span>
              <div
                class="flex items-center gap-2 rounded-lg border border-[var(--app-line)] bg-[var(--app-bg)] px-3 py-2"
              >
                <span class="min-w-0 flex-1 truncate font-mono text-sm text-[var(--app-ink)]">
                  {{ credentials.email }}
                </span>
                <button
                  type="button"
                  class="shrink-0 text-xs font-medium text-[var(--app-ink)] hover:underline"
                  @click="copyText(credentials.email, 'email')"
                >
                  {{ copiedField === 'email' ? 'Copié' : 'Copier' }}
                </button>
              </div>
            </div>
            <div class="space-y-1.5">
              <span class="app-label">Mot de passe</span>
              <div
                class="flex items-center gap-2 rounded-lg border border-[var(--app-line)] bg-[var(--app-bg)] px-3 py-2"
              >
                <span class="min-w-0 flex-1 truncate font-mono text-sm text-[var(--app-ink)]">
                  {{ credentials.password }}
                </span>
                <button
                  type="button"
                  class="shrink-0 text-xs font-medium text-[var(--app-ink)] hover:underline"
                  @click="copyText(credentials.password, 'password')"
                >
                  {{ copiedField === 'password' ? 'Copié' : 'Copier' }}
                </button>
              </div>
            </div>
          </div>

          <button type="button" class="app-btn-primary mt-6 w-full" @click="closeCredentials">Terminé</button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script lang="ts" setup>
import type { Ref } from 'vue'
import { ref, onMounted } from 'vue'
import type { WalletMerchantCredentials, WalletProgram, WalletProgramStatusBadge } from '~/types/WalletProgram'
import { WalletProgramService } from '~/services/walletProgramService'
import { useToast } from '~/composables/useToast'

definePageMeta({
  layout: 'dashboard',
  middleware: ['auth'],
})

const toast: ReturnType<typeof useToast> = useToast()

const programs: Ref<WalletProgram[]> = ref([])
const isLoading: Ref<boolean> = ref(true)
const provisioningId: Ref<number | null> = ref(null)
const credentials: Ref<WalletMerchantCredentials | null> = ref(null)
const credentialsProgram: Ref<WalletProgram | null> = ref(null)
const copiedField: Ref<string> = ref('')

/**
 * First letter of a program's merchant name, for the monogram fallback.
 * @param program - The program.
 * @returns The uppercase initial.
 */
function initial(program: WalletProgram): string {
  return program.organizationName.trim().charAt(0).toUpperCase() || '·'
}

/**
 * Monogram chip style, tinted with the card's brand color when set.
 * @param program - The program.
 * @returns The inline style bindings.
 */
function monogramStyle(program: WalletProgram): Record<string, string> {
  return {
    backgroundColor: program.backgroundColor?.trim() || 'var(--app-ink)',
    color: program.foregroundColor?.trim() || 'var(--app-surface)',
  }
}

/**
 * Map a program status to a French label and an `app-badge` variant.
 * @param status - The program status.
 * @returns The badge descriptor.
 */
function statusBadge(status: WalletProgram['status']): WalletProgramStatusBadge {
  if (status === 'active') {
    return { label: 'Actif', badgeClass: 'app-badge app-badge--success' }
  }
  if (status === 'archived') {
    return { label: 'Archivé', badgeClass: 'app-badge' }
  }
  return { label: 'Brouillon', badgeClass: 'app-badge app-badge--progress' }
}

/** Load the operator's programs. */
async function load(): Promise<void> {
  isLoading.value = true
  try {
    programs.value = await WalletProgramService.list()
  } catch (error) {
    toast.error(error instanceof Error ? error.message : 'Chargement impossible')
  } finally {
    isLoading.value = false
  }
}

/**
 * Provision (or reset) a merchant login and show it once.
 * @param program - The program to provision a login for.
 */
async function provision(program: WalletProgram): Promise<void> {
  provisioningId.value = program.id
  try {
    credentials.value = await WalletProgramService.provisionLogin(program.id)
    credentialsProgram.value = program
  } catch (error) {
    toast.error(error instanceof Error ? error.message : 'Provisioning impossible')
  } finally {
    provisioningId.value = null
  }
}

/**
 * Copy a value to the clipboard and flash a confirmation on its field.
 * @param text - The value to copy.
 * @param field - The field key that was copied.
 */
async function copyText(text: string, field: string): Promise<void> {
  try {
    await navigator.clipboard.writeText(text)
    copiedField.value = field
    setTimeout((): void => {
      if (copiedField.value === field) {
        copiedField.value = ''
      }
    }, 1500)
  } catch {
    toast.error('Copie impossible')
  }
}

/** Close the credentials modal. */
function closeCredentials(): void {
  credentials.value = null
  credentialsProgram.value = null
  copiedField.value = ''
}

onMounted(async (): Promise<void> => {
  await load()
})
</script>
