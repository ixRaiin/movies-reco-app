<!-- src/pages/Details.vue -->
<template>
  <main class="relative min-h-screen text-text-primary">
    <!-- Backdrop (poster blur) -->
    <div class="absolute inset-0 pointer-events-none select-none">
      <div
        v-if="movie && movie.poster_path && posterUrl(movie.poster_path, 'w780')"
        class="absolute inset-0"
        :style="{ backgroundImage: `url(${posterUrl(movie.poster_path, 'w780')})`, backgroundSize:'cover', backgroundPosition:'center' }"
        aria-hidden="true"
      />
      <div class="absolute inset-0 backdrop-blur-xl bg-black/70"></div>
      <div class="absolute inset-0 bg-radial-aurora"></div>
    </div>

    <div class="relative z-10 mx-auto max-w-7xl px-6 py-10 space-y-10">
      <!-- SKELETON -->
      <section v-if="loading" class="space-y-6">
        <div class="h-[52vh] rounded-2xl bg-white/5 animate-pulse" />
        <div class="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
          <div v-for="n in 10" :key="n" class="aspect-[2/3] rounded-2xl bg-white/5 animate-pulse" />
        </div>
      </section>

      <!-- ERROR -->
      <ErrorPanel
        v-else-if="error"
        :title="'Failed to load details'"
        :message="error.message"
        :hint="error.hint || 'Try again shortly.'"
        :code="error.code"
        :dependency="error.dependency || undefined"
        :trace-id="error.trace_id"
        :retry="() => loadAll(Number(route.params.id))"
      />

      <!-- CONTENT -->
      <section v-else-if="movie" class="relative rounded-2xl overflow-hidden mb-8">
        <div class="h-[62vh] md:h-[72vh] bg-center bg-cover" :style="{ backgroundImage: backdropStyle }" aria-hidden="true"/>
        <div class="absolute inset-0 pointer-events-none">
          <div class="absolute inset-0 bg-gradient-to-b from-black/20 via-black/55 to-[var(--color-background)]/95"></div>
          <div class="absolute inset-0 bg-radial-aurora opacity-70"></div>
        </div>

        <div class="absolute inset-0 z-10">
          <div class="mx-auto max-w-7xl h-full px-6 py-6 md:py-10 flex items-end">
            <div class="w-full max-w-3xl pb-4 md:pb-8">
              <h1 class="text-3xl md:text-5xl font-extrabold leading-tight text-transparent bg-clip-text bg-grad-cyan-violet">
                {{ movie.title }} <span v-if="movie.year" class="text-text-secondary font-semibold"> ({{ movie.year }})</span>
              </h1>

              <div class="mt-3 flex flex-wrap gap-2">
                <span v-if="movie.year" class="px-3 py-1 rounded-full text-sm bg-white/10 border border-white/15">{{ movie.year }}</span>
                <span v-if="runtime" class="px-3 py-1 rounded-full text-sm bg-white/10 border border-white/15">{{ runtime }}</span>
                <span v-if="rating" class="px-3 py-1 rounded-full text-sm bg-white/10 border border-white/15">{{ rating }}</span>
                <span v-for="g in genres" :key="g" class="px-3 py-1 rounded-full text-sm bg-white/10 border border-white/15">{{ g }}</span>
              </div>

              <p class="mt-4 max-w-2xl text-text-secondary leading-relaxed">
                {{ movie.overview || 'No overview available.' }}
              </p>

              <div class="mt-5 flex items-center gap-3">
                <button
                  ref="watchNowBtn"
                  type="button"
                  class="px-4 py-2 rounded-xl text-sm font-semibold bg-[color:var(--color-neon-red)]/90 text-white hover:shadow-[0_0_18px_rgba(255,77,77,.7)] transition"
                  @click="openProviders"
                >
                  ▶ Watch Now
                </button>
                <!-- other buttons omitted -->
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- CAST -->
      <section v-if="!loading && cast.length" class="space-y-3">
        <h2 class="text-xl font-semibold text-transparent bg-clip-text bg-grad-violet-magenta">Top billed cast</h2>
        <ul class="flex gap-5 overflow-x-auto scrollbar-hide snap-x snap-mandatory">
          <li v-for="c in cast" :key="c.id" class="snap-start flex-shrink-0 w-36 overlay-glass bg-background/50 rounded-2xl p-3">
            <div class="w-full aspect-square rounded-xl overflow-hidden bg-black/30 mb-2">
              <template v-if="profileUrl(c.profile_path)">
                <img
                  :src="profileUrl(c.profile_path)!"
                  width="185" height="185"
                  :alt="c.name"
                  class="w-full h-full object-cover"
                  loading="lazy" referrerpolicy="no-referrer"
                />
              </template>
              <div v-else class="w-full h-full grid place-items-center text-text-muted">No photo</div>
            </div>
            <div class="space-y-0.5">
              <div class="font-semibold text-sm leading-tight">{{ c.name }}</div>
              <div v-if="c.character" class="text-xs text-text-muted leading-tight">as {{ c.character }}</div>
            </div>
          </li>
        </ul>
      </section>

      <!-- QUICK FREE/STREAM ROW -->
      <section v-if="!loading && hasFreeOffers" class="space-y-4" aria-labelledby="providers-heading">
        <div class="flex items-baseline gap-3">
          <h2 id="providers-heading" class="text-xl font-semibold text-transparent bg-clip-text bg-grad-violet-magenta">
            Watch Free
          </h2>
          <span v-if="providersRegion" class="text-xs text-text-muted">Region: {{ providersRegion }}</span>
        </div>
        <div class="overlay-glass bg-background/50 rounded-2xl p-4">
          <ProviderChips :items="providersFree" />
        </div>
      </section>

      <!-- RECOMMENDATIONS -->
      <section v-if="!loading && recs.length" class="space-y-3">
        <h2 class="text-xl font-semibold text-transparent bg-clip-text bg-grad-cyan-violet">You may like</h2>
        <TransitionGroup name="list-slide" tag="ul" class="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
          <li
            v-for="m in recs" :key="m.id"
            class="overlay-glass rounded-2xl overflow-hidden bg-background/60 hover-scale cursor-pointer"
            @click="openDetails(m.id)"
          >
            <div class="w-full aspect-[2/3] bg-black/30">
              <template v-if="posterUrl(m.poster_path)">
                <img
                  :src="posterUrl(m.poster_path)!"
                  :srcset="posterSrcset(m.poster_path)"
                  width="342" height="513"
                  :alt="`${m.title} poster`"
                  class="w-full h-full object-cover"
                  loading="lazy" referrerpolicy="no-referrer"
                />
              </template>
              <div v-else class="w-full h-full grid place-items-center text-text-muted">No poster</div>
            </div>
            <div class="p-3">
              <div class="font-semibold leading-snug line-clamp-2">{{ m.title }}</div>
              <div v-if="m.year" class="text-sm text-text-muted">({{ m.year }})</div>
            </div>
          </li>
        </TransitionGroup>
      </section>
    </div>

    <!-- Providers Modal -->
    <ProvidersModal
      :open="modalOpen"
      :providers="providers"
      :initialTab="initialTab"
      :returnTo="watchNowBtn || null"
      @close="modalOpen = false"
    />
  </main>
