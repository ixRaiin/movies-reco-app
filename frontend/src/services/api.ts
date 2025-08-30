// src/services/api.ts
const API_BASE = "/api"

// ---------- Shared Types ----------
export type Health = { status: string }

export type Movie = {
  id: number
  title: string
  year?: number | null
  overview?: string | null
  poster_path?: string | null
}

export type Cast = {
  id: number
  name: string
  character?: string | null
  profile_path?: string | null
}

export type ApiErrorEnvelope = {
  code: string
  message: string
  hint?: string | null
  dependency?: string | null
  trace_id?: string | null
}

export type TMDbListResponse<T = any> = {
  page: number
  total_pages: number
  total_results: number
  results: T[]
}

// ---------- Low-level HTTP ----------
async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`
  const res = await fetch(url, {
    ...init,
    headers: { Accept: "application/json", ...(init?.headers || {}) },
    credentials: init?.credentials ?? "same-origin",
  })

  // Try to parse JSON for both success and error
  const parseJson = async () => {
    try {
      return await res.json()
    } catch {
      return null
    }
  }

  if (!res.ok) {
    const body = (await parseJson()) as ApiErrorEnvelope | null
    // Throw the standardized envelope if present, else a generic one
    if (body && body.code && body.message) {
      throw body
    }
    throw {
      code: "http_error",
      message: `HTTP ${res.status}`,
      hint: null,
      dependency: null,
      trace_id: null,
    } as ApiErrorEnvelope
  }

  const data = (await parseJson()) as T
  return data
}

// ---------- Health ----------
export async function getHealth(): Promise<Health> {
  return http<Health>("/health")
}

// ---------- Search ----------
export type SearchResponse = TMDbListResponse<Movie>

export async function searchMovies(q: string, page = 1): Promise<SearchResponse> {
  const qs = new URLSearchParams({ q, page: String(page) })
  return http<SearchResponse>(`/search?${qs.toString()}`)
}

// ---------- Details ----------
export type DetailsResponse = { movie: Movie; cast: Cast[] }

export function getMovieDetails(id: number) {
  return http<DetailsResponse>(`/details/${id}`)
}

// ---------- Recommendations (by movie) ----------
export type RecommendationsResponse = TMDbListResponse<Movie> & {
  source: "recommendations" | "similar"
}

export function getRecommendations(id: number, page = 1) {
  return http<RecommendationsResponse>(`/recommend/${id}?page=${page}`)
}

// ---------- Providers ----------
export type ProviderItem = { id: number; name: string; logoPath: string | null; link?: string }

export type ProvidersResponse = {
  id: number
  region: string
  link?: string | null
  stream: ProviderItem[]
  rent: ProviderItem[]
  // Optional; some backends don’t expose buy, keep it flexible
  buy?: ProviderItem[]
}

export async function getProviders(id: number, region?: string) {
  const qs = new URLSearchParams()
  if (region) qs.set("region", region)
  const suffix = qs.toString() ? `?${qs.toString()}` : ""
  return http<ProvidersResponse>(`/providers/${id}${suffix}`)
}

// ---------- Mood ----------
export type MoodResponse = TMDbListResponse<Movie> & {
  mood: string
  region: string
}

export async function getMoodRecs(mood: string, page = 1, region?: string): Promise<MoodResponse> {
  const qs = new URLSearchParams({ mood, page: String(page) })
  if (region) qs.set("region", region)
  return http<MoodResponse>(`/recommend/mood?${qs.toString()}`)
}

// ---------- Trending / Popular (paged) ----------
export function getTrending(window: "day" | "week" = "day") {
  return http<TMDbListResponse<Movie>>(`/trending?window=${window}`)
}

export function getPopular(page = 1) {
  return http<TMDbListResponse<Movie>>(`/popular?page=${page}`)
}
