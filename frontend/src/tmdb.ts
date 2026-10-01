// Posters are hotlinked from TMDB's image CDN, never downloaded or stored (DESIGN.md §4).
const IMAGE_BASE = 'https://image.tmdb.org/t/p'

export type PosterSize = 'w92' | 'w185' | 'w342' | 'w500'

export function posterUrl(path: string | null, size: PosterSize = 'w342'): string | null {
  return path ? `${IMAGE_BASE}/${size}${path}` : null
}
