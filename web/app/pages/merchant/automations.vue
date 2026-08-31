<template>
  <div class="space-y-6">
    <div>
      <NuxtLink
        to="/merchant"
        class="inline-flex items-center gap-1.5 text-xs font-medium text-[var(--app-ink-soft)] transition-colors hover:text-[var(--app-ink)]"
      >
        <UIcon name="i-lucide-arrow-left" class="h-3.5 w-3.5" />
        Tableau de bord
      </NuxtLink>
      <h1 class="app-page-title mt-2">Vos offres</h1>
      <p class="mt-1.5 max-w-xl text-sm text-[var(--app-ink-soft)]">
        Des offres qui s'affichent sur la carte de vos clients et les notifient : diffusées à tous, ou déclenchées après
        un tampon.
      </p>
    </div>

    <div v-if="formOpen" class="app-card space-y-5 p-5">
      <h2 class="text-sm font-semibold text-[var(--app-ink)]">
        {{ editingId ? "Éditer l'offre" : 'Nouvelle offre' }}
      </h2>

      <div class="space-y-1.5">
        <label class="app-label" for="ma-name">Nom</label>
        <input
          id="ma-name"
          v-model="form.name"
          class="input-field"
          type="text"
          maxlength="60"
          placeholder="Offre du weekend"
        />
      </div>

      <div class="space-y-2">
        <span class="app-label">Déclencheur</span>
        <div class="flex overflow-hidden rounded-lg border border-[var(--app-line)]">
          <button
            v-for="option in TRIGGERS"
            :key="option.value"
            type="button"
            class="flex-1 cursor-pointer px-2.5 py-1.5 text-xs font-medium transition-colors"
            :class="
              form.triggerType === option.value
                ? 'bg-[var(--app-ink)] text-[var(--app-surface)]'
                : 'bg-[var(--app-surface)] text-[var(--app-ink-soft)] hover:text-[var(--app-ink)]'
            "
            @click="form.triggerType = option.value"
          >
            {{ option.label }}
          </button>
        </div>
        <p class="text-[11px] text-[var(--app-ink-soft)]">{{ triggerHint }}</p>
      </div>

      <div v-if="form.triggerType === 'on_scan'" class="space-y-1.5">
        <label class="app-label" for="ma-delay">Délai après le tampon (minutes)</label>
        <input id="ma-delay" v-model.number="form.delayMinutes" class="input-field" type="number" min="0" max="10080" />
      </div>

      <div class="space-y-1.5">
        <label class="app-label" for="ma-offer">Offre affichée sur la carte</label>
        <input
          id="ma-offer"
          v-model="form.fieldValue"
          class="input-field"
          type="text"
          maxlength="80"
          placeholder="-10% sur ta prochaine visite"
        />
      </div>

      <div class="space-y-1.5">
        <label class="app-label" for="ma-message">Message de notification (optionnel)</label>
        <input
          id="ma-message"
          v-model="form.changeMessage"
          class="input-field"
          type="text"
          maxlength="120"
          placeholder="Une offre rien que pour vous !"
        />
      </div>

      <div class="flex gap-2">
        <UiDlhButton class="flex-1" :loading="isSaving" @click="save">Enregistrer</UiDlhButton>
        <button type="button" class="app-btn-secondary flex-1" @click="closeForm">Annuler</button>
      </div>
    </div>

    <template v-else>
      <div class="flex items-center justify-between">
        <span class="text-xs text-[var(--app-ink-soft)]"
          >{{ automations.length }} offre{{ automations.length > 1 ? 's' : '' }}</span
        >
        <UiDlhButton size="md" @click="openCreate">
          <UIcon name="i-lucide-plus" class="h-4 w-4" />
          Nouvelle
        </UiDlhButton>
      </div>

      <div v-if="isLoading" class="space-y-3">
        <div v-for="n in 3" :key="n" class="app-card h-24 animate-pulse"></div>
      </div>

      <div v-else-if="automations.length === 0" class="app-card p-10 text-center">
        <p class="text-sm font-medium text-[var(--app-ink)]">Aucune offre</p>
        <p class="mx-auto mt-1.5 max-w-sm text-xs text-[var(--app-ink-soft)]">
          Créez une diffusion (offre envoyée à tous vos clients) ou une relance automatique après chaque tampon.
        </p>
      </div>

      <div v-else class="space-y-3">
        <div v-for="auto in automations" :key="auto.id" class="app-card flex flex-col gap-3 p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <span class="text-sm font-semibold text-[var(--app-ink)]">{{ auto.name || 'Offre' }}</span>
                <span :class="triggerBadge(auto.triggerType).badgeClass">{{
                  triggerBadge(auto.triggerType).label
                }}</span>
              </div>
              <p class="mt-1 truncate text-xs text-[var(--app-ink-soft)]">
                {{ auto.fieldValue || auto.changeMessage || 'Sans offre définie'
                }}<span v-if="auto.triggerType === 'on_scan'"> · après {{ auto.delayMinutes }} min</span>
              </p>
            </div>
            <button
              type="button"
              class="app-badge shrink-0"
              :class="auto.isActive ? 'app-badge--success' : ''"
              :disabled="busyId === auto.id"
              @click="toggleActive(auto)"
            >
              {{ auto.isActive ? 'Actif' : 'En pause' }}
            </button>
          </div>

          <div class="flex flex-wrap gap-2">
            <button
              v-if="auto.triggerType === 'broadcast'"
              type="button"
              class="app-btn-secondary h-8 px-3 text-xs"
              :disabled="busyId === auto.id || !auto.isActive"
              @click="broadcast(auto)"
            >
              <UIcon
                :name="busyId === auto.id ? 'i-lucide-loader-circle' : 'i-lucide-send'"
                :class="['h-3.5 w-3.5', busyId === auto.id && 'animate-spin']"
              />
              Diffuser maintenant
            </button>
            <button type="button" class="app-btn-secondary h-8 px-3 text-xs" @click="openEdit(auto)">
              <UIcon name="i-lucide-pencil" class="h-3.5 w-3.5" />
              Éditer
            </button>
            <button
              type="button"
              class="app-btn-secondary h-8 px-3 text-xs"
              :disabled="busyId === auto.id"
              @click="remove(auto)"
            >
              <UIcon name="i-lucide-trash-2" class="h-3.5 w-3.5" />
              Supprimer
            </button>
          </div>
        </div>
      </div>
    </template>

    <div
      v-if="flash"
      class="fixed bottom-5 left-1/2 z-50 -translate-x-1/2 rounded-full px-4 py-2 text-sm font-medium shadow-[var(--app-shadow-soft)]"
      :style="flashStyle"
      role="status"
    >
      {{ flash.text }}
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import { computed, ref, onMounted, onUnmounted } from 'vue'
import type {
  WalletAutomation,
  WalletAutomationCreatePayload,
  WalletAutomationForm,
  WalletAutomationTrigger,
} from '~/types/WalletAutomation'
import type { WalletProgramStatusBadge } from '~/types/WalletProgram'
import type { MerchantFlash, MerchantFlashTone } from '~/types/MerchantDashboard'
import { useMerchantStore } from '~/stores/merchant'
import { MerchantAutomationService } from '~/services/merchantAutomationService'

