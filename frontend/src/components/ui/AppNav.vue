<!-- src/components/ui/AppNav.vue -->
<template>
  <!-- Sticky neon-glass navbar -->
  <header
    :class="[
      'sticky top-0 z-40 w-full transition-shadow duration-300',
      scrolled ? 'shadow-[var(--shadow-glass)]' : ''
    ]"
    role="banner"
  >
    <!-- Glass container that blends with dark background -->
    <div
      class="mx-auto max-w-7xl px-4 sm:px-6 rounded-b-2xl
             bg-background/80 backdrop-blur-md overlay-glass"
    >
      <div class="flex h-16 items-center justify-between">
        <!-- Brand -->
        <RouterLink to="/" class="flex items-center gap-2 group" aria-label="Home">
          <span
            class="text-2xl font-extrabold text-transparent bg-clip-text bg-grad-cyan-violet
                   tracking-tight group-hover:shadow-[var(--shadow-neon-cyan)] transition"
          >
            CineMood
          </span>
        </RouterLink>

        <!-- Primary nav (desktop) -->
        <nav class="hidden md:flex items-center gap-6" aria-label="Primary">
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="relative px-1.5 py-1 text-sm font-medium transition-colors"
            v-slot="{ isActive, isExactActive }"
          >
            <span
              :class="[
                (isActive || isExactActive)
                  ? 'text-neon-cyan'
                  : 'text-text-secondary hover:text-neon-violet'
              ]"
            >
              {{ item.label }}
            </span>
            <!-- glowing cyan underline for active link -->
            <span
              :class="[
                'absolute left-0 right-0 -bottom-0.5 h-0.5 rounded-full transition-all',
                (isActive || isExactActive)
                  ? 'bg-[var(--color-neon-cyan)] shadow-[var(--shadow-neon-cyan)] opacity-100'
                  : 'opacity-0'
              ]"
              aria-hidden="true"
            />
          </RouterLink>
        </nav>

        <!-- Right actions -->
        <div class="hidden md:flex items-center gap-3">
          <RouterLink
            to="/search"
            class="px-3 py-1.5 rounded-lg border border-transparent
                   hover:border-neon-cyan hover:shadow-[var(--shadow-neon-cyan)]
                   text-sm transition"
          >
            Quick Search
          </RouterLink>
        </div>

        <!-- Mobile menu button -->
        <button
          type="button"
          class="md:hidden inline-flex items-center justify-center p-2 rounded-md
                 border border-transparent hover:border-neon-cyan
                 hover:shadow-[var(--shadow-neon-cyan)] transition"
          @click="open = !open"
          :aria-expanded="open ? 'true' : 'false'"
          aria-controls="mobile-menu"
          aria-label="Toggle menu"
        >
          <span class="sr-only">Menu</span>
          <div class="space-y-1.5">
            <span class="block h-0.5 w-6 bg-text-primary"></span>
            <span class="block h-0.5 w-6 bg-text-primary"></span>
            <span class="block h-0.5 w-6 bg-text-primary"></span>
          </div>
        </button>
      </div>

      <!-- Mobile sheet -->
      <Transition name="fade">
        <nav
          v-if="open"
          id="mobile-menu"
          class="md:hidden pb-3 flex flex-col gap-1"
          aria-label="Mobile"
        >
          <RouterLink
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="relative px-3 py-2 text-sm font-medium transition-colors rounded-lg
                   hover:bg-white/5"
            v-slot="{ isActive, isExactActive }"
            @click="open = false"
          >
            <span
              :class="[
                (isActive || isExactActive)
                  ? 'text-neon-cyan'
                  : 'text-text-secondary hover:text-neon-violet'
              ]"
            >
              {{ item.label }}
            </span>
          </RouterLink>
        </nav>
      </Transition>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { RouterLink } from 'vue-router' // 👈 add this for TS + template inference

const open = ref(false)
const scrolled = ref(false)

type NavItem = { to: string; label: string }
const navItems: NavItem[] = [
  { to: '/', label: 'Home' },
  { to: '/search', label: 'Search' },
  { to: '/mood', label: 'Mood' },
]

function onScroll() {
  scrolled.value = window.scrollY > 6
}
onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onBeforeUnmount(() => window.removeEventListener('scroll', onScroll))
</script>

<style>
/* subtle drop animation for mobile menu */
.fade-enter-active, .fade-leave-active { transition: opacity .15s ease, transform .15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-4px); }
</style>
