<template>
  <div class="space-y-6">
    <div>
      <NuxtLink
        to="/dashboard/wallet"
        class="inline-flex items-center gap-1.5 text-xs font-medium text-[var(--app-ink-soft)] transition-colors hover:text-[var(--app-ink)]"
      >
        <UIcon name="i-lucide-arrow-left" class="h-3.5 w-3.5" />
        Cartes de fidélité
      </NuxtLink>
      <h1 class="app-page-title mt-2">{{ isNew ? 'Nouveau programme' : 'Éditer le programme' }}</h1>
      <p class="mt-1.5 max-w-2xl text-sm text-[var(--app-ink-soft)]">
        La carte que le commerçant offre à ses clients — ses tampons, sa récompense et ses couleurs.
      </p>
    </div>

    <div v-if="isLoading" class="flex justify-center py-20">
      <UiLoader />
    </div>

    <div v-else class="grid grid-cols-1 gap-5 @4xl:grid-cols-[minmax(0,1fr)_22rem]">
      <div class="app-card flex items-center justify-center overflow-hidden p-8" :style="stageStyle">
        <UiWalletCardPreview
          :organization-name="form.organizationName || 'Nom du commerce'"
          :stamps="sampleStamps"
          :stamps-required="form.stampsRequired"
          :reward-label="form.rewardLabel || null"
          :logo-url="form.logoUrl || null"
          :background-color="form.backgroundColor"
          :foreground-color="form.foregroundColor"
          :label-color="form.labelColor"
          serial-number="apercu-0001"
        />
      </div>

      <div class="app-card space-y-5 p-5">
        <div class="space-y-1.5">
          <label class="app-label" for="wp-org">Nom du commerce</label>
          <input id="wp-org" v-model="form.organizationName" class="input-field" type="text" maxlength="40" />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <div class="space-y-1.5">
            <label class="app-label" for="wp-required">Tampons requis</label>
            <input
              id="wp-required"
              v-model.number="form.stampsRequired"
              class="input-field"
              type="number"
              min="1"
              max="12"
            />
          </div>
          <div class="space-y-1.5">
            <label class="app-label" for="wp-reward">Récompense</label>
            <input id="wp-reward" v-model="form.rewardLabel" class="input-field" type="text" maxlength="40" />
          </div>
        </div>

        <div class="space-y-1.5">
          <label class="app-label" for="wp-message">Message à chaque tampon</label>
          <input
            id="wp-message"
            v-model="form.defaultChangeMessage"
            class="input-field"
            type="text"
            maxlength="80"
            placeholder="Plus que %@ tampons avant votre récompense !"
          />
          <p class="text-[11px] text-[var(--app-ink-soft)]">
            <code class="text-[var(--app-accent-ink)]">%@</code> est remplacé par le nombre de tampons restants.
          </p>
        </div>

        <div class="space-y-1.5">
          <label class="app-label" for="wp-logo">Logo (URL)</label>
          <input id="wp-logo" v-model="form.logoUrl" class="input-field" type="url" placeholder="https://…" />
        </div>

        <div class="space-y-2">
          <span class="app-label">Ambiance</span>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="palette in PALETTES"
              :key="palette.id"
              type="button"
              class="flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors"
              :class="
                palette.id === selectedPaletteId
                  ? 'border-[var(--app-ink)] text-[var(--app-ink)]'
                  : 'border-[var(--app-line)] text-[var(--app-ink-soft)] hover:border-[var(--app-ink-soft)]'
              "
              @click="applyPalette(palette)"
            >
              <span
                class="h-3.5 w-3.5 rounded-full border border-black/10"
                :style="{ backgroundColor: palette.background }"
              />
              {{ palette.label }}
            </button>
          </div>
        </div>

        <div v-if="!isNew" class="space-y-2">
          <span class="app-label">Statut</span>
          <div class="flex overflow-hidden rounded-lg border border-[var(--app-line)]">
            <button
              v-for="option in STATUSES"
              :key="option.value"
              type="button"
              class="flex-1 cursor-pointer px-2.5 py-1.5 text-xs font-medium transition-colors"
              :class="
                form.status === option.value
                  ? 'bg-[var(--app-ink)] text-[var(--app-surface)]'
                  : 'bg-[var(--app-surface)] text-[var(--app-ink-soft)] hover:text-[var(--app-ink)]'
              "
              @click="form.status = option.value"
            >
              {{ option.label }}
            </button>
          </div>
        </div>

        <UiDlhButton class="w-full" :loading="isSaving" @click="save">
          {{ isNew ? 'Créer le programme' : 'Enregistrer' }}
        </UiDlhButton>
      </div>
    </div>

    <div v-if="!isNew && publicToken" class="app-card p-5">
      <div class="mb-3 flex items-center justify-between gap-3">
        <h2 class="text-sm font-semibold text-[var(--app-ink)]">Partager la carte</h2>
        <NuxtLink :to="`/dashboard/wallet/chevalet/${programId}`" class="app-btn-secondary h-8 px-3 text-xs">
          <UIcon name="i-lucide-printer" class="h-3.5 w-3.5" />
          Imprimer le chevalet
        </NuxtLink>
      </div>
      <p class="mb-4 text-xs text-[var(--app-ink-soft)]">
        Le QR à poser sur le comptoir : vos clients le scannent pour ajouter leur carte à Apple Wallet.
      </p>
      <div class="flex flex-col gap-4 @xl:flex-row @xl:items-center">
        <img
          v-if="qrDataUrl"
          :src="qrDataUrl"
          alt="QR code d'enrôlement"
          class="h-28 w-28 shrink-0 rounded-lg border border-[var(--app-line)] bg-white p-1.5"
        />
        <div class="min-w-0 flex-1 space-y-2">
          <span class="app-label">Lien public</span>
          <div class="flex items-center gap-2 rounded-lg border border-[var(--app-line)] bg-[var(--app-bg)] px-3 py-2">
            <span class="min-w-0 flex-1 truncate font-mono text-xs text-[var(--app-ink)]">{{ enrollLink }}</span>
            <button
              type="button"
              class="shrink-0 text-xs font-medium text-[var(--app-ink)] hover:underline"
              @click="copyLink"
            >
              {{ linkCopied ? 'Copié' : 'Copier' }}
            </button>
          </div>
          <a
            :href="enrollLink"
            target="_blank"
            rel="noopener"
            class="inline-flex items-center gap-1 text-xs font-medium text-[var(--app-ink-soft)] transition-colors hover:text-[var(--app-ink)]"
          >
            Ouvrir la page
            <UIcon name="i-lucide-external-link" class="h-3 w-3" />
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import type { ComputedRef, Ref } from 'vue'
import { computed, ref, onMounted } from 'vue'
import type {
  WalletColorPalette,
  WalletProgram,
  WalletProgramCreatePayload,
  WalletProgramForm,
  WalletProgramStatus,
} from '~/types/WalletProgram'
import { WalletProgramService } from '~/services/walletProgramService'
import { useToast } from '~/composables/useToast'
import { useWalletEnrollLink } from '~/composables/useWalletEnrollLink'

