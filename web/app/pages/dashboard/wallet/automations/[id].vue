<template>
  <div class="space-y-6">
    <div>
      <NuxtLink
        :to="`/dashboard/wallet/${programId}`"
        class="inline-flex items-center gap-1.5 text-xs font-medium text-[var(--app-ink-soft)] transition-colors hover:text-[var(--app-ink)]"
      >
        <UIcon name="i-lucide-arrow-left" class="h-3.5 w-3.5" />
        {{ programName || 'Programme' }}
      </NuxtLink>
      <h1 class="app-page-title mt-2">Automatisations</h1>
      <p class="mt-1.5 max-w-2xl text-sm text-[var(--app-ink-soft)]">
        Des offres qui s'affichent sur la carte et notifient le client : diffusées à tous, ou déclenchées après un
        tampon.
      </p>
    </div>

    <div v-if="formOpen" class="app-card space-y-5 p-5">
      <h2 class="text-sm font-semibold text-[var(--app-ink)]">
        {{ editingId ? "Éditer l'automatisation" : 'Nouvelle automatisation' }}
      </h2>

      <div class="space-y-1.5">
        <label class="app-label" for="au-name">Nom</label>
        <input
          id="au-name"
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
        <label class="app-label" for="au-delay">Délai après le tampon (minutes)</label>
        <input id="au-delay" v-model.number="form.delayMinutes" class="input-field" type="number" min="0" max="10080" />
      </div>

      <div class="space-y-1.5">
        <label class="app-label" for="au-offer">Offre affichée sur la carte</label>
        <input
          id="au-offer"
          v-model="form.fieldValue"
          class="input-field"
          type="text"
          maxlength="80"
          placeholder="-10% sur ta prochaine visite"
        />
      </div>

      <div class="space-y-1.5">
        <label class="app-label" for="au-message">Message de notification (optionnel)</label>
        <input
          id="au-message"
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
        <span class="text-xs text-[var(--app-ink-soft)]">
          {{ automations.length }} automatisation{{ automations.length > 1 ? 's' : '' }}
        </span>
        <UiDlhButton size="md" @click="openCreate">
          <UIcon name="i-lucide-plus" class="h-4 w-4" />
          Nouvelle
        </UiDlhButton>
      </div>

      <div v-if="isLoading" class="space-y-3">
        <div v-for="n in 3" :key="n" class="app-card h-24 animate-pulse"></div>
      </div>

      <div v-else-if="automations.length === 0" class="app-card p-10 text-center">
        <p class="text-sm font-medium text-[var(--app-ink)]">Aucune automatisation</p>
        <p class="mx-auto mt-1.5 max-w-sm text-xs text-[var(--app-ink-soft)]">
          Créez une diffusion (offre envoyée à tous vos clients) ou une relance automatique après chaque tampon.
        </p>
      </div>

      <div v-else class="space-y-3">
        <div v-for="auto in automations" :key="auto.id" class="app-card flex flex-col gap-3 p-4">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <span class="text-sm font-semibold text-[var(--app-ink)]">{{ auto.name || 'Automatisation' }}</span>
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
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import { computed, ref, onMounted } from 'vue'
import type {
  WalletAutomation,
  WalletAutomationCreatePayload,
  WalletAutomationForm,
  WalletAutomationTrigger,
} from '~/types/WalletAutomation'
import type { WalletProgram, WalletProgramStatusBadge } from '~/types/WalletProgram'
import { WalletAutomationService } from '~/services/walletAutomationService'
import { WalletProgramService } from '~/services/walletProgramService'
import { useToast } from '~/composables/useToast'

definePageMeta({
  layout: 'dashboard',
  middleware: ['auth'],
})

/** Selectable triggers. */
const TRIGGERS: { value: WalletAutomationTrigger; label: string }[] = [
  { value: 'broadcast', label: 'Diffusion' },
  { value: 'on_scan', label: 'Après un tampon' },
]

