<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import MoodFilter from '@/components/mood/MoodFilter.vue'
import { getMoodRecs, type Movie, type MoodResponse } from '@/services/api'

/** height of your sticky navbar (px) */
const NAV_OFFSET = 84

type MoodSlug = 'happy' | 'sad' | 'romantic' | 'thriller' | 'sci-fi' | 'action' | 'adventure' | 'horror'
type SortKey = 'featured' | 'newest' | 'rating' | 'popularity' | 'title'

const MOODS: Array<{ slug: MoodSlug; label: string; icon?: string }> = [
  { slug: 'happy',     label: 'Happy',     icon: '😊' },
  { slug: 'sad',       label: 'Sad',       icon: '🫶' },
  { slug: 'romantic',  label: 'Romantic',  icon: '💗' },
  { slug: 'thriller',  label: 'Thriller',  icon: '🗝️' },
  { slug: 'sci-fi',    label: 'Sci-Fi',    icon: '🛸' },
  { slug: 'action',    label: 'Action',    icon: '⚡' },
  { slug: 'adventure', label: 'Adventure', icon: '🏔️' },
  { slug: 'horror',    label: 'Horror',    icon: '👻' },
]

/* ---------------- state ---------------- */
const activeMood = ref<MoodSlug>('happy')
const textFilter = ref('')
const yearMin = ref(2000)
const yearMax = ref(new Date().getFullYear())
const hideSequels = ref(true)
const sortBy = ref<SortKey>('featured')

const pool = ref<Movie[]>([])
const page = ref(1)
const totalPages = ref(0)
const loading = ref(false)
const error = ref<string | null>(null)

/* ---------------- fetch ---------------- */
async function fetchMood(reset = false) {
  if (loading.value) return
  if (reset) {
    page.value = 1
    pool.value = []
    totalPages.value = 0
    error.value = null
  }
  loading.value = true
  try {
    const res: MoodResponse = await getMoodRecs(activeMood.value, page.value)
    const items = (res?.results || []).filter(m => m?.id && m?.poster_path)
    pool.value = reset ? items : pool.value.concat(items)
    totalPages.value = res?.total_pages || 1
  } catch (e: any) {
    error.value = e?.message || 'Failed to fetch mood results.'
  } finally {
    loading.value = false
  }
}
function loadMore() {
  if (!loading.value && page.value < totalPages.value) {
    page.value += 1
    fetchMood(false)
  }
}

/* ---------------- filters & intent ---------------- */
const G = { DRAMA: 18, COMEDY: 35, HORROR: 27, ROMANCE: 10749, SCIFI: 878 }

function hasGenre(m: Movie, id: number) {
  const ids = (m as any).genre_ids as number[] | undefined
  return Array.isArray(ids) && ids.includes(id)
}
function includesAny(txt: string, arr: string[]) {
  const t = txt.toLowerCase()
  return arr.some(k => t.includes(k))
}

function matchesIntent(m: Movie, mood: MoodSlug) {
  const title = m.title || ''
  const overview = (m as any).overview || ''
  const blob = `${title} ${overview}`.toLowerCase()

  switch (mood) {
    case 'romantic': {
      const romance = ['romance','romantic','love','lovers','relationship','wedding','bride','valentine','soulmate','honeymoon','heartwarming']
      const hit = includesAny(blob, romance)
      const isRomance = hasGenre(m, G.ROMANCE)
      const isRomCom = hasGenre(m, G.COMEDY) && hit
      const isHorror = hasGenre(m, G.HORROR)
      if (isHorror && !(isRomance || isRomCom || hit)) return false
      return isRomance || isRomCom || hit
    }
    case 'sad': {
      const positiveStruggle = ['inspire','inspiring','uplifting','hope','resilience','overcome','overcoming','survive','survival','perseverance','underdog','dream','true story','biographical','based on a true story','redemption','heartwarming']
      const bleak = ['slasher','serial killer','possession','gore','massacre']
      if (includesAny(blob, bleak)) return false
      if (hasGenre(m, G.HORROR)) return false
      const dramaish = hasGenre(m, G.DRAMA) || includesAny(blob, ['drama'])
      return includesAny(blob, positiveStruggle) || dramaish
    }
    case 'sci-fi': {
      const scifi = ['sci-fi','science fiction','space','spaceship','alien','android','robot','future','futuristic','time travel','time-travel','multiverse','cyberpunk','dystopia','post-apocalyptic','galaxy','planet']
      return hasGenre(m, G.SCIFI) || includesAny(blob, scifi)
    }
    default:
      return true
  }
}

