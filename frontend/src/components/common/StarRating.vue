<template>
  <div class="inline-flex items-center gap-1" :aria-label="ariaLabel">
    <button
      v-for="n in 5" :key="n" type="button"
      class="focus:outline-none"
      :aria-pressed="n <= modelValue"
      @click="$emit('update:modelValue', n)"
      @keydown.enter.prevent="$emit('update:modelValue', n)"
    >
      <svg :width="20" :height="20" viewBox="0 0 24 24"
        :class="n <= modelValue ? 'fill-[var(--neon-pink)] drop-shadow-[0_0_10px_rgba(255,106,213,.6)]' : 'fill-white/25'"
        role="img" focusable="false" aria-hidden="true">
        <path d="M12 .587l3.668 7.431 8.2 1.192-5.934 5.787 1.402 8.168L12 18.896l-7.336 3.869 1.402-8.168L.132 9.21l8.2-1.192z"/>
      </svg>
    </button>
    <button v-if="modelValue>0" class="ml-1 text-xs text-white/60 hover:text-white/90"
      @click="$emit('update:modelValue', 0)">Clear</button>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: number
  ariaLabel?: string
}>()
defineEmits<{(e:'update:modelValue', v:number): void}>()
</script>