const route: ReturnType<typeof useRoute> = useRoute()
const toast: ReturnType<typeof useToast> = useToast()

const programId: number = Number(route.params.id)

const programName: Ref<string> = ref('')
const automations: Ref<WalletAutomation[]> = ref([])
const isLoading: Ref<boolean> = ref(true)
const busyId: Ref<number | null> = ref(null)

const formOpen: Ref<boolean> = ref(false)
const editingId: Ref<number | null> = ref(null)
const isSaving: Ref<boolean> = ref(false)
const form: Ref<WalletAutomationForm> = ref(emptyForm())

/** A blank automation form (defaults to a broadcast). */
function emptyForm(): WalletAutomationForm {
  return { name: '', triggerType: 'broadcast', delayMinutes: 0, fieldValue: '', changeMessage: '' }
}

/** Contextual help under the trigger selector. */
const triggerHint: ComputedRef<string> = computed((): string =>
  form.value.triggerType === 'broadcast'
    ? 'Envoyée à toutes les cartes actives, quand vous cliquez sur « Diffuser ».'
    : 'Déclenchée automatiquement après chaque tampon, une fois le délai écoulé.',
)

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

/** Load the program name and its automations. */
async function load(): Promise<void> {
  isLoading.value = true
  try {
    const [program, list]: [WalletProgram, WalletAutomation[]] = await Promise.all([
      WalletProgramService.get(programId),
      WalletAutomationService.list(programId),
    ])
    programName.value = program.organizationName
    automations.value = list
  } catch (error) {
    toast.error(error instanceof Error ? error.message : 'Chargement impossible')
  } finally {
    isLoading.value = false
  }
}

/** Create or save the automation, then return to the list. */
async function save(): Promise<void> {
  isSaving.value = true
  try {
    if (editingId.value === null) {
      await WalletAutomationService.create(programId, buildPayload())
      toast.success('Automatisation créée')
    } else {
      await WalletAutomationService.update(editingId.value, buildPayload())
      toast.success('Automatisation enregistrée')
    }
    closeForm()
    await load()
  } catch (error) {
    toast.error(error instanceof Error ? error.message : 'Enregistrement impossible')
  } finally {
    isSaving.value = false
  }
}

/**
 * Toggle an automation active/paused.
 * @param automation - The automation to toggle.
 */
async function toggleActive(automation: WalletAutomation): Promise<void> {
  busyId.value = automation.id
  try {
    const updated: WalletAutomation = await WalletAutomationService.update(automation.id, {
      isActive: !automation.isActive,
    })
    automations.value = automations.value.map(
      (item: WalletAutomation): WalletAutomation => (item.id === updated.id ? updated : item),
    )
  } catch (error) {
    toast.error(error instanceof Error ? error.message : 'Action impossible')
  } finally {
    busyId.value = null
  }
}

/**
 * Fan a broadcast automation out to every active card.
 * @param automation - The broadcast automation.
 */
async function broadcast(automation: WalletAutomation): Promise<void> {
  busyId.value = automation.id
  try {
    const result: { scheduled: number } = await WalletAutomationService.broadcast(automation.id)
    toast.success(`Offre envoyée à ${result.scheduled} carte${result.scheduled > 1 ? 's' : ''}`)
  } catch (error) {
    toast.error(error instanceof Error ? error.message : 'Diffusion impossible')
  } finally {
    busyId.value = null
  }
}

/**
 * Delete an automation after confirmation.
 * @param automation - The automation to delete.
 */
async function remove(automation: WalletAutomation): Promise<void> {
  if (!window.confirm('Supprimer cette automatisation ?')) {
    return
  }
  busyId.value = automation.id
  try {
    await WalletAutomationService.remove(automation.id)
    automations.value = automations.value.filter((item: WalletAutomation): boolean => item.id !== automation.id)
  } catch (error) {
    toast.error(error instanceof Error ? error.message : 'Suppression impossible')
  } finally {
    busyId.value = null
  }
}

onMounted(async (): Promise<void> => {
  await load()
})
</script>
