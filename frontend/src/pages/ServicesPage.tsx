import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { type Service, getMyServices, listServices, setMyServices } from '../api'
import { posterUrl } from '../tmdb'

type Loaded = { services: Service[]; selected: Set<number> }

export default function ServicesPage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const welcome = params.has('welcome') // arrived straight from signup
  const [loaded, setLoaded] = useState<Loaded | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<{ kind: 'ok' | 'error'; text: string } | null>(null)

  useEffect(() => {
    let cancelled = false
    Promise.all([listServices(), getMyServices()])
      .then(([services, mine]) => {
        if (!cancelled) setLoaded({ services, selected: new Set(mine.map((s) => s.id)) })
      })
      .catch((err: Error) => {
        if (!cancelled) setLoadError(err.message)
      })
    return () => {
      cancelled = true
    }
  }, [])

  function toggle(id: number) {
    if (!loaded) return
    const selected = new Set(loaded.selected)
    if (selected.has(id)) selected.delete(id)
    else selected.add(id)
    setLoaded({ ...loaded, selected })
    setMessage(null)
  }

  async function save() {
    if (!loaded) return
    setSaving(true)
    setMessage(null)
    try {
      await setMyServices([...loaded.selected])
      if (welcome) {
        navigate('/', { replace: true })
        return
      }
      setMessage({ kind: 'ok', text: 'Saved.' })
    } catch (err) {
      setMessage({ kind: 'error', text: err instanceof Error ? err.message : 'Could not save' })
    }
    setSaving(false)
  }

  if (loadError) return <p className="error">{loadError}</p>
  if (!loaded) return <p className="muted">Loading…</p>

  return (
    <section>
      <h1>{welcome ? 'Which streaming services do you have?' : 'My streaming services'}</h1>
      <p className="muted">
        Used only to filter your recommendations. You can still rank any movie, wherever you
        watched it.
      </p>

      <ul className="service-grid">
        {loaded.services.map((s) => {
          const logo = posterUrl(s.logo_path, 'w92')
          const on = loaded.selected.has(s.id)
          return (
            <li key={s.id}>
              <button
                type="button"
                className={`service-tile${on ? ' selected' : ''}`}
                aria-pressed={on}
                onClick={() => toggle(s.id)}
              >
                {logo && <img src={logo} alt="" />}
                <span>{s.name}</span>
              </button>
            </li>
          )
        })}
      </ul>

      <div className="actions">
        <button type="button" className="button primary" onClick={save} disabled={saving}>
          {saving ? 'Saving…' : welcome ? 'Continue' : 'Save'}
        </button>
        {welcome && (
          <button type="button" className="button link" onClick={() => navigate('/')}>
            Skip for now
          </button>
        )}
        {message && <span className={message.kind === 'ok' ? 'muted' : 'error'}>{message.text}</span>}
      </div>
      <p className="attribution muted">Streaming service data from JustWatch.</p>
    </section>
  )
}
