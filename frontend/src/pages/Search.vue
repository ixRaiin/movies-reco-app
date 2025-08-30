<template>
  <main class="min-h-screen bg-background text-text-primary">
    <!-- === HERO / SEARCH BAR === -->
    <section class="relative py-12 px-6 bg-radial-aurora text-center">
      <h1 class="text-4xl md:text-5xl font-extrabold mb-4 text-transparent bg-clip-text bg-grad-cyan-violet">
        Discover Your Next Favorite
      </h1>
      <p class="text-text-muted mb-8">Search by movie, series, or genre</p>

      <form class="flex justify-center gap-3" @submit.prevent="performSearch(true)">
        <div class="overlay-glass flex items-center gap-2 px-4 py-2 w-full max-w-xl rounded-full">
          <input
            v-model.trim="q"
            type="search"
            placeholder="Search for movies…"
            class="bg-transparent flex-1 outline-none text-text-primary placeholder-text-muted
                   focus:ring-2 focus:ring-neon-cyan rounded-full px-2 py-1"
            aria-label="Search movies"
          />
          <button
            type="submit"
            class="p-2 rounded-full border border-neon-cyan hover:shadow-[var(--shadow-neon-cyan)] transition"
            aria-label="Search"
          >
            🔍
          </button>
        </div>
      </form>

      <p class="mt-3 text-sm text-text-muted" aria-live="polite">
        <span v-if="q && !loading && !err">
          {{ totalResults }} result(s) for “{{ q }}” • page {{ page }}{{ totalPages ? ` of ${totalPages}` : '' }}
        </span>
        <span v-else-if="loading">Searching…</span>
      </p>
    </section>

    <!-- === WHEN NO QUERY: Top 10 === -->
    <section v-if="!q" class="py-12 px-6 space-y-6">
      <h2 class="text-2xl font-bold bg-clip-text text-transparent bg-grad-violet-magenta mb-6">
        Top 10 This Week
      </h2>

      <div class="flex gap-6 overflow-x-auto scrollbar-hide snap-x snap-mandatory">
        <div
          v-for="(m, index) in top10"
          :key="m.id"
          class="relative snap-start flex-shrink-0 w-44 md:w-52 lg:w-60 cursor-pointer transition-transform duration-300 hover:scale-[1.03]"
          @click="openDetails(m.id)"
        >
          <span class="absolute -left-5 top-3 text-6xl md:text-7xl font-black text-neon-cyan/15 select-none">
            {{ index + 1 }}
          </span>

          <div class="relative overflow-hidden rounded-2xl w-full h-72 bg-black/30">
            <template v-if="posterUrl(m.poster_path)">
              <img
                :src="posterUrl(m.poster_path, 'w342')!"
                :srcset="posterSrcsetHQ(m.poster_path)"
                sizes="(min-width: 1024px) 12vw, (min-width: 768px) 18vw, 50vw"
                width="342" height="513"
                :alt="`${m.title} poster`"
                class="w-full h-full object-cover rounded-2xl"
                loading="lazy" decoding="async" referrerpolicy="no-referrer"
              />
            </template>
            <div v-else class="w-full h-full grid place-items-center text-text-muted">No poster</div>
          </div>

          <h3 class="mt-3 text-center font-semibold text-base md:text-lg line-clamp-2">
            {{ m.title }}
          </h3>
        </div>
      </div>
    </section>

    <!-- === WHEN QUERY: results + pager === -->
    <section v-else class="px-6 py-8 space-y-6">
      <header class="flex items-center justify-between gap-3">
        <div class="flex items-center gap-3">
          <h2 class="text-2xl font-bold">Search</h2>
          <span v-if="results.length" class="text-sm text-text-muted" aria-live="polite">
            Showing {{ results.length }} • page {{ page }}{{ totalPages ? ` of ${totalPages}` : '' }}
          </span>
        </div>

        <!-- Pager -->
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
      </header>

      <!-- Loading skeleton -->
      <div v-if="loading" class="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
        <div v-for="n in 10" :key="n" class="rounded-2xl bg-white/5 aspect-[2/3] animate-pulse" />
      </div>

      <!-- Error panel -->
      <ErrorPanel
        v-else-if="err"
        :title="'Search failed'"
        :message="err.message"
        :hint="err.hint || 'Check your network or try another query.'"
        :code="err.code"
        :dependency="err.dependency || undefined"
        :trace-id="err.trace_id"
        :retry="retry"
      />

      <!-- Results grid -->
      <TransitionGroup
        v-else-if="results.length"
        name="list-slide"
        tag="ul"
        class="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5"
      >
        <li
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
            <div v-else class="w-full h-full grid place-items-center text-text-muted">
              No poster
            </div>
          </div>
          <h3 class="mt-3 text-center font-semibold text-base md:text-lg leading-snug line-clamp-2">
            {{ m.title }}
          </h3>
        </li>
      </TransitionGroup>

      <!-- Empty state -->
      <div v-else class="overlay-glass p-8 text-center rounded-xl max-w-md mx-auto">
        <p class="text-4xl mb-3">🔎</p>
        <p class="text-text-muted">No matches found. Try a different title.</p>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { useRouter } from "vue-router"
