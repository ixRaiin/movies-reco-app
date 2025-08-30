<!-- src/pages/Mood.vue -->
<template>
  <main class="min-h-screen bg-background text-text-primary">
    <!-- =============== HERO / MOOD PICKER =============== -->
    <section class="relative py-12 px-6 bg-radial-aurora text-center">
      <h1 class="text-4xl md:text-5xl font-extrabold mb-3 text-transparent bg-clip-text bg-grad-cyan-violet">
        Find movies by mood
      </h1>
      <p class="text-text-muted mb-8">Pick a vibe and let the neon guide you.</p>

      <!-- Mood chips + region -->
      <div class="flex flex-wrap items-center justify-center gap-2 md:gap-3">
        <button
          v-for="m in moods"
          :key="m.value"
          type="button"
          class="px-3 py-1.5 rounded-full text-sm transition overlay-glass hover:shadow-[var(--shadow-neon-cyan)]"
          :class="mood === m.value ? 'text-neon-cyan border-[color:var(--color-neon-cyan)]' : 'text-text-secondary'"
          @click="selectMood(m.value as MoodKey)"
          :aria-pressed="mood === m.value ? 'true' : 'false'"
        >
          {{ m.label }}
        </button>

        <div class="h-6 w-px bg-gradient-to-b from-transparent via-white/20 to-transparent mx-2 md:mx-3" aria-hidden="true"></div>

        <!-- Region -->
        <label class="sr-only" for="region">Region</label>
        <select
          id="region"
          v-model="region"
          class="overlay-glass px-3 py-1.5 rounded-full text-sm outline-none focus:ring-2 focus:ring-neon-violet"
          @change="applyQuery({ region, page: 1 })"
        >
          <option value="">Region: auto</option>
          <option v-for="r in regions" :key="r" :value="r">{{ r }}</option>
        </select>
      </div>
    </section>

    <!-- =============== STATUS / PAGING =============== -->
    <section class="px-6 py-6 max-w-7xl mx-auto">
      <div v-if="mood" class="flex items-end justify-between gap-3">
        <div>
          <h2 class="text-2xl font-bold">
            Picks for
            <span class="text-transparent bg-clip-text bg-grad-violet-magenta">“{{ mood }}”</span>
          </h2>
          <p class="text-text-muted text-sm">
            {{ totalText }}
          </p>
        </div>

        <div class="inline-flex items-center gap-2">
          <button
            class="px-3 py-1.5 rounded-lg border border-white/10 text-sm
                   hover:border-neon-cyan hover:shadow-[var(--shadow-neon-cyan)]
                   transition disabled:opacity-50"
            :disabled="page <= 1 || loading"
            @click="goPage(page - 1)"
          >
            Prev
          </button>
          <span class="text-sm text-text-secondary">{{ page }} / {{ totalPages || 1 }}</span>
          <button
            class="px-3 py-1.5 rounded-lg border border-white/10 text-sm
                   hover:border-neon-cyan hover:shadow-[var(--shadow-neon-cyan)]
                   transition disabled:opacity-50"
            :disabled="page >= totalPages || loading"
            @click="goPage(page + 1)"
          >
            Next
          </button>
        </div>
      </div>
    </section>

    <!-- =============== RESULTS =============== -->
    <section class="px-6 pb-12 max-w-7xl mx-auto">
      <!-- Loading -->
      <div v-if="loading" class="grid gap-6 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        <div v-for="n in 10" :key="n" class="aspect-[2/3] rounded-2xl bg-white/5 animate-pulse" />
      </div>

      <!-- Grid: CLEAN CARDS (poster + title only) -->
      <transition name="fade" mode="out-in">
        <div
          v-if="results.length && !loading"
          key="grid"
          class="grid gap-6 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5"
        >
          <div
            v-for="m in results"
            :key="m.id"
            class="cursor-pointer transition-transform duration-300 hover:scale-[1.02]"
            @click="openDetails(m.id)"
          >
            <div class="relative overflow-hidden rounded-2xl w-full aspect-[2/3] bg-black/30">
              <template v-if="posterUrl(m.poster_path)">
                <img
                  :src="posterUrl(m.poster_path, 'w342')!"
                  :srcset="posterSrcsetHQ(m.poster_path)"
                  sizes="(min-width: 1280px) 18vw, (min-width: 1024px) 22vw, (min-width: 768px) 30vw, 45vw"
                  width="342" height="513"
                  :alt="`${m.title} poster`"
                  class="w-full h-full object-cover rounded-2xl"
                  loading="lazy" decoding="async" referrerpolicy="no-referrer"
                />
              </template>
              <div v-else class="w-full h-full grid place-items-center text-text-muted">No poster</div>
            </div>
            <h3 class="mt-3 text-center font-semibold text-base md:text-lg leading-snug line-clamp-2">
              {{ m.title }}
            </h3>
          </div>
        </div>

        <!-- Empty -->
        <div v-else-if="mood && !loading" key="empty" class="overlay-glass p-8 text-center rounded-xl max-w-md mx-auto">
          <p class="text-4xl mb-3">✨</p>
          <p class="text-text-muted">No matches for this mood. Try another vibe.</p>
        </div>

        <!-- Idle -->
        <div v-else key="idle" class="overlay-glass p-8 text-center rounded-xl max-w-md mx-auto text-text-muted">
          Pick a mood to see recommendations.
        </div>
      </transition>

      <!-- Error -->
      <div v-if="error" class="mt-6 overlay-glass p-4 rounded-lg text-red-400">
        ❌ {{ error }}
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import { getMoodRecs, type Movie } from "../services/api"
import { posterUrl } from "../lib/img"

