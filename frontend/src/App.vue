<template>
  <div id="app" class="min-h-screen bg-[var(--color-background)] text-text-primary">
    <AppNav />
    <Transition name="route-fade" mode="out-in" appear>
      <RouterView />
    </Transition>
  </div>
</template>

<script setup lang="ts">
import AppNav from "./components/ui/AppNav.vue"
</script>
