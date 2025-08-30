// src/lib/img.ts
const TMDB_IMG = "https://image.tmdb.org/t/p"

export function posterUrl(
  path?: string | null,
  size: "w185" | "w342" | "w500" | "w780" | "w1280" = "w342"
) {
  if (!path) return null
  return `${TMDB_IMG}/${size}${path}`
}

export function backdropUrl(
  path?: string | null,
  size: "w780" | "w1280" | "original" = "w1280"
) {
  if (!path) return null
  return `${TMDB_IMG}/${size}${path}`
}

export function providerLogoUrl(path?: string | null, size: "w45" | "w92" = "w92") {
  if (!path) return null
  return `${TMDB_IMG}/${size}${path}`
}

/** NEW: profile image helper for cast */
export function profileUrl(path?: string | null, size: "w185" | "w342" | "w500" = "w185") {
  if (!path) return null
  return `${TMDB_IMG}/${size}${path}`
}

/** Responsive pair for card posters (good default): w185 1x, w342 2x */
export function posterSrcset(path?: string | null) {
  if (!path) return undefined
  const s1 = posterUrl(path, "w185")
  const s2 = posterUrl(path, "w342")
  return `${s1} 1x, ${s2} 2x`
}
