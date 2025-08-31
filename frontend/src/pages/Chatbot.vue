<script setup lang="ts">
import { ref, nextTick, computed } from 'vue'
import { RouterLink } from 'vue-router'
import { analyzeMood, searchMovies } from '@/services/api'
import GlassCard from '@/components/ui/GlassCard.vue'
import GlowButton from '@/components/ui/GlowButton.vue'
import PosterCard from '@/components/movies/PosterCard.vue'

type Msg = { role: 'user' | 'assistant'; content: string }
type Movie = { id: number; title: string; poster_path: string | null; overview?: string | null }

const messages = ref<Msg[]>([
  { role: 'assistant', content: "Hi! Tell me how you're feeling and I’ll pull a few great movies for that vibe." }
])
const userText = ref('')
const movies = ref<Movie[]>([])
const loading = ref(false)
const loadingCards = ref(false)
const hasSearched = ref(false)
const error = ref<string | null>(null)
const logEl = ref<HTMLElement | null>(null)

const phase = ref<'idle'|'analyze'|'done'>('idle')
const phaseText = computed(() => ({
  idle:   '',
  analyze:'Analyzing your mood and fetching matches…',
  done:   'Done.'
}[phase.value]))

// Only render items that have both id and poster
const visibleMovies = computed(() =>
  movies.value.filter(m => m?.id && m?.poster_path).slice(0, 10)
)

/* ---------- helpers ---------- */

// Try to parse movie titles from an LLM content blob
function extractTitlesFromContent(content: string): string[] {
  const titles: string[] = []
  const lines = content.split('\n').map(l => l.trim()).filter(Boolean)

  for (const raw of lines) {
    // strip bullets / numbering / asterisks
    let s = raw.replace(/^[\s*•\-–\d\.\)\(]+/, '').replace(/\*\*/g, '').trim()
    if (!s) continue

    // Prefer split at " - " or " – " or ":" (title – desc)
    let title =
      s.split(' – ')[0]
       .split(' - ')[0]
       .split(':')[0]
       .trim()

    // Remove trailing year "(1999)" if present
    title = title.replace(/\s*\(\d{4}\)$/, '').trim()

    // Basic sanity
    if (title && title.length > 1 && !/^\d{4}$/.test(title)) {
      titles.push(title)
    }
  }

  // de-dupe, keep order, cap at 10
  const seen = new Set<string>()
  return titles.filter(t => !seen.has(t) && seen.add(t)).slice(0, 10)
}

// Enrich a list of titles via your TMDB proxy, keep first result w/ poster
async function enrichTitles(titles: string[]): Promise<Movie[]> {
  const out: Movie[] = []
  await Promise.all(
    titles.map(async (t) => {
      try {
        const res = await searchMovies(t, 1) // uses your existing service
        const first = res?.results?.find((r: any) => r?.poster_path && r?.id)
        if (first) {
          out.push({
            id: first.id,
            title: first.title,
            poster_path: first.poster_path ?? null,
            overview: first.overview ?? null
          })
        }
      } catch {
        /* ignore individual failures */
      }
    })
  )
  // de-dupe by id
  const seen = new Set<number>()
  return out.filter(m => !seen.has(m.id) && seen.add(m.id))
}

/* ---------- main submit ---------- */

async function handleSearch() {
  const text = userText.value.trim()
  if (!text || loading.value) return

  error.value = null
  messages.value.push({ role: 'user', content: text })
  userText.value = ''
  await nextTick(() => logEl.value?.scrollTo({ top: logEl.value.scrollHeight, behavior: 'smooth' }))

  loading.value = true
  loadingCards.value = true
  hasSearched.value = true
  phase.value = 'analyze'

  try {
    // Your backend may return either:
    //  A) { movies: Movie[], reply?: string }
    //  B) full LLM shape with choices[0].message.content
    const res: any = await analyzeMood(text)

    let backendMovies: Movie[] = Array.isArray(res?.movies) ? res.movies : []
    let llmContent: string | undefined =
      res?.reply ??
      res?.choices?.[0]?.message?.content

    // If the backend already did TMDB filtering, use that
    if (backendMovies.length > 0) {
      const seen = new Set<number>()
      movies.value = backendMovies
        .filter(m => m && m.id && m.poster_path && !seen.has(m.id) && seen.add(m.id))
        .slice(0, 10)
    } else if (typeof llmContent === 'string' && llmContent.trim()) {
      // Parse titles from content and enrich via TMDB
      const titles = extractTitlesFromContent(llmContent)
      movies.value = await enrichTitles(titles)
    } else {
      movies.value = []
    }

    // Keep transcript surface-level (not listing the movies)
    const assistantLine =
      (typeof res?.reply === 'string' && res.reply.trim()) ||
      (llmContent ? 'Got it — here are a few that fit. Tap a poster for details.' :
        "I'm not sure I can match that yet — try adding hints like era, pace, or 'not scary'.")
    messages.value.push({ role: 'assistant', content: assistantLine })
    await nextTick(() => logEl.value?.scrollTo({ top: logEl.value.scrollHeight, behavior: 'smooth' }))

    phase.value = 'done'
  } catch (e: any) {
    error.value = e?.message || 'Something went wrong.'
    messages.value.push({
      role: 'assistant',
      content: "Hmm, I hit a snag. Try rephrasing your mood (add hints like era, pace, or 'not scary')."
    })
  } finally {
    loading.value = false
    loadingCards.value = false
  }
}
</script>