</template>

<script setup lang="ts">
import { onMounted, ref, watch, computed } from "vue"
import { useRoute, useRouter } from "vue-router"
import ErrorPanel from "../components/ui/ErrorPanel.vue"
import ProviderChips from "../components/ui/ProviderChips.vue"
import ProvidersModal from "../components/ui/ProvidersModal.vue"
import {
  getMovieDetails, getRecommendations, getProviders,
  type DetailsResponse, type Cast, type Movie, type RecommendationsResponse, type ProviderItem, type ProvidersResponse
} from "../services/api"
import { posterUrl, posterSrcset, profileUrl, backdropUrl } from "../lib/img"

const route = useRoute()
const router = useRouter()

type ChipProvider = { id: number; name: string; logoPath: string | null; link?: string }

const movie = ref<Movie | null>(null)
const cast = ref<Cast[]>([])
const loading = ref(true)
const error = ref<any | null>(null)

const recs = ref<Movie[]>([])

const providersFree = ref<ChipProvider[]>([])
const providersRegion = ref<string | null>(null)

const runtime = ref<string | null>(null)
const rating = ref<string | null>(null)
const genres = ref<string[]>([])

const providers = ref<{ stream: ChipProvider[]; rent: ChipProvider[]; buy: ChipProvider[] }>({ stream: [], rent: [], buy: [] })
const modalOpen = ref(false)
const provFetched = ref(false)
const initialTab = ref<"stream" | "rent" | "buy">("stream")
const watchNowBtn = ref<HTMLButtonElement | null>(null)

const backdropStyle = computed(() => {
  const path = movie.value?.backdrop_path || movie.value?.poster_path
  const url = backdropUrl(path || undefined, "w1280")
  return url ? `url('${url}')` : "none"
})
const hasFreeOffers = computed(() => providersFree.value.length > 0)

async function loadAll(id: number) {
  loading.value = true
  error.value = null
  try {
    const details: DetailsResponse = await getMovieDetails(id)
    movie.value = details.movie
    cast.value = details.cast

    runtime.value = details.movie?.runtime ? `${details.movie.runtime} min` : null
    rating.value = typeof details.movie?.vote_average === "number" ? `★ ${details.movie.vote_average.toFixed(1)}` : null
    genres.value = Array.isArray(details.movie?.genres) ? (details.movie!.genres as any[]).map(g => g?.name).filter(Boolean) : []

    const r: RecommendationsResponse = await getRecommendations(id, 1)
    recs.value = r.results

    const raw: ProvidersResponse = await getProviders(id)
    const toChip = (x: ProviderItem): ChipProvider => ({ id: x.id, name: x.name, logoPath: x.logoPath ?? null, link: x.link })
    const stream = Array.isArray(raw?.stream) ? raw.stream.map(toChip) : []
    providersFree.value = stream
    providersRegion.value = raw?.region ?? null

    provFetched.value = false
    providers.value = { stream: [], rent: [], buy: [] }
  } catch (e: any) {
    error.value = { message: e?.message || "Failed to load movie" }
  } finally {
    loading.value = false
  }
}

async function openProviders() {
  if (!movie.value) return
  if (!provFetched.value) {
    const raw: ProvidersResponse = await getProviders(movie.value.id)
    const toChip = (x: ProviderItem): ChipProvider => ({ id: x.id, name: x.name, logoPath: x.logoPath ?? null, link: x.link })
    providers.value = {
      stream: (raw.stream || []).map(toChip),
      rent:   (raw.rent   || []).map(toChip),
      buy:    (raw.buy    || []).map(toChip),
    }
    initialTab.value =
      (providers.value.stream?.length ?? 0) > 0 ? "stream" :
      (providers.value.rent?.length   ?? 0) > 0 ? "rent"   : "buy"
    provFetched.value = true
  }
  modalOpen.value = true
}

function openDetails(id: number) { router.push({ name: "details", params: { id } }) }

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
.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
</style>
