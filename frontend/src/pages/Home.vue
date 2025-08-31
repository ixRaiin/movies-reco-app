<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import HeroCarousel from '@/components/home/HeroCarousel.vue'
import ScrollableRow from '@/components/common/ScrollableRow.vue'
import { getTrending, getPopular } from '@/services/api'

type Movie = { id:number; title:string; poster_path:string | null }

// UI state
const windowRange = ref<'day' | 'week'>('day')
const loadingTrend = ref(false)
const loadingPopular = ref(false)
const error = ref<string | null>(null)

// Data
const trending = ref<Movie[]>([])
const popular = ref<Movie[]>([])

// Derived
const topTen = computed<Movie[]>(() => trending.value.slice(0, 10))

async function loadTrending() {
  loadingTrend.value = true
  try {
    const res = await getTrending(windowRange.value)
    trending.value = (res?.results ?? []) as Movie[]
  } catch (e: any) {
    error.value = e?.message || 'Failed to load trending.'
    trending.value = []
  } finally {
    loadingTrend.value = false
  }
}

async function loadPopular() {
  loadingPopular.value = true
  try {
    const res = await getPopular()
    popular.value = (res?.results ?? []) as Movie[]
  } catch (e: any) {
    error.value = e?.message || 'Failed to load popular.'
    popular.value = []
  } finally {
    loadingPopular.value = false
  }
}

function switchWindow(w: 'day' | 'week') {
  if (windowRange.value === w) return
  windowRange.value = w
  loadTrending()
}

onMounted(async () => {
  await Promise.allSettled([loadTrending(), loadPopular()])
})
</script>

<template>
  <!-- No local background; global fixed neon gradient is applied via #app::before -->
  <main class="px-4 sm:px-6 py-4 space-y-6">

    <!-- Header / Day-Week toggle (compact to save vertical space) -->
    <div class="flex items-center justify-between">
      <h1 class="heading-brand text-2xl sm:text-3xl font-extrabold">Discover</h1>
      <div class="flex gap-2">
        <button
          class="px-3 py-1 rounded border border-transparent hover:border-[color:var(--neon-cyan)]/60 hover:shadow-[0_0_18px_rgba(126,233,255,.25)] transition"
          :class="{ 'text-cyan-300 border-[color:var(--neon-cyan)]/60': windowRange === 'day' }"
          @click="switchWindow('day')"
        >
          Day
        </button>
        <button
          class="px-3 py-1 rounded border border-transparent hover:border-[color:var(--neon-cyan)]/60 hover:shadow-[0_0_18px_rgba(126,233,255,.25)] transition"
          :class="{ 'text-cyan-300 border-[color:var(--neon-cyan)]/60': windowRange === 'week' }"
          @click="switchWindow('week')"
        >
          Week
        </button>
      </div>
    </div>

    <!-- Top 10 (compact paddings; overlay arrows handled inside component) -->
    <div v-if="loadingTrend" class="grid gap-5 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
      <div v-for="n in 10" :key="n" class="rounded-2xl h-64 animate-pulse bg-white/5"></div>
    </div>
    <HeroCarousel v-else :items="topTen" />

    <!-- Popular Now -->
    <div v-if="loadingPopular" class="grid gap-5 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
      <div v-for="n in 10" :key="n" class="rounded-2xl h-64 animate-pulse bg-white/5"></div>
    </div>
    <ScrollableRow v-else :items="popular" title="Popular Now" />

    <!-- Trending Today / This Week -->
    <ScrollableRow
      v-if="!loadingTrend && trending.length"
      :items="trending"
      :title="`Trending • ${windowRange === 'day' ? 'Today' : 'This Week'}`"
    />

    <!-- Error (non-blocking) -->
    <p v-if="error" role="alert" class="text-sm text-red-300">{{ error }}</p>
  </main>
</template>
