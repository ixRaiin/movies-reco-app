<script setup lang="ts">
import PosterCard from '@/components/movies/PosterCard.vue'
type Item = { id:number; title:string; poster_path:string | null; overview?:string | null }
defineProps<{ title: string; items: Item[] }>()
</script>

<template>
  <section class="mt-10 surface-aurora rounded-2xl py-6">
    <div class="mb-3 flex items-center justify-between px-1 sm:px-0">
      <h3 class="heading-brand text-2xl sm:text-3xl font-extrabold">
        {{ title }}
      </h3>
      <span class="text-sm text-white/70">{{ items.length }} items</span>
    </div>

    <div class="relative overflow-x-auto snap-x snap-mandatory flex gap-6 pb-2 scrollbar-hide">
      <RouterLink
        v-for="(m, idx) in items"
        :key="m.id"
        :to="{ name: 'details', params: { id: m.id } }"
        class="outline-none min-w-[170px] sm:min-w-[190px] md:min-w-[210px] snap-start relative"
      >
        <!-- faint index badge at left edge for subtle continuity with hero -->
        <div class="absolute -left-1 -top-6 select-none pointer-events-none">
          <div class="font-black text-[4.5rem] sm:text-[5.5rem] leading-none text-transparent bg-clip-text"
               style="background: var(--brand-grad); opacity:.18; filter: blur(1px)">
            {{ (idx + 1) }}
          </div>
        </div>

        <PosterCard :title="m.title" :posterPath="m.poster_path">
          <template #sub>
            <p class="mt-1 text-[12px] text-white/65 line-clamp-3">{{ m.overview || ' ' }}</p>
          </template>
        </PosterCard>
      </RouterLink>
    </div>
  </section>
</template>

<style scoped>
.scrollbar-hide::-webkit-scrollbar{display:none}
.scrollbar-hide{scrollbar-width:none;-ms-overflow-style:none}
</style>