definePageMeta({
  layout: 'dashboard',
  middleware: ['auth'],
})

/** Brand-color presets offered as one-tap ambiances. */
const PALETTES: WalletColorPalette[] = [
  {
    id: 'kebab',
    label: 'Kebab',
    background: 'rgb(23, 23, 23)',
    foreground: 'rgb(255, 255, 255)',
    labelColor: 'rgba(255, 255, 255, 0.62)',
  },
  {
    id: 'cafe',
    label: 'Café',
    background: 'rgb(60, 42, 33)',
    foreground: 'rgb(245, 236, 224)',
    labelColor: 'rgba(245, 236, 224, 0.6)',
  },
  {
    id: 'barber',
    label: 'Barbier',
    background: 'rgb(17, 24, 39)',
    foreground: 'rgb(233, 213, 160)',
    labelColor: 'rgba(233, 213, 160, 0.6)',
  },
  {
    id: 'institut',
    label: 'Institut',
    background: 'rgb(244, 232, 236)',
    foreground: 'rgb(60, 22, 44)',
    labelColor: 'rgba(60, 22, 44, 0.55)',
  },
  {
    id: 'primeur',
    label: 'Primeur',
    background: 'rgb(20, 83, 45)',
    foreground: 'rgb(240, 253, 244)',
    labelColor: 'rgba(240, 253, 244, 0.6)',
  },
]

/** Fallback palette when none matches (also the create default). */
const DEFAULT_PALETTE: WalletColorPalette = PALETTES[0] ?? {
  id: 'kebab',
  label: 'Kebab',
  background: 'rgb(23, 23, 23)',
  foreground: 'rgb(255, 255, 255)',
  labelColor: 'rgba(255, 255, 255, 0.62)',
}

/** Selectable program statuses (edit mode). */
const STATUSES: { value: WalletProgramStatus; label: string }[] = [
  { value: 'draft', label: 'Brouillon' },
  { value: 'active', label: 'Actif' },
  { value: 'archived', label: 'Archivé' },
]

const route: ReturnType<typeof useRoute> = useRoute()
const toast: ReturnType<typeof useToast> = useToast()

/** Whether we are creating a new program (route id === "new"). */
const isNew: boolean = route.params.id === 'new'

/** The edited program's id, or null in create mode. */
const programId: number | null = isNew ? null : Number(route.params.id)

const isLoading: Ref<boolean> = ref(!isNew)
const isSaving: Ref<boolean> = ref(false)

