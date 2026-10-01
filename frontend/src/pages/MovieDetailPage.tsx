import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError, type MovieDetail, type Person, getMovie } from '../api'
import Poster from '../components/Poster'
import { posterUrl } from '../tmdb'

// The last *finished* request, tagged with the movie id it answered (same pattern as search).
type Finished = { id: number; movie: MovieDetail } | { id: number; error: Error }

export default function MovieDetailPage() {
  const { tmdbId } = useParams()
  const id = Number(tmdbId)
  const validId = Number.isInteger(id) && id > 0
  const [finished, setFinished] = useState<Finished | null>(null)

  useEffect(() => {
    if (!validId) return
    const controller = new AbortController()
    getMovie(id, controller.signal)
      .then((movie) => setFinished({ id, movie }))
      .catch((err: Error) => {
        if (!controller.signal.aborted) setFinished({ id, error: err })
      })
    return () => controller.abort()
  }, [id, validId])

  if (!validId) return <Problem title="That isn't a valid movie link." />
  if (finished?.id !== id) return <p className="muted">Loading…</p>
  if ('error' in finished) return <ErrorView error={finished.error} />
  return <Detail movie={finished.movie} />
}

function ErrorView({ error }: { error: Error }) {
  const status = error instanceof ApiError ? error.status : 0
  if (status === 404) return <Problem title="We couldn't find that movie." />
  if (status === 502) {
    return <Problem title="Couldn't reach our movie data provider. Try again in a minute." />
  }
  return <Problem title="Something went wrong loading this movie." />
}

function Problem({ title }: { title: string }) {
  return (
    <section>
      <p className="error">{title}</p>
      <Link to="/">Back to search</Link>
    </section>
  )
}

function Detail({ movie }: { movie: MovieDetail }) {
  const facts = [
    movie.year,
    movie.runtime_min ? formatRuntime(movie.runtime_min) : null,
    movie.genres.join(', '),
  ].filter(Boolean)

  return (
    <article className="movie-detail">
      <Poster path={movie.poster_path} title={movie.title} size="w500" />
      <div className="movie-info">
        <h1>{movie.title}</h1>
        {facts.length > 0 && <p className="muted">{facts.join(' · ')}</p>}
        {movie.directors.length > 0 && (
          <p>
            <strong>Directed by</strong> {names(movie.directors)}
          </p>
        )}
        {movie.top_cast.length > 0 && (
          <p>
            <strong>Starring</strong> {names(movie.top_cast)}
          </p>
        )}
        {movie.overview && <p className="overview">{movie.overview}</p>}
        {movie.vote_average !== null && movie.vote_count ? (
          <p className="muted">
            TMDB rating {movie.vote_average.toFixed(1)}/10 ({movie.vote_count.toLocaleString()}{' '}
            votes)
          </p>
        ) : null}
        <WhereToWatch movie={movie} />
      </div>
    </article>
  )
}

function WhereToWatch({ movie }: { movie: MovieDetail }) {
  return (
    <section className="where-to-watch">
      <h2>Where to watch</h2>
      {movie.providers.length === 0 ? (
        <p className="muted">Not on any subscription service in the {movie.providers_region}.</p>
      ) : (
        <ul className="providers">
          {movie.providers.map((p) => {
            const logo = posterUrl(p.logo_path, 'w92')
            return (
              <li key={p.id} className="provider">
                {logo && <img src={logo} alt="" />}
                <span>{p.name.trim()}</span>
              </li>
            )
          })}
        </ul>
      )}
      {/* Required wherever provider data appears (DESIGN.md §4). */}
      <p className="attribution muted">Streaming data from JustWatch.</p>
    </section>
  )
}

function names(people: Person[]): string {
  return people.map((p) => p.name).join(', ')
}

function formatRuntime(minutes: number): string {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return h > 0 ? `${h}h ${m}m` : `${m}m`
}