import ErrorPanel from "../components/ui/ErrorPanel.vue"
import { posterUrl } from "../lib/img"
import { getTrending, searchMovies } from "../services/api"
import { parseApiError, type ApiErrorEnvelope } from "../lib/errors"

type LiteMovie = { id: number; title: string; year?: number; poster_path?: string | null }

const router = useRouter()

const q = ref("")
const page = ref(1)
const totalPages = ref(0)
const totalResults = ref(0)

const top10 = ref<LiteMovie[]>([])
const results = ref<LiteMovie[]>([])
const loading = ref(false)
const err = ref<ApiErrorEnvelope | null>(null)
let lastReq: { q: string; page: number } | null = null

function posterSrcsetHQ(path?: string | null) {
  if (!path) return undefined
  const s1 = posterUrl(path, "w342")
  const s2 = posterUrl(path, "w500")
  return `${s1} 1x, ${s2} 2x`
}

function normalize(movie: any): LiteMovie {
  return {
    id: movie.id,
    title: movie.title ?? movie.name ?? "Untitled",
    year: movie.release_date ? Number(String(movie.release_date).slice(0, 4)) : undefined,
    poster_path: movie.poster_path ?? null,
  }
}

async function performSearch(resetPage = false) {
  err.value = null
  if (!q.value.trim()) return
  if (resetPage) page.value = 1

  loading.value = true
  lastReq = { q: q.value, page: page.value }
  try {
    const data = await searchMovies(q.value, page.value)
    results.value = (data?.results || []).map(normalize)
    totalPages.value = Number(data?.total_pages || 0)
    totalResults.value = Number(data?.total_results || results.value.length)
  } catch (e) {
    err.value = await parseApiError(e)
  } finally {
    loading.value = false
  }
}

async function goPage(p: number) {
  page.value = Math.max(1, Math.min(p, totalPages.value || 1))
  await performSearch(false)
}

async function retry() {
  if (!lastReq) return
  q.value = lastReq.q
  page.value = lastReq.page
  await performSearch(false)
}

function openDetails(id: number) {
  router.push({ name: "details", params: { id } })
}

onMounted(async () => {
  try {
    const trending = await getTrending("week")
    top10.value = (trending?.results || []).slice(0, 10).map(normalize)
  } catch {
    top10.value = []
  }
})
</script>

<style scoped>
.list-slide-move,
.list-slide-enter-active,
.list-slide-leave-active { transition: all 0.25s ease; }
.list-slide-enter-from,
.list-slide-leave-to { opacity: 0; transform: translateY(6px); }
.list-slide-leave-active { position: absolute; }

/* hide native scrollbar */
.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
</style>
