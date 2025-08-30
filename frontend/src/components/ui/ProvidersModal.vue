<!-- src/components/ui/ProvidersModal.vue -->
<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 grid place-items-center bg-black/60 px-4"
    role="dialog"
    aria-modal="true"
    aria-labelledby="providers-title"
    @keydown.esc.prevent.stop="close"
    @keydown.tab.prevent="onTabCycle"
  >
    <div
      ref="dialog"
      class="w-full max-w-lg rounded-2xl bg-neutral-900 p-4 shadow-xl outline-none"
      tabindex="-1"
    >
      <div class="mb-3 flex items-center justify-between">
        <h3 id="providers-title" class="text-base font-semibold text-white">Where to watch</h3>
        <button
          ref="closeBtn"
          class="rounded px-2 py-1 text-slate-300 hover:bg-white/10"
          type="button"
          @click="close"
        >✕</button>
      </div>

      <div class="flex gap-4 border-b border-white/10" role="tablist" aria-label="Provider groups">
        <button :class="tabBtn('stream')" role="tab" :aria-selected="tab==='stream'" @click="tab='stream'">
          Streaming <span class="text-xs opacity-70">({{ providers.stream?.length || 0 }})</span>
        </button>
        <button :class="tabBtn('rent')" role="tab" :aria-selected="tab==='rent'" @click="tab='rent'">
          Rent <span class="text-xs opacity-70">({{ providers.rent?.length || 0 }})</span>
        </button>
        <button :class="tabBtn('buy')" role="tab" :aria-selected="tab==='buy'" @click="tab='buy'">
          Buy <span class="text-xs opacity-70">({{ providers.buy?.length || 0 }})</span>
        </button>
      </div>

      <div class="pt-3">
        <ProviderChips
          v-if="(tab==='stream' && providers.stream?.length) ||
                 (tab==='rent' && providers.rent?.length)   ||
                 (tab==='buy' && providers.buy?.length)"
          :items="tab==='stream' ? providers.stream : (tab==='rent' ? providers.rent : providers.buy)"
        />
        <p v-else class="text-sm text-slate-400">Not available in your region.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watchEffect, onMounted, onBeforeUnmount, nextTick } from "vue"
import ProviderChips from "./ProviderChips.vue"

const props = defineProps<{
  open: boolean
  providers: { stream: any[]; rent: any[]; buy: any[] }
  initialTab?: "stream" | "rent" | "buy"
  /** Optional: element to return focus to when modal closes */
  returnTo?: HTMLElement | null
}>()
const emit = defineEmits<{ (e: "close"): void }>()

const tab = ref<"stream" | "rent" | "buy">("stream")
const dialog = ref<HTMLDivElement | null>(null)
const closeBtn = ref<HTMLButtonElement | null>(null)

watchEffect(() => {
  tab.value = props.initialTab || "stream"
})

function tabBtn(name: "stream" | "rent" | "buy") {
  return [
    "pb-2 focus:outline-none",
    tab.value === name ? "border-b-2 border-white/80" : "opacity-70",
  ].join(" ")
}

function close() {
  emit("close")
  // restore focus on next tick to avoid racing the parent state
  nextTick(() => {
    props.returnTo?.focus?.()
  })
}

// Simple focus trap: keep focus within the dialog
function onTabCycle(e: KeyboardEvent) {
  const focusables = dialog.value?.querySelectorAll<HTMLElement>(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  )
  if (!focusables || focusables.length === 0) return
  const list = Array.from(focusables).filter(el => !el.hasAttribute("disabled"))
  const active = document.activeElement as HTMLElement | null
  const idx = Math.max(0, list.indexOf(active || list[0]))

  // Shift+Tab or Tab
  const nextIdx = (e.shiftKey ? (idx - 1 + list.length) : (idx + 1)) % list.length
  list[nextIdx].focus()
}

function trapFocus() {
  // focus dialog container, then close button if present
  dialog.value?.focus()
  closeBtn.value?.focus()
}

function keydownEscape(e: KeyboardEvent) {
  if (e.key === "Escape") {
    e.preventDefault()
    e.stopPropagation()
    close()
  }
}

onMounted(() => {
  document.addEventListener("keydown", keydownEscape)
})
onBeforeUnmount(() => {
  document.removeEventListener("keydown", keydownEscape)
})

watchEffect(async () => {
  if (props.open) {
    await nextTick()
    trapFocus()
  }
})
</script>
