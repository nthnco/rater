import { type SubmitEvent, useState } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'

type Mode = 'login' | 'signup'

const COPY = {
  login: { title: 'Log in', submit: 'Log in', switchText: 'New here?', switchLink: 'Create an account' },
  signup: { title: 'Create your account', submit: 'Sign up', switchText: 'Have an account?', switchLink: 'Log in' },
}

/** Only allow redirects within our own app (no open redirects to other sites). */
function safeNext(next: string | null): string | null {
  return next && next.startsWith('/') && !next.startsWith('//') ? next : null
}

export default function AuthPage({ mode }: { mode: Mode }) {
  const auth = useAuth()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const next = safeNext(params.get('next'))
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const copy = COPY[mode]

  if (auth.user) return <Navigate to={next ?? '/'} replace />

  async function onSubmit(e: SubmitEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      if (mode === 'signup') {
        await auth.signup(email, password)
        // Onboarding step 1 (DESIGN.md §2): pick streaming services.
        navigate('/settings/services?welcome=1', { replace: true })
      } else {
        await auth.login(email, password)
        navigate(next ?? '/', { replace: true })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
      setSubmitting(false)
    }
  }

  const otherPath = mode === 'login' ? '/signup' : '/login'
  return (
    <section className="auth-card">
      <h1>{copy.title}</h1>
      <form onSubmit={onSubmit} className="form">
        <label>
          Email
          <input
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete={mode === 'signup' ? 'new-password' : 'current-password'}
            required
            minLength={mode === 'signup' ? 8 : undefined}
            maxLength={128}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {mode === 'signup' && <span className="hint">At least 8 characters.</span>}
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" className="button primary" disabled={submitting}>
          {submitting ? 'One moment…' : copy.submit}
        </button>
      </form>
      <p className="muted">
        {copy.switchText}{' '}
        <Link to={next ? `${otherPath}?next=${encodeURIComponent(next)}` : otherPath}>
          {copy.switchLink}
        </Link>
      </p>
    </section>
  )
}
