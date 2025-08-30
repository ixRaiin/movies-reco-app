<template>
  <section
    class="overlay-glass rounded-2xl border border-white/10 bg-background/60 p-4 md:p-5"
    role="status"
    aria-live="polite"
  >
    <div class="flex items-start gap-3">
      <!-- Icon -->
      <div class="mt-0.5 grid h-9 w-9 place-items-center rounded-full bg-white/10 border border-white/15">
        <!-- warning triangle -->
        <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
          <path fill="currentColor" d="M1 21h22L12 2zm12-3h-2v2h2zm0-8h-2v6h2z"/>
        </svg>
      </div>

      <!-- Text -->
      <div class="flex-1">
        <h3 class="text-base font-semibold text-white">
          {{ title || defaultTitle }}
        </h3>
        <p v-if="message" class="mt-1 text-sm text-text-secondary">
          {{ message }}
          <span v-if="hint" class="block opacity-80">Hint: {{ hint }}</span>
        </p>

        <div class="mt-3 flex flex-wrap items-center gap-2 text-xs text-text-muted">
          <span v-if="code" class="rounded bg-white/5 px-2 py-0.5 border border-white/10">code: {{ code }}</span>
          <span v-if="dependency" class="rounded bg-white/5 px-2 py-0.5 border border-white/10">dep: {{ dependency }}</span>
          <span v-if="traceId" class="rounded bg-white/5 px-2 py-0.5 border border-white/10">trace: {{ traceId }}</span>
        </div>

        <!-- Actions -->
        <div class="mt-4 flex gap-2">
          <button
            v-if="retry"
            type="button"
            class="rounded-lg bg-white/10 px-3 py-1.5 text-sm font-medium hover:bg-white/20 focus:outline-none focus:ring"
            @click="retry"
          >
            Retry
          </button>
          <button
            v-if="onDetails"
            type="button"
            class="rounded-lg border border-white/15 px-3 py-1.5 text-sm hover:bg-white/5 focus:outline-none focus:ring"
            @click="onDetails"
          >
            Details
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
type Props = {
  title?: string
  message?: string
  hint?: string
  code?: string
  dependency?: string | null
  traceId?: string
  retry?: () => void
  onDetails?: () => void
}
const props = defineProps<Props>()
const defaultTitle = "Something went wrong"
</script>
