<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { onMounted, onBeforeUnmount, ref } from 'vue'

export interface Item {
  id: number
  title: string
  poster_path: string | null
  overview?: string | null
}

const props = defineProps<{ title: string; items: Item[] }>()

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
  <section class="relative py-6">
    <div class="mb-3 flex items-center justify-between">
    <h3 class="heading-row halo text-2xl sm:text-3xl font-extrabold">{{ title }}</h3>
      <span class="text-xs sm:text-sm text-white/70">{{ items.length }} items</span>
    </div>

    <div class="relative">
      <!-- Edge hot-zones -->
      <div class="carousel-edge carousel-edge--left" aria-hidden="true">
        <button class="carousel-chev-lg" aria-label="Scroll left"  @click="scrollBy(-560)">‹</button>
      </div>
      <div class="carousel-edge carousel-edge--right" aria-hidden="true">
        <button class="carousel-chev-lg" aria-label="Scroll right" @click="scrollBy(560)">›</button>
      </div>

      <!-- Track -->
      <div
        ref="scroller"
        class="flex gap-4 sm:gap-5 overflow-x-auto snap-x snap-mandatory py-1 scrollbar-hide scroll-smooth px-1"
      >
        <RouterLink
          v-for="m in props.items"
          :key="m.id"
          :to="{ name: 'details', params: { id: m.id } }"
          class="relative snap-start flex-shrink-0
                 w-[156px] sm:w-[188px] md:w-[208px]
                 cursor-pointer group outline-none"
          :aria-label="`Open details for ${m.title}`"
        >
          <!-- Poster tile (no border slab; reddish-neon glow lives behind) -->
          <div class="tile row-tile">
            <img
              v-if="m.poster_path"
              :src="`https://image.tmdb.org/t/p/w342${m.poster_path}`"
              :alt="m.title"
              class="hero-img"
              loading="lazy"
              referrerpolicy="no-referrer"
            />
            <div class="img-overlay opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          </div>

          <h4 class="mt-2 text-center font-semibold text-[12px] sm:text-sm line-clamp-2">
            {{ m.title }}
          </h4>
        </RouterLink>
      </div>
    </div>
  </section>
</template>
