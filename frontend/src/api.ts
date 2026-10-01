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

export type User = { id: number; email: string; region: string }

export type Service = { id: number; name: string; logo_path: string | null }

// FastAPI errors are {"detail": "..."} or, for validation errors, {"detail": [{msg, ...}]}.
function errorMessage(body: { detail?: unknown }, status: number): string {
  if (typeof body.detail === 'string') return body.detail
  if (Array.isArray(body.detail) && body.detail.length > 0) {
    return body.detail.map((d: { msg?: string }) => d.msg ?? 'Invalid input').join('; ')
  }
  return `Request failed (${status})`
}

async function request<T>(
  method: 'GET' | 'POST' | 'PUT' | 'DELETE',
  path: string,
  options: { body?: unknown; signal?: AbortSignal } = {},
): Promise<T> {
  // Same-origin requests send the httpOnly auth cookie automatically; JS never touches it.
  const res = await fetch(`/api${path}`, {
    method,
    signal: options.signal,
    headers: options.body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new ApiError(res.status, errorMessage(body, res.status))
  }
  return (res.status === 204 ? undefined : await res.json()) as T
}

// --- movies ---

export function searchMovies(query: string, signal?: AbortSignal): Promise<MovieSearchResult[]> {
  return request('GET', `/movies/search?q=${encodeURIComponent(query)}`, { signal })
}

export function getMovie(tmdbId: number, signal?: AbortSignal): Promise<MovieDetail> {
  return request('GET', `/movies/${tmdbId}`, { signal })
}

// --- auth ---

export function signup(email: string, password: string): Promise<User> {
  return request('POST', '/auth/signup', { body: { email, password } })
}

export function login(email: string, password: string): Promise<User> {
  return request('POST', '/auth/login', { body: { email, password } })
}

export function logout(): Promise<void> {
  return request('POST', '/auth/logout')
}

/** The logged-in user, or null if not logged in. */
export async function getMe(): Promise<User | null> {
  try {
    return await request<User>('GET', '/me')
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) return null
    throw err
  }
}

// --- streaming services ---

export function listServices(): Promise<Service[]> {
  return request('GET', '/services')
}

export function getMyServices(): Promise<Service[]> {
  return request('GET', '/me/services')
}

export function setMyServices(serviceIds: number[]): Promise<Service[]> {
  return request('PUT', '/me/services', { body: { service_ids: serviceIds } })
}
