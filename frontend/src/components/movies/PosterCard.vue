<script setup lang="ts">
type Props = {
  title: string
  posterPath: string | null
  alt?: string
}
defineProps<Props>()
</script>

<template>
  <div class="relative snap-start cursor-pointer transition-transform duration-300 hover:scale-105 group">
    <div class="relative overflow-hidden rounded-2xl bg-white/5 backdrop-blur-md border border-white/10">
      <img
        v-if="posterPath"
        :src="`https://image.tmdb.org/t/p/w342${posterPath}`"
        :alt="alt || title"
        class="w-full h-72 object-cover rounded-2xl"
        loading="lazy"
        referrerpolicy="no-referrer"
      />
      <div class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition"></div>
    </div>
    <div class="mt-3 px-1">
      <h3 class="text-center font-semibold text-sm line-clamp-2">{{ title }}</h3>
      <slot name="sub" />
    </div>
  </div>
</template>
