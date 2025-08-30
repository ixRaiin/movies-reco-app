<script setup lang="ts">
import { providerLogoUrl } from "../../lib/img"  // adjust if you use @ alias
type ProviderItem = { id:number; name:string; logoPath:string|null; link?:string }
defineProps<{ items: ProviderItem[] }>()
const logoSrc = (p: ProviderItem) => providerLogoUrl(p.logoPath, "w92")
const open = (url?: string) => url && window.open(url, "_blank", "noopener")
</script>

<template>
  <div v-if="items?.length" class="flex flex-wrap gap-2">
    <button
      v-for="p in items"
      :key="p.id"
      type="button"
      class="inline-flex items-center gap-2 rounded-full border border-white/10 px-3 py-1 text-sm hover:bg-white/5"
      @click="open(p.link)"
      :aria-label="`Open ${p.name}`"
    >
      <img
        v-if="logoSrc(p)"
        :src="logoSrc(p)!"
        :alt="p.name"
        width="24" height="24" loading="lazy" class="rounded"
      />
      <div v-else class="grid h-6 w-6 place-items-center rounded bg-white/10 text-[10px] uppercase">
        {{ (p.name || "?").slice(0, 2) }}
      </div>
      <span class="truncate max-w-[14ch]" :title="p.name">{{ p.name }}</span>
    </button>
  </div>

  <p v-else class="text-sm text-slate-400">No providers available.</p>
</template>