const route = useRoute()
const router = useRouter()

// Single source of truth for moods
const moods = [
  { value: "happy",     label: "Happy" },
  { value: "family",    label: "Family" },
  { value: "comedy",    label: "Comedy" },
  { value: "action",    label: "Action" },
  { value: "adventure", label: "Adventure" },
  { value: "drama",     label: "Drama" },
  { value: "thriller",  label: "Thriller" },
  { value: "horror",    label: "Horror" },
  { value: "sci-fi",    label: "Sci-Fi" },
  { value: "animated",  label: "Animated" },
] as const

// Derive union type from moods array
type MoodKey = typeof moods[number]["value"]

const regions = ["US", "GB", "CA", "AE", "KW", "DE", "FR", "IN"]

const mood = ref<MoodKey | "">("")
const region = ref<string>("")
const page = ref(1)
const totalPages = ref(0)
const results = ref<Movie[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const totalText = computed(() =>
  results.value.length
    ? `${results.value.length} results • page ${page.value}${totalPages.value ? ` of ${totalPages.value}` : ""}`
    : "No results yet"
)

function posterSrcsetHQ(path?: string | null) {
  if (!path) return undefined
  const s1 = posterUrl(path, "w342")
  const s2 = posterUrl(path, "w500")
  return `${s1} 1x, ${s2} 2x`
}

function openDetails(id: number) {
  router.push({ name: "details", params: { id } })
}

function applyQuery(q: { mood?: string | null; page?: number | null; region?: string | null }) {
  const next = new URLSearchParams(route.query as Record<string, string>)
  if (q.mood !== undefined) next.set("mood", q.mood ?? "")
  if (q.page !== undefined) next.set("page", q.page ? String(q.page) : "1")
  if (q.region !== undefined) {
    if (q.region) next.set("region", q.region)
    else next.delete("region")
  }
  if (!next.get("mood")) next.delete("mood")
  router.push({ name: "mood", query: Object.fromEntries(next.entries()) })
}

async function fetchMood() {
  if (!mood.value) return
  loading.value = true
  error.value = null
  results.value = []
  try {
    const res = await getMoodRecs(mood.value, page.value, region.value || undefined)
    results.value = res.results
    totalPages.value = res.total_pages || 0
  } catch (e: any) {
    error.value = e?.message || "Failed to load mood recommendations"
  } finally {
    loading.value = false
  }
}

function selectMood(m: MoodKey) {
  if (mood.value === m) return
  applyQuery({ mood: m, page: 1 })
}

function goPage(p: number) {
  const np = Math.max(1, p)
  applyQuery({ page: np })
}

function refreshFromRoute() {
  const qm = String(route.query.mood || "")
  const qp = Number(route.query.page || 1)
  const qr = String(route.query.region || "")

  // Narrow to known moods
  const supported = moods.map(m => m.value) as readonly string[]
  mood.value = (qm && supported.includes(qm)) ? (qm as MoodKey) : ""
  page.value = Number.isFinite(qp) && qp > 0 ? qp : 1
  region.value = qr || ""
  if (mood.value) fetchMood()
}

onMounted(() => {
  refreshFromRoute()
})

watch(() => route.fullPath, () => {
  refreshFromRoute()
})
</script>


<style>
.fade-enter-active, .fade-leave-active { transition: opacity .2s ease, transform .2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(6px); }
</style>
