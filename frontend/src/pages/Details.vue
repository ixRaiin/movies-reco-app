<template>
  <main class="relative min-h-screen text-text-primary">

    <!-- === HERO BACKDROP === -->
    <div class="absolute inset-0 pointer-events-none select-none">
      <div
        v-if="movie && posterUrl(movie.poster_path)"
        class="absolute inset-0"
        :style="{
          backgroundImage: `url(${posterUrl(movie.poster_path, 'w780')})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center'
        }"
        aria-hidden="true"
      />
      <!-- blur + darken + neon radial glaze -->
      <div class="absolute inset-0 backdrop-blur-xl bg-black/70"></div>
      <div class="absolute inset-0 bg-radial-aurora"></div>
    </div>

    <!-- === CONTENT WRAPPER === -->
    <div class="relative z-10 mx-auto max-w-7xl px-6 py-10 space-y-10">

    <!-- === HERO (full-bleed background with overlayed content) === -->
    <section v-if="movie" class="relative rounded-2xl overflow-hidden mb-8">
      <!-- Backdrop image -->
      <div
        class="h-[62vh] md:h-[72vh] bg-center bg-cover"
        :style="{
          backgroundImage: backdropStyle
        }"
        aria-hidden="true"
      />

      <!-- Overlays: dark gradient + neon aurora glaze -->
      <div class="absolute inset-0 pointer-events-none">
        <div class="absolute inset-0 bg-gradient-to-b from-black/20 via-black/55 to-[var(--color-background)]/95"></div>
        <div class="absolute inset-0 bg-radial-aurora opacity-70"></div>
      </div>

      <!-- Content on top of image -->
      <div class="absolute inset-0 z-10">
        <div class="mx-auto max-w-7xl h-full px-6 py-6 md:py-10 flex items-end">
          <div class="w-full max-w-3xl pb-4 md:pb-8">
            <!-- Title -->
            <h1 class="text-3xl md:text-5xl font-extrabold leading-tight text-transparent bg-clip-text bg-grad-cyan-violet">
              {{ movie.title }}
              <span v-if="movie.year" class="text-text-secondary font-semibold"> ({{ movie.year }})</span>
            </h1>

            <!-- Pills row -->
            <div class="mt-3 flex flex-wrap gap-2">
              <span v-if="movie.year" class="px-3 py-1 rounded-full text-sm bg-white/10 border border-white/15">
                <span class="inline-block align-middle mr-1 opacity-80" aria-hidden="true">
                  <svg width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M7 2v2H5a2 2 0 0 0-2 2v2h18V6a2 2 0 0 0-2-2h-2V2h-2v2H9V2zM3 10v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V10z"/></svg>
                </span>
                {{ movie.year }}
              </span>
              <span v-if="runtime" class="px-3 py-1 rounded-full text-sm bg-white/10 border border-white/15">
                <span class="inline-block align-middle mr-1 opacity-80" aria-hidden="true">
                  <svg width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M12 1a11 11 0 1 0 11 11A11.013 11.013 0 0 0 12 1m1 11.414l3.707 3.707l-1.414 1.414L11 13V6h2z"/></svg>
                </span>
                {{ runtime }}
              </span>
              <span v-if="rating" class="px-3 py-1 rounded-full text-sm bg-white/10 border border-white/15">
                <span class="inline-block align-middle mr-1 opacity-80" aria-hidden="true">
                  <svg width="16" height="16" viewBox="0 0 24 24"><path fill="currentColor" d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.62L12 2L9.19 8.62L2 9.24l5.46 4.73L5.82 21z"/></svg>
                </span>
                {{ rating }}
              </span>
              <span
                v-for="g in genres"
                :key="g"
                class="px-3 py-1 rounded-full text-sm bg-white/10 border border-white/15"
              >
                {{ g }}
              </span>
            </div>

            <!-- Overview -->
            <p class="mt-4 max-w-2xl text-text-secondary leading-relaxed">
              {{ movie.overview || 'No overview available.' }}
            </p>

            <!-- Actions -->
            <div class="mt-5 flex items-center gap-3">
              <a
                v-if="providers?.link"
                :href="providers.link"
                target="_blank"
                rel="noopener"
                class="px-4 py-2 rounded-xl text-sm font-semibold
                      bg-[color:var(--color-neon-red)]/90 text-white
                      hover:shadow-[0_0_18px_rgba(255,77,77,.7)]
                      transition focus:outline-none focus:ring-2 focus:ring-[color:var(--color-neon-red)]"
                aria-label="Watch now"
              >
                ▶ Watch Now
              </a>

              <button
                type="button"
                class="h-10 w-10 grid place-items-center rounded-full bg-white/10 border border-white/15
                      hover:border-[color:var(--color-neon-cyan)] hover:shadow-[var(--shadow-neon-cyan)]
                      transition"
                aria-label="Add to watchlist"
                title="Add to watchlist"
              >
                <svg width="18" height="18" viewBox="0 0 24 24"><path fill="currentColor" d="M6 2h12a2 2 0 0 1 2 2v18l-8-5l-8 5V4a2 2 0 0 1 2-2"/></svg>
              </button>

              <button
                type="button"
                class="h-10 w-10 grid place-items-center rounded-full bg-white/10 border border-white/15
                      hover:border-[color:var(--color-neon-violet)] hover:shadow-[var(--shadow-neon-violet)]
                      transition"
                aria-label="Share"
                title="Share"
              >
                <svg width="18" height="18" viewBox="0 0 24 24"><path fill="currentColor" d="m14 9l-1.41 1.41L15.17 13H10a5 5 0 0 0-5 5v1h2v-1a3 3 0 0 1 3-3h5.17l-2.58 2.59L14 19l5-5zM19 3h-6v2h6v6h2V5a2 2 0 0 0-2-2"/></svg>
              </button>

              <button
                type="button"
                class="h-10 w-10 grid place-items-center rounded-full bg-white/10 border border-white/15
                      hover:border-[color:var(--color-neon-cyan)] hover:shadow-[var(--shadow-neon-cyan)]
                      transition"
                aria-label="Show similar"
                title="Show similar"
                @click="scrollToSection('recs')"
              >
                <svg width="18" height="18" viewBox="0 0 24 24"><path fill="currentColor" d="M12 2L1 7l11 5l9-4.09V17h2V7zM1 17l11 5l11-5l-11-5z"/></svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>


      <!-- === CAST (scroll row) === -->
      <section v-if="cast.length" class="space-y-3">
        <div class="flex items-baseline gap-3">
          <h2 class="text-xl font-semibold text-transparent bg-clip-text bg-grad-violet-magenta">
            Top billed cast
          </h2>
          <button
            class="ml-auto px-3 py-1 rounded-full text-sm bg-white/5 border border-white/15 hover:border-neon-cyan hover:shadow-[var(--shadow-neon-cyan)] transition"
            type="button"
            title="View all"
            aria-label="View all cast"
          >
            View All
          </button>
        </div>

        <ul class="flex gap-5 overflow-x-auto scrollbar-hide snap-x snap-mandatory">
          <li
            v-for="c in cast"
            :key="c.id"
            class="snap-start flex-shrink-0 w-36 overlay-glass bg-background/50 rounded-2xl p-3"
          >
            <div class="w-full aspect-square rounded-xl overflow-hidden bg-black/30 mb-2">
              <img
                v-if="profileUrl(c.profile_path)"
                :src="profileUrl(c.profile_path)!"
                :alt="c.name"
                class="w-full h-full object-cover"
                loading="lazy"
                referrerpolicy="no-referrer"
              />
              <div v-else class="w-full h-full grid place-items-center text-text-muted">No photo</div>
            </div>
            <div class="space-y-0.5">
              <div class="font-semibold text-sm leading-tight">{{ c.name }}</div>
              <div v-if="c.character" class="text-xs text-text-muted leading-tight">as {{ c.character }}</div>
            </div>
          </li>
        </ul>
      </section>
      
      <!-- === PROVIDERS (Tabbed) === -->
      <section v-if="providers" class="space-y-4" aria-labelledby="providers-heading">
        <div class="flex items-baseline gap-3">
          <h2 id="providers-heading" class="text-xl font-semibold text-transparent bg-clip-text bg-grad-violet-magenta">
            Where to watch
          </h2>
          <a v-if="providers.link" :href="providers.link" target="_blank" class="text-sm text-neon-cyan underline">More on TMDb</a>
          <span class="text-xs text-text-muted">Region: {{ providers.region }}</span>
        </div>

        <!-- Tabs -->
        <div class="inline-flex rounded-xl overflow-hidden border border-white/10 bg-white/5" role="tablist" aria-label="Offer type">
          <button
            role="tab"
            :aria-selected="offerTab === 'flatrate'"
            class="px-4 py-2 text-sm transition border-r border-white/10"
            :class="offerTab === 'flatrate'
              ? 'text-neon-cyan bg-white/10 shadow-[var(--shadow-neon-cyan)]'
              : 'text-text-secondary hover:text-neon-violet'"
            @click="offerTab = 'flatrate'"
          >
            Streaming <span class="opacity-70">({{ offerCounts.flatrate }})</span>
          </button>
          <button
            role="tab"
            :aria-selected="offerTab === 'rent'"
            class="px-4 py-2 text-sm transition"
            :class="offerTab === 'rent'
              ? 'text-neon-cyan bg-white/10 shadow-[var(--shadow-neon-cyan)]'
              : 'text-text-secondary hover:text-neon-violet'"
            @click="offerTab = 'rent'"
          >
            Rent <span class="opacity-70">({{ offerCounts.rent }})</span>
          </button>
        </div>

        <!-- Offers list -->
        <div class="overlay-glass bg-background/50 rounded-2xl p-4">
          <div v-if="currentOffers.length" class="flex flex-wrap gap-3">
            <div
              v-for="p in currentOffers"
              :key="p.provider_id"
              class="inline-flex items-center gap-2 rounded-xl px-3 py-2 bg-white/5 border border-white/10
                    hover:border-neon-cyan hover:shadow-[var(--shadow-neon-cyan)] transition"
              :title="p.provider_name"
            >
              <img
                v-if="providerLogoUrl(p.logo_path)"
                :src="providerLogoUrl(p.logo_path)!"
                :alt="p.provider_name"
                class="h-6 w-auto"
                loading="lazy"
                referrerpolicy="no-referrer"
              />
              <span class="text-sm">{{ p.provider_name }}</span>
            </div>
          </div>
          <p v-else class="text-sm text-text-muted">No offers</p>
        </div>
      </section>

      <!-- === RECOMMENDATIONS === -->
      <section v-if="recs.length" :id="ids.recs" class="space-y-3">
        <div class="flex items-baseline gap-3">
          <h2 class="text-xl font-semibold text-transparent bg-clip-text bg-grad-cyan-violet">
            You may like
          </h2>
        </div>

        <ul class="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
          <li
            v-for="m in recs"
            :key="m.id"
            class="overlay-glass rounded-2xl overflow-hidden bg-background/60 cursor-pointer transition-transform duration-300 hover:scale-[1.02] hover:shadow-[var(--shadow-neon-cyan)]"
            @click="openDetails(m.id)"
          >
            <div class="w-full aspect-[2/3] bg-black/30">
              <img
                v-if="posterUrl(m.poster_path)"
                :src="posterUrl(m.poster_path)!"
                :alt="`${m.title} poster`"
                class="w-full h-full object-cover"
                loading="lazy"
                referrerpolicy="no-referrer"
              />
              <div v-else class="w-full h-full grid place-items-center text-text-muted">No poster</div>
            </div>
            <div class="p-3">
              <div class="font-semibold leading-snug line-clamp-2">{{ m.title }}</div>
              <div v-if="m.year" class="text-sm text-text-muted">({{ m.year }})</div>
            </div>
          </li>
        </ul>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import {
  getMovieDetails, getRecommendations, getProviders,
  type DetailsResponse, type Cast, type Movie, type RecommendationsResponse, type ProvidersResponse
} from "../services/api"
import { posterUrl, profileUrl, providerLogoUrl } from "../lib/img"
import { computed } from "vue"

const route = useRoute()
const router = useRouter()

const movie = ref<Movie | null>(null)
const cast = ref<Cast[]>([])
const loading = ref(true)
const error = ref<string | null>(null)

const recs = ref<Movie[]>([])
const recsSource = ref<"recommendations" | "similar" | null>(null)

const providers = ref<ProvidersResponse | null>(null)

/** Optional extra meta if you later add these fields on backend */
const runtime = ref<string | null>(null)     // e.g., "2h 8m"
const rating = ref<string | null>(null)      // e.g., "7.6/10"
const genres = ref<string[]>([])             // e.g., ["Action","Sci-Fi"]

const ids = { recs: "recs" }

const backdropStyle = computed(() => {
  const path = movie.value?.poster_path
  if (!path) return "none"
  const url = posterUrl(path, "w1280")
  return url ? `url('${url}')` : "none"
})


const offerTab = ref<"flatrate" | "rent">("flatrate")

const offerCounts = computed(() => ({
  flatrate: providers.value?.flatrate?.length ?? 0,
  rent: providers.value?.rent?.length ?? 0,
}))

const currentOffers = computed(() => {
  return offerTab.value === "flatrate"
    ? providers.value?.flatrate ?? []
    : providers.value?.rent ?? []
})

async function loadAll(id: number) {
  loading.value = true
  error.value = null
  try {
    const details: DetailsResponse = await getMovieDetails(id)
    movie.value = details.movie
    cast.value = details.cast

    // optional meta: if backend later exposes, map them here
    // runtime.value = details.movie.runtime ? `${Math.floor(details.movie.runtime/60)}h ${details.movie.runtime%60}m` : null
    // rating.value = details.movie.vote_average ? `${details.movie.vote_average.toFixed(1)}/10` : null
    // genres.value = details.movie.genres?.map((g:any)=>g.name) ?? []

    const r: RecommendationsResponse = await getRecommendations(id, 1)
    recs.value = r.results
    recsSource.value = r.source

    providers.value = await getProviders(id)
  } catch (e: any) {
    error.value = e?.message || "Failed to load movie"
  } finally {
    loading.value = false
  }
}

function openDetails(id: number) {
  router.push({ name: "details", params: { id } })
}
function scrollToSection(anchor: keyof typeof ids) {
  const el = document.getElementById(ids[anchor])
  if (el) el.scrollIntoView({ behavior: "smooth", block: "start" })
}

onMounted(() => {
  const id = Number(route.params.id)
  if (id) loadAll(id)
})
watch(() => route.params.id, (val) => {
  const id = Number(val)
  if (id) loadAll(id)
})
</script>

<style>
/* keep carousels tidy on small screens */
.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
</style>