definePageMeta({
  layout: 'merchant',
  middleware: ['merchant-auth'],
})

/** Selectable triggers. */
const TRIGGERS: { value: WalletAutomationTrigger; label: string }[] = [
  { value: 'broadcast', label: 'Diffusion' },
  { value: 'on_scan', label: 'Après un tampon' },
]

const merchantStore: ReturnType<typeof useMerchantStore> = useMerchantStore()

const automations: Ref<WalletAutomation[]> = ref([])
const isLoading: Ref<boolean> = ref(true)
const busyId: Ref<number | null> = ref(null)

const formOpen: Ref<boolean> = ref(false)
const editingId: Ref<number | null> = ref(null)
const isSaving: Ref<boolean> = ref(false)
const form: Ref<WalletAutomationForm> = ref(emptyForm())

const flash: Ref<MerchantFlash | null> = ref(null)
let flashTimer: ReturnType<typeof setTimeout> | null = null

/** A blank automation form (defaults to a broadcast). */
function emptyForm(): WalletAutomationForm {
  return { name: '', triggerType: 'broadcast', delayMinutes: 0, fieldValue: '', changeMessage: '' }
}

/** Contextual help under the trigger selector. */
const triggerHint: ComputedRef<string> = computed((): string =>
  form.value.triggerType === 'broadcast'
    ? 'Envoyée à toutes vos cartes actives, quand vous cliquez sur « Diffuser ».'
    : 'Déclenchée automatiquement après chaque tampon, une fois le délai écoulé.',
)

/** Background/text style of the transient action flash, by tone. */
const flashStyle: ComputedRef<Record<string, string>> = computed((): Record<string, string> => {
  const tone: MerchantFlashTone = flash.value?.tone ?? 'neutral'
  if (tone === 'success') {
    return { backgroundColor: 'var(--app-green)', color: '#fbf9f3' }
  }
  if (tone === 'error') {
    return { backgroundColor: 'var(--app-red)', color: '#fbf9f3' }
  }
  return { backgroundColor: 'var(--app-ink)', color: 'var(--app-surface)' }
})

/**
 * Label + `app-badge` variant for a trigger.
 * @param trigger - The automation trigger.
 * @returns The badge descriptor.
 */
function triggerBadge(trigger: WalletAutomationTrigger): WalletProgramStatusBadge {
  return trigger === 'broadcast'
    ? { label: 'Diffusion', badgeClass: 'app-badge app-badge--info' }
    : { label: 'Après un tampon', badgeClass: 'app-badge' }
}

