<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, nextTick } from 'vue'
import { searchMovies, type SearchMovie, type SearchResponse } from '@/services/api'
import { useRatings, type UserRating } from '@/composables/useRatings'

/* === Ratings store ======================================================= */
const { rate, get: getRating, list: listRatings } = useRatings()

/* =========================================================================
   Relevance Ranker (Unicode-safe) + Personalization
=========================================================================== */
const W = {
  exact: 1200, starts: 500, whole: 250, position: 120,
  tokenCoverage: 40, fuzzy: 20, yearMatch: 22, yearProximity: 12,
  voteAvg: 8, popularity: 4, rarePenalty: -5,
  // personalization
  genreAffinity: 160,  // weight for favored genres
  favRecency: 40,      // small decade-based nudge
}

function escapeRegExp(s: string) { return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') }
function normalizeNumerals(s: string) {
  return s
    .replace(/\bii\b/g, '2').replace(/\biii\b/g, '3').replace(/\biv\b/g, '4')
    .replace(/\bvi\b/g, '6').replace(/\bvii\b/g, '7').replace(/\bviii\b/g, '8')
    .replace(/\bix\b/g, '9').replace(/\bx\b/g, '10')
}
function norm(s: string): string {
  return normalizeNumerals(
    (s || '').toLowerCase().normalize('NFKD')
      .replace(/\p{Diacritic}/gu, '')
      .replace(/[^\p{L}\p{N}\s]/gu, ' ')
      .replace(/\s+/g, ' ').trim()
  )
}
function bigrams(s: string) { const o:string[]=[]; for(let i=0;i<s.length-1;i++) o.push(s.slice(i,i+2)); return o }
function jaccard(a:string[], b:string[]) {
  if(!a.length||!b.length) return 0
  const A=new Set(a), B=new Set(b); let inter=0; for(const x of A) if(B.has(x)) inter++
  const union = new Set([...A,...B]).size
  return union ? inter/union : 0
}
function yearFrom(text: string): number | null {
  const m = text.match(/(?:^|\D)(19|20)\d{2}(?=\D|$)/)
  return m ? parseInt(m[0].match(/\d{4}/)![0], 10) : null
}

type Rankable = {
  id: number
  title?: string | null
  name?: string | null
  original_title?: string | null
  original_name?: string | null
  popularity?: number | null
  vote_average?: number | null
  vote_count?: number | null
  release_date?: string | null
  genre_ids?: number[]
}

/* --- Build user preference profile from ratings --- */
function buildProfile(ratings: UserRating[]) {
  const genreW = new Map<number, number>()
  const decadeW = new Map<number, number>()
  for (const r of ratings) {
    const w = Math.max(-1, Math.min(1, (r.rating - 3) / 2)) // 5★ -> +1 … 1★ -> -1
    for (const gid of r.genre_ids || []) {
      genreW.set(gid, (genreW.get(gid) || 0) + w)
    }
    const y = r.release_date?.slice(0,4)
    if (y && /^\d{4}$/.test(y)) {
      const decade = Math.floor(parseInt(y,10)/10)*10
      decadeW.set(decade, (decadeW.get(decade) || 0) + w)
    }
  }
  for (const [k,v] of genreW) genreW.set(k, Math.max(-1, Math.min(1, v)))
  for (const [k,v] of decadeW) decadeW.set(k, Math.max(-1, Math.min(1, v)))
  return { genreW, decadeW }
}

function personalBoost(m: Rankable, prof: ReturnType<typeof buildProfile>) {
  const gids = m.genre_ids || []
  let gScore = 0
  for (const gid of gids) gScore += (prof.genreW.get(gid) || 0)
  const genreAffinity = gids.length ? gScore / gids.length : 0 // [-1..+1]

  const y = m.release_date?.slice(0,4)
  let favRecency = 0
  if (y && /^\d{4}$/.test(y)) {
    const dec = Math.floor(parseInt(y,10)/10)*10
    favRecency = prof.decadeW.get(dec) ? Math.max(-1, Math.min(1, prof.decadeW.get(dec)!)) : 0
  }
  return W.genreAffinity * genreAffinity + W.favRecency * favRecency
}

function scoreAgainstTitle(nq:string, qTokens:string[], qBi:string[], t:string) {
  const exact = t === nq ? 1 : 0
  const starts = t.startsWith(nq) ? 1 : 0
  const wholeWordRe = new RegExp(`\\b${escapeRegExp(nq)}\\b`, 'u')
  const wholeHit = wholeWordRe.test(t) ? 1 : 0
  const coverage = qTokens.length ? qTokens.filter(tok => t.includes(tok)).length / qTokens.length : 0
  const fuzzy = jaccard(qBi, bigrams(t))
  const idxPos = t.indexOf(nq)
  const posScore = idxPos >= 0 ? 1 - (idxPos / Math.max(1, t.length - nq.length + 1)) : 0
  return { exact, starts, wholeHit, coverage, fuzzy, posScore }
}

function rankByRelevance<T extends Rankable>(
  query: string,
  items: T[],
  profile: ReturnType<typeof buildProfile>
): T[] {
  const nqRaw = norm(query)
  if (!nqRaw) return items

  const shortQ = nqRaw.length <= 2
  const Wf = {
    ...W,
    fuzzy: shortQ ? W.fuzzy * 0.3 : W.fuzzy,
    tokenCoverage: shortQ ? W.tokenCoverage * 0.5 : W.tokenCoverage,
    starts: shortQ ? W.starts * 1.3 : W.starts,
  }

  const qTokens = nqRaw.split(' ').filter(Boolean)
  const qBi = bigrams(nqRaw)
  const qYear = yearFrom(query)
  const popMax = Math.max(...items.map(i => i.popularity || 0), 1)

  const scored = items.map((m, idx) => {
    const baseTitle = m.title || m.name || ''
    const altTitle  = m.original_title || m.original_name || ''
    const t = norm(baseTitle)
    const tAlt = norm(altTitle)

    const s1 = scoreAgainstTitle(nqRaw, qTokens, qBi, t)
    const s2 = scoreAgainstTitle(nqRaw, qTokens, qBi, tAlt)

    const exact = Math.max(s1.exact, s2.exact)
    const starts = Math.max(s1.starts, s2.starts)
    const wholeHit = Math.max(s1.wholeHit, s2.wholeHit)
    const coverage = Math.max(s1.coverage, s2.coverage)
    const fuzzy = Math.max(s1.fuzzy, s2.fuzzy)
    const posScore = Math.max(s1.posScore, s2.posScore)

    const titleYear =
      yearFrom(baseTitle) ||
      yearFrom(altTitle) ||
      (m.release_date ? parseInt(m.release_date.slice(0, 4) || '') : null)
    const yearMatch = qYear && titleYear === qYear ? 1 : 0
    const yearDistance = qYear && titleYear ? Math.min(20, Math.abs(qYear - titleYear)) : null
    const yearProximity = yearDistance != null ? (1 - yearDistance / 20) : 0

    const vote = (m.vote_average || 0) / 10
    const pop = Math.min((m.popularity || 0) / popMax, 1)
    const rarePenalty = (m.vote_count || 0) < 10 ? Wf.rarePenalty : 0

    const pBoost = personalBoost(m, profile)

    const score =
      Wf.exact * exact +
      Wf.starts * starts +
      Wf.whole * wholeHit +
      Wf.position * posScore +
      Wf.tokenCoverage * coverage +
      Wf.fuzzy * fuzzy +
      Wf.yearMatch * yearMatch +
      Wf.yearProximity * yearProximity +
      Wf.voteAvg * vote +
      Wf.popularity * pop +
      rarePenalty +
      pBoost

    return { m, score, idx }
  })

  scored.sort((a, b) =>
    b.score - a.score ||
    (b.m.vote_count || 0) - (a.m.vote_count || 0) ||
    (b.m.vote_average || 0) - (a.m.vote_average || 0) ||
    (b.m.popularity || 0) - (a.m.popularity || 0) ||
    a.idx - b.idx
  )
  return scored.map(s => s.m)
}

/* =========================================================================
   State
=========================================================================== */
const q = ref<string>('')               // search box
const language = ref('en-US')

const results = ref<SearchMovie[]>([])
const page = ref(1)
const totalPages = ref(0)
const loading = ref(false)
const error = ref<string | null>(null)
const hasSearched = ref(false)

/* Recent searches */
const RECENT_KEY = 'cine.recent.searches'
const recent = ref<string[]>([])
function loadRecent(){ try{recent.value=JSON.parse(localStorage.getItem(RECENT_KEY)||'[]')}catch{recent.value=[]} }
function pushRecent(term: string){
  const arr = [term, ...recent.value.filter(t => t !== term)].slice(0, 8)
  recent.value = arr
  localStorage.setItem(RECENT_KEY, JSON.stringify(arr))
}
function clearRecent(){ recent.value=[]; localStorage.removeItem(RECENT_KEY) }

/* Helpers */
function reset(){ results.value=[]; page.value=1; totalPages.value=0; error.value=null }

/* Search runner with personalization */
let inflight: AbortController | null = null
async function runSearch(term: string, { append = false } = {}) {
  const s = term.trim()
  if (!s) { reset(); hasSearched.value = false; return }

  if (!append) reset()
  loading.value = true
  error.value = null

  inflight?.abort()
  inflight = new AbortController()

  try {
    const res: SearchResponse = await searchMovies(s, page.value, language.value)
    const items = (res?.results || []).filter(m => m?.id && m?.poster_path)

    const pool = append ? results.value.concat(items) : items
    const prof = buildProfile(listRatings())
    results.value = rankByRelevance<SearchMovie & Rankable>(q.value, pool, prof)

    totalPages.value = res?.total_pages || 0
    hasSearched.value = true
    if (!append) pushRecent(s)
  } catch (e: any) {
    if (e?.name !== 'AbortError') error.value = e?.message || 'Search failed.'
  } finally {
    loading.value = false
  }
}

/* Debounce */
let debounceId: number | null = null
function debouncedSearch(){
  if (debounceId) window.clearTimeout(debounceId)
  debounceId = window.setTimeout(() => runSearch(q.value), 300)
}

/* Infinite scroll */
const ioTarget = ref<HTMLElement | null>(null)
let io: IntersectionObserver | null = null
function setupIO(){
  if (!ioTarget.value) return
  io = new IntersectionObserver(async entries => {
    const e = entries[0]
    if (!e?.isIntersecting || loading.value || page.value >= totalPages.value) return
    page.value += 1
    await runSearch(q.value, { append: true })
  },{ rootMargin: '800px 0px 0px 0px', threshold: 0 })
  io.observe(ioTarget.value)
}

/* Lifecycle */
onMounted(()=>{ loadRecent(); setupIO() })
onBeforeUnmount(()=>{ io?.disconnect(); inflight?.abort() })

/* URL ?q= bootstrap */
const urlQ = new URLSearchParams(location.search).get('q') || ''
if (urlQ) { q.value = urlQ; runSearch(q.value) }

/* Derived */
const emptyState = computed(() =>
  hasSearched.value && !loading.value && !results.value.length && !error.value
)

/* OPTIONAL: user-rated movies sorted by relevancy to current query */
function ratedByRelevancyTo(query: string) {
  const prof = buildProfile(listRatings())
  const rated = listRatings().map(r => ({
    id: r.id,
    title: r.title || '',
    poster_path: r.poster_path ?? null,
    genre_ids: r.genre_ids ?? [],
    release_date: r.release_date ?? null,
    vote_average: 0, vote_count: 0, popularity: 0,
  }))
  return rankByRelevance<Rankable>(query, rated, prof)
}
</script>

<template>
  <main class="mx-auto max-w-7xl px-4 sm:px-6 py-6">
    <!-- Title -->
    <div class="mb-5 flex items-end justify-between gap-4">
      <h1 class="heading heading-top10 halo text-3xl sm:text-4xl font-extrabold">
        Search
      </h1>
      <div class="text-sm text-[color:var(--text-secondary)]" v-if="hasSearched && results.length">
        {{ results.length }} results · page {{ page }} / {{ totalPages }}
      </div>
    </div>

    <!-- Input -->
    <form class="overlay-glass rounded-2xl p-2 flex items-center gap-2" @submit.prevent="runSearch(q)">
      <input
        v-model="q"
        type="search"
        inputmode="search"
        placeholder="Search for a movie title…"
        class="bg-transparent flex-1 px-3 py-2 text-base outline-none"
        @input="debouncedSearch"
        aria-label="Search movies"
      />
      <select v-model="language" class="bg-transparent rounded-md px-2 py-2 text-sm outline-none border border-white/10">
        <option value="en-US">EN</option>
        <option value="fr-FR">FR</option>
        <option value="de-DE">DE</option>
        <option value="es-ES">ES</option>
        <option value="ja-JP">JA</option>
      </select>
      <button class="carousel-chev-lg" type="submit" aria-label="Run search">🔎</button>
    </form>

    <!-- Recent searches -->
    <div v-if="recent.length && !hasSearched" class="mt-4 flex flex-wrap gap-2 items-center">
      <button
        v-for="r in recent" :key="r"
        @click="q=r; nextTick(() => runSearch(q))"
        class="px-3 py-1 rounded-full text-sm border border-white/10 bg-white/5 hover:bg-white/10 transition"
      >
        {{ r }}
      </button>

      <!-- Clear history button -->
      <button
        @click="clearRecent"
        class="ml-3 px-3 py-1 rounded-full text-sm text-red-300 border border-red-300/30 bg-red-500/10 hover:bg-red-500/20 transition"
      >
        Clear
      </button>
    </div>


    <!-- Error -->
    <p v-if="error" role="alert" class="mt-6 text-red-300">
      {{ error }}
    </p>

    <!-- Empty -->
    <div v-if="emptyState" class="overlay-glass rounded-2xl p-8 mt-6 text-center">
      <p class="text-text-secondary">No results yet. Try a different title or language.</p>
    </div>

    <!-- Results -->
    <section v-if="results.length" class="mt-6">
      <div class="grid gap-6 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
        <RouterLink
          v-for="m in results"
          :key="m.id"
          :to="{ name: 'details', params: { id: m.id } }"
          class="tile row-tile group outline-none"
          :aria-label="`Open details for ${m.title}`"
        >
          <img
            class="hero-img"
            :src="`https://image.tmdb.org/t/p/w342${m.poster_path}`"
            :alt="m.title"
            loading="lazy"
            referrerpolicy="no-referrer"
          />
          <div class="img-overlay opacity-0 group-hover:opacity-100 transition"></div>
          <div class="mt-3 px-1">
            <h3 class="font-semibold text-sm line-clamp-2">{{ m.title }}</h3>
            <p class="text-[12px] text-text-secondary line-clamp-2">
              {{ m.overview || ' ' }}
            </p>
          </div>
        </RouterLink>
      </div>

      <!-- sentinel for infinite scroll -->
      <div ref="ioTarget" class="h-12"></div>

      <!-- Loading more skeletons -->
      <div v-if="loading" class="grid gap-6 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 mt-4">
        <div v-for="n in 10" :key="n" class="overlay-glass rounded-2xl h-64 animate-pulse bg-white/5"></div>
      </div>
    </section>

    <!-- First load skeletons -->
    <div v-else-if="loading" class="grid gap-6 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 mt-6">
      <div v-for="n in 10" :key="n" class="overlay-glass rounded-2xl h-64 animate-pulse bg-white/5"></div>
    </div>
  </main>
</template>
