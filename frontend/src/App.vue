<template>
  <div class="min-h-screen bg-background text-text-primary">
    <AppNav />
    <RouterView />
  </div>
</template>


<script setup lang="ts">
import AppNav from './components/AppNav.vue'
</script>
