import { type PosterSize, posterUrl } from '../tmdb'

type Props = { path: string | null; title: string; size?: PosterSize }

export default function Poster({ path, title, size = 'w342' }: Props) {
  const src = posterUrl(path, size)
  if (!src) {
    return <div className="poster poster-missing" aria-label={`${title} (no poster)`} />
  }
  return <img className="poster" src={src} alt={`${title} poster`} loading="lazy" />
}