function withinYear(m: Movie) {
  const y = parseInt((m as any).year || (m as any).release_date?.slice(0, 4) || '', 10)
  if (Number.isNaN(y)) return true
  return y >= yearMin.value && y <= yearMax.value
}
function textMatch(m: Movie) {
  const q = textFilter.value.trim().toLowerCase()
  if (!q) return true
  const t = (m.title || '').toLowerCase()
  const ov = ((m as any).overview || '').toLowerCase()
  return t.includes(q) || ov.includes(q)
}
function isObviousSequel(t: string) {
  const s = (t || '').toLowerCase()
  const words = ['part ','chapter ','episode ','season ','sequel','remake','reboot']
  const roman = /\b(ii|iii|iv|v|vi|vii|viii|ix|x)\b/i
  const numeric = /\b\d{1,2}\b/
  return words.some(w => s.includes(w)) || roman.test(s) || numeric.test(s)
}

function applyFilters(arr: Movie[]) {
  let out = arr.filter(m => matchesIntent(m, activeMood.value))
  if (hideSequels.value) out = out.filter(m => !isObviousSequel(m.title || ''))
  out = out.filter(withinYear).filter(textMatch)

  switch (sortBy.value) {
    case 'newest':
      out = [...out].sort((a, b) => ((b as any).release_date || '').localeCompare((a as any).release_date || ''))
      break
    case 'rating':
      out = [...out].sort((a: any, b: any) => (b.vote_average || 0) - (a.vote_average || 0))
      break
    case 'popularity':
      out = [...out].sort((a: any, b: any) => (b.popularity || 0) - (a.popularity || 0))
      break
    case 'title':
      out = [...out].sort((a, b) => (a.title || '').localeCompare(b.title || ''))
      break
    default:
      break
  }
  return out
}

const visible = computed(() => applyFilters(pool.value))

/* ---------------- watchers/lifecycle ---------------- */
watch(activeMood, () => fetchMood(true))
onMounted(() => {
  fetchMood(true)
  window.addEventListener('scroll', onScroll, { passive: true })
})
onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll as any)
})
function onScroll() {
  const nearBottom = window.innerHeight + window.scrollY >= document.body.offsetHeight - 1200
  if (nearBottom) loadMore()
}

const moods = MOODS
</script>

<template>
  <main class="max-w-7xl mx-auto px-4 pb-24">
    <!-- header -->
    <header class="pt-8 mb-6">
      <h1 class="text-3xl font-extrabold heading-pop">Mood Browser</h1>
    </header>

    <div class="grid grid-cols-12 gap-6">
      <!-- sticky sidebar -->
      <div class="col-span-12 md:col-span-3">
        <MoodFilter
          :moods="moods"
          v-model:activeMood="activeMood"
          v-model:text="textFilter"
          v-model:yearMin="yearMin"
          v-model:yearMax="yearMax"
          v-model:hideSequels="hideSequels"
          v-model:sortBy="sortBy"
          :navOffset="NAV_OFFSET"
        />
      </div>

      <!-- results -->
      <section class="col-span-12 md:col-span-9">
        <div v-if="error" class="text-red-300 mb-4">{{ error }}</div>

        <div
          class="grid gap-6"
          :class="{
            'grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5': true
          }"
        >
          <RouterLink
            v-for="m in visible"
            :key="m.id"
            :to="`/details/${m.id}`"
            class="tile row-tile group"
          >
            <img
              class="hero-img"
              :alt="m.title"
              :src="`https://image.tmdb.org/t/p/w500${m.poster_path}`"
              loading="lazy"
            />
            <div class="mt-2 text-sm text-white/90 truncate">{{ m.title }}</div>
            <div class="text-xs text-white/50">
              {{ (m as any).year || (m as any).release_date?.slice(0,4) || '' }}
            </div>
          </RouterLink>
        </div>

        <!-- load more -->
        <div class="flex justify-center mt-10" v-if="!loading && page < totalPages">
          <button
            class="px-4 py-2 rounded-lg bg-white/10 border border-white/15 hover:bg-white/15 transition"
            @click="loadMore"
          >
            Load more
          </button>
        </div>

        <div class="text-center text-white/60 mt-10" v-if="loading">Loading…</div>
        <div class="text-center text-white/60 mt-10" v-if="!loading && !visible.length">No results.</div>
      </section>
    </div>
  </main>
</template>
