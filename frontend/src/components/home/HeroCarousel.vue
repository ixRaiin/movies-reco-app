<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { onMounted, onBeforeUnmount, ref } from 'vue'

export interface Item { id:number; title:string; poster_path:string | null }
defineProps<{ items: Item[] }>()

const scroller = ref<HTMLElement | null>(null)

function scrollBy(px: number) {
  scroller.value?.scrollBy({ left: px, behavior: 'smooth' })
}

function onWheel(e: WheelEvent) {
  const el = scroller.value
  if (!el) return
  const dx = Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY
  if (dx !== 0) { e.preventDefault(); el.scrollLeft += dx }
}

onMounted(() => scroller.value?.addEventListener('wheel', onWheel, { passive: false }))
onBeforeUnmount(() => scroller.value?.removeEventListener('wheel', onWheel))
</script>

<template>
  <section class="relative pt-2 pb-1">
    <div class="mb-3 flex items-center justify-between">
      <!-- Bigger, colorful heading -->
      <h2 class="heading heading-top10 halo text-4xl sm:text-5xl font-extrabold mb-3">
        Top 10 Today
      </h2>
    </div>

    <div class="relative">
      <!-- Edge hot-zones (big click targets) -->
      <div class="carousel-edge carousel-edge--left" aria-hidden="true">
        <button class="carousel-chev-lg" aria-label="Scroll left"  @click="scrollBy(-780)">‹</button>
      </div>
      <div class="carousel-edge carousel-edge--right" aria-hidden="true">
        <button class="carousel-chev-lg" aria-label="Scroll right" @click="scrollBy(780)">›</button>
      </div>

      <!-- Track -->
      <div
        ref="scroller"
        class="flex gap-6 overflow-x-auto snap-x snap-mandatory py-1 scrollbar-hide scroll-smooth px-1"
      >
        <RouterLink
          v-for="(m, i) in items.slice(0, 10)"
          :key="m.id"
          :to="{ name: 'details', params: { id: m.id } }"
          class="relative snap-start flex-shrink-0
                 w-[232px] sm:w-[292px] md:w-[352px] lg:w-[392px]
                 cursor-pointer group outline-none"
          :aria-label="`Open details for ${m.title}`"
        >
          <!-- Poster tile (no visible border/panel) -->
          <div class="tile hero-tile">
            <!-- Rank sits behind the poster, half-visible, lowered for readability -->
            <div class="rank-hero z-[1]">
              <span class="rank-hero__back">{{ i + 1 }}</span>
              <span class="rank-hero__front">{{ i + 1 }}</span>
            </div>

            <!-- Cyan glow lives behind the image (via ::before in CSS) -->
            <img
              v-if="m.poster_path"
              :src="`https://image.tmdb.org/t/p/w780${m.poster_path}`"
              :alt="m.title"
              class="hero-img"
              loading="lazy"
              referrerpolicy="no-referrer"
            />

            <!-- Subtle bottom gradient only on hover (no seams) -->
            <div class="img-overlay opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          </div>

          <h3 class="mt-2 text-center font-semibold text-sm sm:text-base line-clamp-2">
            {{ m.title }}
          </h3>
        </RouterLink>
      </div>
    </div>
  </section>
</template>
