<template>
  <main class="min-h-screen bg-background text-text-primary">
    <!-- Hero search bar section -->
    <section class="relative py-12 px-6 bg-radial-aurora text-center">
      <h1 class="text-4xl md:text-5xl font-extrabold mb-4 text-transparent bg-clip-text bg-grad-cyan-violet">
        Discover Your Next Favorite
      </h1>
      <p class="text-text-muted mb-8">Search by movie, series, or genre</p>

      <div class="flex justify-center gap-3">
        <!-- Glassmorphic search input -->
        <div class="overlay-glass flex items-center gap-2 px-4 py-2 w-full max-w-xl rounded-full">
          <input
            v-model="query"
            type="text"
            placeholder="Search for movies..."
            class="bg-transparent flex-1 outline-none text-text-primary placeholder-text-muted
                   focus:ring-2 focus:ring-neon-cyan rounded-full px-2 py-1"
            @keyup.enter="performSearch"
            aria-label="Search movies"
          />
          <button
            @click="performSearch"
            class="p-2 rounded-full border border-neon-cyan hover:shadow-[var(--shadow-neon-cyan)] transition"
            aria-label="Search"
          >
            🔍
          </button>
        </div>

        <!-- Filter dropdown (placeholder for genres/series) -->
        <select
          v-model="filter"
          class="overlay-glass px-4 py-2 rounded-full text-sm outline-none
                 focus:ring-2 focus:ring-neon-violet"
          aria-label="Search filter"
        >
          <option>Movies</option>
          <option>Series</option>
          <option>Genres</option>
        </select>
      </div>
    </section>

    <!-- Conditional states -->
    <section v-if="!query" class="py-12 px-6 space-y-6">
      <h2 class="text-2xl font-bold bg-clip-text text-transparent bg-grad-violet-magenta mb-6">
        Top 10 This Month
      </h2>

      <div class="flex gap-6 overflow-x-auto scrollbar-hide snap-x snap-mandatory">
        <div
          v-for="(movie, index) in top10"
          :key="movie.id"
          class="relative overlay-glass snap-start flex-shrink-0 w-40 md:w-48 cursor-pointer transition-transform duration-300 hover:scale-105"
          @click="$router.push({ name: 'details', params: { id: movie.id } })"
        >
          <!-- Rank overlay -->
          <span
            class="absolute -left-3 top-3 text-6xl font-black text-neon-cyan/20 select-none"
          >
            {{ index + 1 }}
          </span>

          <img
            v-if="posterUrl(movie.poster_path)"
            :src="posterUrl(movie.poster_path)!"
            :alt="movie.title"
            class="w-full h-60 object-cover rounded-[1rem]"
            loading="lazy"
          />
          <div v-else class="w-full h-60 flex items-center justify-center text-text-muted">
            No poster
          </div>
          <p class="mt-2 text-center text-sm font-medium">{{ movie.title }}</p>
        </div>
      </div>
    </section>

    <!-- Search results -->
    <section v-else class="py-12 px-6 space-y-6">
      <div>
        <h2 class="text-2xl font-bold">
          Search Results for
          <span class="text-transparent bg-clip-text bg-grad-cyan-violet">“{{ query }}”</span>
        </h2>
        <p class="text-text-muted text-sm">{{ results.length }} results found</p>
      </div>

      <div
        v-if="results.length"
        class="grid gap-6 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5"
      >
        <div
          v-for="movie in results"
          :key="movie.id"
          class="relative overlay-glass cursor-pointer group transition-transform duration-300 hover:scale-105"
          @click="$router.push({ name: 'details', params: { id: movie.id } })"
        >
          <img
            v-if="posterUrl(movie.poster_path)"
            :src="posterUrl(movie.poster_path)!"
            :alt="movie.title"
            class="w-full h-60 object-cover rounded-[1rem] group-hover:shadow-[var(--shadow-neon-violet)]"
            loading="lazy"
          />
          <div
            class="absolute bottom-0 left-0 right-0 p-2 text-sm text-center
                   bg-background/60 backdrop-blur-xs opacity-0 group-hover:opacity-100
                   transition"
          >
            <span class="text-transparent bg-clip-text bg-grad-violet-magenta font-semibold">
              {{ movie.title }}
            </span>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div
        v-else
        class="overlay-glass p-8 text-center rounded-xl max-w-md mx-auto"
      >
        <p class="text-4xl mb-3">🔎</p>
        <p class="text-text-muted">No matches found. Try a different title.</p>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { getTrending, searchMovies, type Movie } from "../services/api"
import { posterUrl } from "../lib/img"

const query = ref("")
const filter = ref("Movies")
const top10 = ref<Movie[]>([])
const results = ref<Movie[]>([])

async function performSearch() {
  if (!query.value.trim()) {
    results.value = []
    return
  }
  const res = await searchMovies(query.value, 1)
  results.value = res.results
}

onMounted(async () => {
  const trending = await getTrending("week")
  top10.value = trending.results.slice(0, 10)
})
</script>