const { buildLink, buildQr }: ReturnType<typeof useWalletEnrollLink> = useWalletEnrollLink()
const publicToken: Ref<string | null> = ref(null)
const qrDataUrl: Ref<string> = ref('')
const linkCopied: Ref<boolean> = ref(false)

const form: Ref<WalletProgramForm> = ref({
  organizationName: '',
  stampsRequired: 10,
  rewardLabel: '',
  defaultChangeMessage: '',
  logoUrl: '',
  backgroundColor: DEFAULT_PALETTE.background,
  foregroundColor: DEFAULT_PALETTE.foreground,
  labelColor: DEFAULT_PALETTE.labelColor,
  status: 'draft',
})

/** Id of the palette matching the current colors, or "custom". */
const selectedPaletteId: ComputedRef<string> = computed(
  (): string =>
    PALETTES.find((palette: WalletColorPalette) => palette.background === form.value.backgroundColor)?.id ?? 'custom',
)

/** Illustrative stamp count on the preview. */
const sampleStamps: ComputedRef<number> = computed((): number =>
  Math.min(Math.max(1, Math.round(form.value.stampsRequired * 0.4)), Math.max(form.value.stampsRequired, 1)),
)

/** Soft stage backdrop tinted with the card color. */
const stageStyle: ComputedRef<Record<string, string>> = computed(
  (): Record<string, string> => ({
    background: `radial-gradient(120% 120% at 50% 0%, ${form.value.backgroundColor}22, transparent 70%)`,
  }),
)

/** The program's public enrollment link (empty until it has a token). */
const enrollLink: ComputedRef<string> = computed((): string => (publicToken.value ? buildLink(publicToken.value) : ''))

/**
 * Apply a palette preset to the form colors.
 * @param palette - The chosen palette.
 */
function applyPalette(palette: WalletColorPalette): void {
  form.value.backgroundColor = palette.background
  form.value.foregroundColor = palette.foreground
  form.value.labelColor = palette.labelColor
}

/** Copy the public enrollment link to the clipboard. */
async function copyLink(): Promise<void> {
  if (!enrollLink.value) {
    return
  }
  try {
    await navigator.clipboard.writeText(enrollLink.value)
    linkCopied.value = true
    setTimeout((): void => {
      linkCopied.value = false
    }, 1500)
  } catch {
    toast.error('Copie impossible')
  }
}

/** Load the edited program into the form. */
async function load(): Promise<void> {
  if (programId === null) {
    return
  }
  try {
    const program: WalletProgram = await WalletProgramService.get(programId)
    form.value = {
      organizationName: program.organizationName,
      stampsRequired: program.stampsRequired,
      rewardLabel: program.rewardLabel ?? '',
      defaultChangeMessage: program.defaultChangeMessage ?? '',
      logoUrl: program.logoUrl ?? '',
      backgroundColor: program.backgroundColor ?? DEFAULT_PALETTE.background,
      foregroundColor: program.foregroundColor ?? DEFAULT_PALETTE.foreground,
      labelColor: program.labelColor ?? DEFAULT_PALETTE.labelColor,
      status: program.status,
    }
    publicToken.value = program.publicToken
    if (program.publicToken) {
      qrDataUrl.value = await buildQr(program.publicToken)
    }
  } catch {
    toast.error('Programme introuvable')
    navigateTo('/dashboard/wallet')
  } finally {
    isLoading.value = false
  }
}

/** Build the create/update payload from the form. */
function buildPayload(): WalletProgramCreatePayload {
  const stamps: number = Math.min(Math.max(form.value.stampsRequired, 1), 12)
  return {
    organizationName: form.value.organizationName.trim(),
    stampsRequired: stamps,
    rewardLabel: form.value.rewardLabel.trim() || null,
    defaultChangeMessage: form.value.defaultChangeMessage.trim() || null,
    logoUrl: form.value.logoUrl.trim() || null,
    backgroundColor: form.value.backgroundColor,
    foregroundColor: form.value.foregroundColor,
    labelColor: form.value.labelColor,
  }
}

/** Create or save the program. */
async function save(): Promise<void> {
  if (!form.value.organizationName.trim()) {
    toast.error('Le nom du commerce est requis.')
    return
  }
  isSaving.value = true
  try {
    if (programId === null) {
      await WalletProgramService.create(buildPayload())
      toast.success('Programme créé')
    } else {
      await WalletProgramService.update(programId, { ...buildPayload(), status: form.value.status })
      toast.success('Programme enregistré')
    }
    navigateTo('/dashboard/wallet')
  } catch (error) {
    toast.error(error instanceof Error ? error.message : 'Enregistrement impossible')
  } finally {
    isSaving.value = false
  }
}

onMounted(async (): Promise<void> => {
  await load()
})
</script>
