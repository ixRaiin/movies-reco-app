<script setup lang="ts">
defineProps<{ as?: string }>()
</script>

<template>
  <button
    class="px-4 py-2 rounded-2xl text-sm font-semibold
           text-white bg-[color:var(--neon-cyan)]/90
           hover:shadow-neon transition focus-neon disabled:opacity-60"
  >
    <slot />
  </button>
</template>
