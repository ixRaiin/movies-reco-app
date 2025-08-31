// src/composables/useRatings.ts
import { ref } from 'vue'

export type UserRating = {
  id: number
  rating: number        // 1..5
  title?: string
  poster_path?: string | null
  genre_ids?: number[]
  release_date?: string | null
  updatedAt: number
}

const LS_KEY = 'cine.user.ratings.v1'
const ratingsMap = ref<Record<number, UserRating>>({})

function load() {
  try {
    const raw = localStorage.getItem(LS_KEY)
    ratingsMap.value = raw ? JSON.parse(raw) : {}
  } catch { ratingsMap.value = {} }
}
function save() {
  localStorage.setItem(LS_KEY, JSON.stringify(ratingsMap.value))
}

export function useRatings() {
  if (!Object.keys(ratingsMap.value).length) load()

  function rate(movie: {
    id: number
    title?: string
    poster_path?: string | null
    genre_ids?: number[]
    release_date?: string | null
  }, value: number) {
    if (!movie?.id) return
    if (value <= 0) {
      delete ratingsMap.value[movie.id]
    } else {
      ratingsMap.value[movie.id] = {
        id: movie.id,
        rating: Math.max(1, Math.min(5, value)),
        title: movie.title,
        poster_path: movie.poster_path ?? null,
        genre_ids: movie.genre_ids ?? [],
        release_date: movie.release_date ?? null,
        updatedAt: Date.now(),
      }
    }
    save()
  }

  function clearAll() {
    ratingsMap.value = {}
    save()
  }

  function get(id: number): number {
    return ratingsMap.value[id]?.rating ?? 0
  }

  function list(): UserRating[] {
    return Object.values(ratingsMap.value).sort((a, b) => b.updatedAt - a.updatedAt)
  }

  return { rate, clearAll, get, list, ratingsMap }
}
