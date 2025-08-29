const BASE = (import.meta as any).env?.VITE_TMDB_IMG_BASE || "https://image.tmdb.org/t/p"

export function posterUrl(path?: string | null, size: string = "w342"): string | null {
  if (!path) return null
  return `${BASE}/${size}${path}`
}

export function profileUrl(path?: string | null, size: string = "w185"): string | null {
  if (!path) return null
  return `https://image.tmdb.org/t/p/${size}${path}`
}

export function providerLogoUrl(path?: string | null, size: string = "w92"): string | null {
  if (!path) return null
  return `https://image.tmdb.org/t/p/${size}${path}`
}