/**
 * Flash a transient confirmation, auto-dismissed after a short delay.
 * @param text - The message.
 * @param tone - Its tone.
 */
function showFlash(text: string, tone: MerchantFlashTone): void {
  flash.value = { text, tone }
  if (flashTimer !== null) {
    clearTimeout(flashTimer)
  }
  flashTimer = setTimeout((): void => {
    flash.value = null
  }, 2600)
}

/** Open the form to create a new automation. */
function openCreate(): void {
  editingId.value = null
  form.value = emptyForm()
  formOpen.value = true
}

/**
 * Open the form to edit an automation.
 * @param automation - The automation to edit.
 */
function openEdit(automation: WalletAutomation): void {
  editingId.value = automation.id
  form.value = {
    name: automation.name ?? '',
    triggerType: automation.triggerType,
    delayMinutes: automation.delayMinutes,
    fieldValue: automation.fieldValue ?? '',
    changeMessage: automation.changeMessage ?? '',
  }
  formOpen.value = true
}

/** Close the form without saving. */
function closeForm(): void {
  formOpen.value = false
  editingId.value = null
}

/** Build the create/update payload from the form. */
function buildPayload(): WalletAutomationCreatePayload {
  return {
    name: form.value.name.trim() || null,
    triggerType: form.value.triggerType,
    delayMinutes: form.value.triggerType === 'on_scan' ? Math.max(form.value.delayMinutes, 0) : 0,
    fieldValue: form.value.fieldValue.trim() || null,
    changeMessage: form.value.changeMessage.trim() || null,
  }
}

/** Load the merchant's automations. */
async function load(): Promise<void> {
  const token: string | null = merchantStore.token
  if (!token) {
    isLoading.value = false
    return
  }
  isLoading.value = true
  try {
    automations.value = await MerchantAutomationService.list(token)
  } catch (error) {
    showFlash(error instanceof Error ? error.message : 'Chargement impossible', 'error')
  } finally {
    isLoading.value = false
  }
}

/** Create or save the automation, then return to the list. */
async function save(): Promise<void> {
  const token: string | null = merchantStore.token
  if (!token) {
    return
  }
  isSaving.value = true
  try {
    if (editingId.value === null) {
      await MerchantAutomationService.create(token, buildPayload())
      showFlash('Offre créée', 'success')
    } else {
      await MerchantAutomationService.update(token, editingId.value, buildPayload())
      showFlash('Offre enregistrée', 'success')
    }
    closeForm()
    await load()
  } catch (error) {
    showFlash(error instanceof Error ? error.message : 'Enregistrement impossible', 'error')
  } finally {
    isSaving.value = false
  }
}

/**
 * Toggle an automation active/paused.
 * @param automation - The automation to toggle.
 */
async function toggleActive(automation: WalletAutomation): Promise<void> {
  const token: string | null = merchantStore.token
  if (!token) {
    return
  }
  busyId.value = automation.id
  try {
    const updated: WalletAutomation = await MerchantAutomationService.update(token, automation.id, {
      isActive: !automation.isActive,
    })
    automations.value = automations.value.map(
      (item: WalletAutomation): WalletAutomation => (item.id === updated.id ? updated : item),
    )
  } catch (error) {
    showFlash(error instanceof Error ? error.message : 'Action impossible', 'error')
  } finally {
    busyId.value = null
  }
}

/**
 * Broadcast an automation to every active card.
 * @param automation - The broadcast automation.
 */
async function broadcast(automation: WalletAutomation): Promise<void> {
  const token: string | null = merchantStore.token
  if (!token) {
    return
  }
  busyId.value = automation.id
  try {
    const result: { scheduled: number } = await MerchantAutomationService.broadcast(token, automation.id)
    showFlash(`Offre envoyée à ${result.scheduled} carte${result.scheduled > 1 ? 's' : ''}`, 'success')
  } catch (error) {
    showFlash(error instanceof Error ? error.message : 'Diffusion impossible', 'error')
  } finally {
    busyId.value = null
  }
}

/**
 * Delete an automation after confirmation.
 * @param automation - The automation to delete.
 */
async function remove(automation: WalletAutomation): Promise<void> {
  const token: string | null = merchantStore.token
  if (!token || !window.confirm('Supprimer cette offre ?')) {
    return
  }
  busyId.value = automation.id
  try {
    await MerchantAutomationService.remove(token, automation.id)
    automations.value = automations.value.filter((item: WalletAutomation): boolean => item.id !== automation.id)
  } catch (error) {
    showFlash(error instanceof Error ? error.message : 'Suppression impossible', 'error')
  } finally {
    busyId.value = null
  }
}

onMounted(async (): Promise<void> => {
  await load()
})

onUnmounted((): void => {
  if (flashTimer !== null) {
    clearTimeout(flashTimer)
  }
})
</script>
