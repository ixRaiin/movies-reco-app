<template>
  <div class="min-h-screen bg-background text-text-primary">
    <!-- Hero / Top 10 -->
    <section class="relative py-10 px-6 bg-radial-aurora">
      <div class="flex items-baseline justify-between">
        <h1 class="text-5xl font-extrabold mb-6 text-transparent bg-clip-text bg-grad-cyan-violet">
          Top 10 Today
        </h1>
        <div class="flex gap-2">
          <button
            class="px-3 py-1 rounded border border-transparent hover:border-neon-cyan hover:shadow-[var(--shadow-neon-cyan)] transition"
            :class="{'text-neon-cyan border-neon-cyan': window === 'day'}"
            @click="switchWindow('day')"
          >
            Day
          </button>
          <button
            class="px-3 py-1 rounded border border-transparent hover:border-neon-cyan hover:shadow-[var(--shadow-neon-cyan)] transition"
            :class="{'text-neon-cyan border-neon-cyan': window === 'week'}"
            @click="switchWindow('week')"
          >
            Week
          </button>
        </div>
      </div>

      <!-- Carousel -->
      <div class="relative">
        <div class="flex gap-6 overflow-x-auto scrollbar-hide snap-x snap-mandatory">
          <div
            v-for="(movie, index) in top10"
            :key="movie.id"
            class="relative snap-start flex-shrink-0 w-48 md:w-56 lg:w-64 cursor-pointer transition-transform duration-300 hover:scale-105"
            @click="$router.push({ name: 'details', params: { id: movie.id } })"
          >
            <!-- Rank Number -->
            <span class="absolute -left-6 top-4 text-7xl font-black text-neon-cyan/20 select-none">
              {{ index + 1 }}
            </span>

            <!-- Poster Card -->
            <div class="overlay-glass relative overflow-hidden">
              <img
                v-if="posterUrl(movie.poster_path)"
                :src="posterUrl(movie.poster_path)!"
                :alt="movie.title"
                class="w-full h-72 object-cover rounded-[1rem]"
                loading="lazy"
                referrerpolicy="no-referrer"
              />
              <div v-else class="w-full h-72 flex items-center justify-center text-text-muted">No poster</div>
            </div>
            <h3 class="mt-3 text-center font-semibold text-lg line-clamp-2">{{ movie.title }}</h3>
          </div>
        </div>
      </div>
    </section>

    <!-- Trending/Popular -->
    <section class="py-10 px-6 space-y-6">
      <div class="flex items-center justify-between">
        <h2 class="text-3xl font-bold bg-clip-text text-transparent bg-grad-violet-magenta">
          Trending Today
        </h2>
        <button
          class="px-3 py-1 rounded border hover:border-neon-violet hover:shadow-[var(--shadow-neon-violet)] transition"
          @click="refreshPopular"
        >
          Refresh Popular
        </button>
      </div>

      <div class="flex gap-6 overflow-x-auto scrollbar-hide snap-x snap-mandatory">
        <div
          v-for="movie in popular"
          :key="movie.id"
          class="overlay-glass snap-start flex-shrink-0 w-40 md:w-48 cursor-pointer transition-transform duration-300 hover:scale-105"
          @click="$router.push({ name: 'details', params: { id: movie.id } })"
        >
          <img
            v-if="posterUrl(movie.poster_path)"
            :src="posterUrl(movie.poster_path)!"
            :alt="movie.title"
            class="w-full h-60 object-cover rounded-[1rem]"
            loading="lazy"
            referrerpolicy="no-referrer"
          />
          <div v-else class="w-full h-60 flex items-center justify-center text-text-muted">No poster</div>
          <div class="p-2 text-center">
            <p class="font-medium text-sm line-clamp-2">{{ movie.title }}</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue"
import { posterUrl } from "../lib/img"
import { getTrending, getPopular, type Movie } from "../services/api"

const window = ref<"day" | "week">("day")
const top10 = ref<Movie[]>([])
const popular = ref<Movie[]>([])

async function loadTrending() {
  const data = await getTrending(window.value)
  top10.value = data.results
}
async function refreshPopular() {
  const data = await getPopular()
  popular.value = data.results
}
function switchWindow(w: "day" | "week") {
  window.value = w
  loadTrending()
}

onMounted(async () => {
  await Promise.all([loadTrending(), refreshPopular()])
})
</script>
