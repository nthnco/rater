// The only place the frontend talks to our backend. Types mirror backend/app/api/schemas.py.
// Requests go to /api/*, which Vite proxies to FastAPI; the browser never calls TMDB directly.

export type MovieSearchResult = {
  tmdb_id: number
  title: string
  year: number | null
  poster_path: string | null
}

export type Person = { id: number; name: string }

export type Provider = { id: number; name: string; logo_path: string | null }

export type MovieDetail = {
  tmdb_id: number
  title: string
  year: number | null
  release_date: string | null
  overview: string | null
  poster_path: string | null
  runtime_min: number | null
  genres: string[]
  directors: Person[]
  top_cast: Person[]
  vote_average: number | null
  vote_count: number | null
  providers_region: string
  providers: Provider[]
}

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(`/api${path}`, { signal })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(res.status, body.detail ?? `Request failed (${res.status})`)
  }
  return res.json() as Promise<T>
}

export function searchMovies(query: string, signal?: AbortSignal): Promise<MovieSearchResult[]> {
  return getJson(`/movies/search?q=${encodeURIComponent(query)}`, signal)
}

export function getMovie(tmdbId: number, signal?: AbortSignal): Promise<MovieDetail> {
  return getJson(`/movies/${tmdbId}`, signal)
}