<template>
  <section class="mx-auto max-w-7xl px-4 sm:px-6 py-6 bg-aurora min-h-[100dvh]">
    <!-- Header -->
    <div class="mb-4 flex items-center justify-between">
      <h1 class="text-2xl sm:text-3xl font-extrabold text-grad-cyan-violet">
        Experimental · Chatbot
      </h1>
      <span class="text-text-secondary text-sm">Movies by mood</span>
    </div>

    <!-- Chat glass -->
    <GlassCard class="p-4 md:p-6">
      <!-- Transcript -->
      <div id="chatlog" class="space-y-3 max-h-[42vh] overflow-y-auto pr-1" ref="logEl">
        <div
          v-for="(m, i) in messages"
          :key="i"
          :class="[
            'rounded-xl px-3 py-2 max-w-[80%] md:max-w-[70%]',
            m.role === 'assistant'
              ? 'bg-white/5 text-text-primary'
              : 'bg-[color:var(--neon-cyan)]/10 text-text-primary ml-auto border border-[var(--neon-cyan)]/30'
          ]"
        >
          <p class="whitespace-pre-wrap text-sm leading-relaxed">{{ m.content }}</p>
        </div>

        <!-- Status strip -->
        <div v-if="loading || phase !== 'idle'" class="text-xs text-text-secondary pl-1">
          <span v-if="phase === 'analyze'">🔎 {{ phaseText }}</span>
          <span v-else-if="phase === 'done'">✅ {{ phaseText }}</span>
        </div>
      </div>

      <!-- Input -->
      <form class="mt-4 flex items-center gap-2" @submit.prevent="handleSearch">
        <label for="mood-input" class="sr-only">Describe your mood</label>
        <div
          class="flex items-center gap-2 overlay-glass-strong rounded-full px-3 py-2
                 focus-within:ring-2 focus-within:ring-[color:var(--neon-cyan)] w-full"
        >
          <input
            id="mood-input"
            v-model="userText"
            type="text"
            autocomplete="off"
            :disabled="loading"
            placeholder="Describe your mood… e.g. 'overwhelmed but hopeful'"
            class="bg-transparent flex-1 outline-none text-text-primary placeholder-text-secondary"
          />
          <GlowButton :disabled="loading || !userText.trim()" aria-label="Send">
            {{ loading ? 'Sending…' : 'Send' }}
          </GlowButton>
        </div>
      </form>
    </GlassCard>

    <!-- Results header -->
    <div class="mt-8 mb-3 flex items-center justify-between">
      <h2 class="text-lg font-semibold text-text-primary">Top matches</h2>
      <span class="text-text-secondary text-sm">{{ visibleMovies.length }} results</span>
    </div>

    <!-- Loading -->
    <div v-if="loadingCards" class="grid gap-6 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
      <div v-for="n in 10" :key="n" class="overlay-glass rounded-2xl h-64 animate-pulse bg-white/5"></div>
    </div>

    <!-- Empty -->
    <GlassCard v-else-if="!visibleMovies.length && hasSearched" class="p-6 text-center">
      <p class="text-text-secondary">
        No matches yet. Try describing your mood a bit more (e.g., “cozy romantic, not scary, under 2 hours”).
      </p>
    </GlassCard>

    <!-- Posters -->
    <div v-else class="grid gap-6 grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
      <RouterLink
        v-for="m in visibleMovies"
        :key="m.id"
        :to="{ name: 'details', params: { id: m.id } }"
        class="outline-none"
        :aria-label="`Open details for ${m.title}`"
      >
        <PosterCard :title="m.title" :posterPath="m.poster_path">
          <template #sub>
            <p class="mt-1 text-[12px] text-text-secondary line-clamp-3">{{ m.overview || 'No description available.' }}</p>
          </template>
        </PosterCard>
      </RouterLink>
    </div>

    <!-- Error -->
    <p v-if="error" role="alert" class="mt-4 text-[13px] text-red-300">{{ error }}</p>
  </section>
</template>
