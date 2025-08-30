<template>
  <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
    <SkeletonCard v-for="n in count" :key="n" />
  </div>
</template>
<script setup lang="ts">
defineProps<{ count?: number }>()
</script>
