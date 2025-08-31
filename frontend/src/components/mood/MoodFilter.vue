<script setup lang="ts">
import { computed } from 'vue'

type MoodSlug = 'happy' | 'sad' | 'romantic' | 'thriller' | 'sci-fi' | 'action' | 'adventure' | 'horror'
type SortKey = 'featured' | 'newest' | 'rating' | 'popularity' | 'title'

const props = defineProps<{
  moods: Array<{ slug: MoodSlug; label: string; icon?: string }>
  activeMood: MoodSlug
  text: string
  yearMin: number
  yearMax: number
  hideSequels: boolean
  sortBy: SortKey
  navOffset?: number
}>()

const emit = defineEmits<{
  (e: 'update:activeMood', v: MoodSlug): void
  (e: 'update:text', v: string): void
  (e: 'update:yearMin', v: number): void
  (e: 'update:yearMax', v: number): void
  (e: 'update:hideSequels', v: boolean): void
  (e: 'update:sortBy', v: SortKey): void
}>()

const padTop = computed(() => `${(props.navOffset ?? 84) + 12}px`)
</script>

<template>
  <aside
    class="sticky left-0 w-[280px] max-w-[90vw] rounded-2xl overlay-glass p-4"
    :style="{ top: padTop }"
  >
    <h3 class="mb-3 text-sm font-semibold tracking-wide heading-pop">Mood Browser</h3>

    <!-- mood chips -->
    <div class="flex flex-wrap gap-2 mb-4">
      <button
        v-for="m in moods"
        :key="m.slug"
        @click="emit('update:activeMood', m.slug)"
        class="px-3 py-1.5 rounded-full border border-white/10 text-sm transition"
        :class="m.slug === activeMood ? 'bg-white/15' : 'bg-white/5 hover:bg-white/10'"
      >
        <span v-if="m.icon">{{ m.icon }}</span>
        <span class="ml-1">{{ m.label }}</span>
      </button>
    </div>

    <!-- text contains -->
    <label class="block text-xs text-white/60 mb-1">Title contains</label>
    <input
      class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 mb-3 focus:outline-none focus:ring-2 focus:ring-cyan-300/40"
      type="text" :value="text" placeholder="e.g., love, dark, space"
      @input="emit('update:text', ($event.target as HTMLInputElement).value)"
    />

    <!-- year range -->
    <label class="block text-xs text-white/60 mb-1">Year range</label>
    <div class="flex items-center gap-2 mb-3">
      <input
        class="w-20 rounded-lg bg-white/5 border border-white/10 px-2 py-1 focus:outline-none"
        type="number" :value="yearMin" min="1900" max="2100"
        @input="emit('update:yearMin', parseInt(($event.target as HTMLInputElement).value || '0'))"
      />
      <span class="text-white/40">—</span>
      <input
        class="w-20 rounded-lg bg-white/5 border border-white/10 px-2 py-1 focus:outline-none"
        type="number" :value="yearMax" min="1900" max="2100"
        @input="emit('update:yearMax', parseInt(($event.target as HTMLInputElement).value || '0'))"
      />
    </div>

    <!-- hide sequels -->
    <label class="flex items-center gap-2 mb-4 text-sm">
      <input
        type="checkbox" :checked="hideSequels"
        @change="emit('update:hideSequels', ($event.target as HTMLInputElement).checked)"
      />
      <span class="text-white/80">Hide obvious sequels/remakes</span>
    </label>

    <!-- sort -->
    <label class="block text-xs text-white/60 mb-1">Sort by</label>
    <select
      class="w-full rounded-lg bg-white/5 border border-white/10 px-3 py-2 focus:outline-none"
      :value="sortBy"
      @change="emit('update:sortBy', ($event.target as HTMLSelectElement).value as SortKey)"
    >
      <option value="featured">Featured</option>
      <option value="newest">Newest</option>
      <option value="rating">Rating</option>
      <option value="popularity">Popularity</option>
      <option value="title">Title (A–Z)</option>
    </select>
  </aside>
</template>
