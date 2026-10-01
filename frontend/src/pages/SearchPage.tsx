import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { type MovieSearchResult, searchMovies } from '../api'
import Poster from '../components/Poster'

const DEBOUNCE_MS = 300

// The last *finished* search, tagged with the query it answered.
type Finished =
  | { query: string; results: MovieSearchResult[] }
  | { query: string; error: string }

type SearchState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'done'; results: MovieSearchResult[] }
  | { status: 'error'; message: string }

// Idle and loading aren't stored; they're derived: loading = "no answer yet for this query".
function deriveState(query: string, finished: Finished | null): SearchState {
  if (!query) return { status: 'idle' }
  if (finished?.query !== query) return { status: 'loading' }
  return 'error' in finished
    ? { status: 'error', message: finished.error }
    : { status: 'done', results: finished.results }
}

export default function SearchPage() {
  // The URL (?q=...) is the source of truth for what's searched, so Back restores results.
  const [params, setParams] = useSearchParams()
  const query = params.get('q') ?? ''
  const [text, setText] = useState(query)
  const [finished, setFinished] = useState<Finished | null>(null)
  const state = deriveState(query, finished)

  // 1) Debounce: copy the typed text into the URL only after a pause in typing.
  //    Each keystroke clears the previous timer, so only the last one fires.
  useEffect(() => {
    const timer = setTimeout(() => {
      const trimmed = text.trim()
      if (trimmed !== query) setParams(trimmed ? { q: trimmed } : {}, { replace: true })
    }, DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [text, query, setParams])

  // 2) Fetch when the URL query changes. Aborting the previous request on every change
  //    means a slow, stale response can never overwrite newer results.
  useEffect(() => {
    if (!query) return
    const controller = new AbortController()
    searchMovies(query, controller.signal)
      .then((results) => setFinished({ query, results }))
      .catch((err: Error) => {
        if (!controller.signal.aborted) setFinished({ query, error: err.message })
      })
    return () => controller.abort()
  }, [query])

  return (
    <section>
      <input
        type="search"
        className="search-input"
        placeholder="Search any movie…"
        aria-label="Search movies"
        value={text}
        onChange={(e) => setText(e.target.value)}
        autoFocus
      />

      {state.status === 'loading' && <p className="muted">Searching…</p>}
      {state.status === 'error' && <p className="error">{state.message}</p>}
      {state.status === 'done' && state.results.length === 0 && (
        <p className="muted">No movies found for “{query}”.</p>
      )}
      {state.status === 'done' && state.results.length > 0 && (
        <ul className="poster-grid">
          {state.results.map((movie) => (
            <li key={movie.tmdb_id}>
              <Link to={`/movies/${movie.tmdb_id}`} className="poster-card">
                <Poster path={movie.poster_path} title={movie.title} size="w342" />
                <span className="poster-title">{movie.title}</span>
                {movie.year && <span className="muted">{movie.year}</span>}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
