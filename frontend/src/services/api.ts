const API_BASE = '/api'

export type Health = { status: string }
export type Movie = {
  id: number
  title: string
  year?: number | null
  overview?: string | null
  poster_path?: string | null
}
export type SearchResponse = {
  page: number
  total_pages: number
  total_results: number
  results: Movie[]
}

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path.startsWith('/') ? path : `/${path}`}`
  const res = await fetch(url, { ...init, headers: { Accept: 'application/json', ...(init?.headers || {}) } })
  if (!res.ok) {
    const maybe = await res.json().catch(() => ({}))
    throw new Error((maybe && (maybe.message || maybe.code)) || `HTTP ${res.status}`)
  }
  return res.json()
}

export const getHealth = async () => {
  const res = await fetch('/api/health')
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export const searchMovies = (q: string, page = 1) =>
  http<SearchResponse>(`/search?q=${encodeURIComponent(q)}&page=${page}`)

export type Cast = {
  id: number
  name: string
  character?: string | null
  profile_path?: string | null
}

export type DetailsResponse = {
  movie: Movie
  cast: Cast[]
}

export const getMovieDetails = (id: number) =>
  http<DetailsResponse>(`/details/${id}`)

export type RecommendationsResponse = {
  source: "recommendations" | "similar"
  page: number
  total_pages: number
  total_results: number
  results: Movie[]
}

export const getRecommendations = (id: number, page = 1) =>
  http<RecommendationsResponse>(`/recommend/${id}?page=${page}`)

export type Provider = {
  provider_id: number
  provider_name: string
  logo_path: string | null
}

export type ProvidersResponse = {
  region: string
  link?: string
  flatrate: Provider[]
  rent: Provider[]
  buy: Provider[]
  ads: Provider[]
  free: Provider[]
}

export const getProviders = (id: number, region?: string) =>
  http<ProvidersResponse>(`/providers/${id}${region ? `?region=${encodeURIComponent(region)}` : ""}`)

export type MoodResponse = {
  mood: string
  genres: number[]
  page: number
  total_pages: number
  total_results: number
  results: Movie[]
}

export const getMoodRecs = (mood: string, page = 1, region?: string) =>
  http<MoodResponse>(`/recommend/mood?mood=${encodeURIComponent(mood)}&page=${page}${region ? `&region=${encodeURIComponent(region)}` : ""}`)

export const getTrending = (window: "day" | "week" = "day") =>
  http<{ window: "day" | "week"; results: Movie[]; total: number }>(`/trending?window=${window}`)

export const getPopular = () =>
  http<{ results: Movie[]; total: number }>(`/popular`)

