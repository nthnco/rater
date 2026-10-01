import { BrowserRouter, Link, Route, Routes, useNavigate } from 'react-router-dom'
import AuthProvider from './auth/AuthProvider'
import RequireAuth from './auth/RequireAuth'
import { useAuth } from './auth/useAuth'
import Footer from './components/Footer'
import AuthPage from './pages/AuthPage'
import MovieDetailPage from './pages/MovieDetailPage'
import SearchPage from './pages/SearchPage'
import ServicesPage from './pages/ServicesPage'

function NotFound() {
  return (
    <section>
      <h2>Page not found</h2>
      <Link to="/">Back to search</Link>
    </section>
  )
}

function Header() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function onLogout() {
    await logout()
    navigate('/')
  }

  return (
    <header className="site-header">
      <Link to="/" className="brand">
        Rater
      </Link>
      <nav className="nav">
        {user === undefined ? null : user ? (
          <>
            <span className="muted nav-email">{user.email}</span>
            <Link to="/settings/services">My services</Link>
            <button type="button" className="button link" onClick={onLogout}>
              Log out
            </button>
          </>
        ) : (
          <>
            <Link to="/login">Log in</Link>
            <Link to="/signup" className="button primary small">
              Sign up
            </Link>
          </>
        )}
      </nav>
    </header>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Header />
        <main>
          <Routes>
            <Route path="/" element={<SearchPage />} />
            <Route path="/movies/:tmdbId" element={<MovieDetailPage />} />
            <Route path="/login" element={<AuthPage mode="login" />} />
            <Route path="/signup" element={<AuthPage mode="signup" />} />
            <Route
              path="/settings/services"
              element={
                <RequireAuth>
                  <ServicesPage />
                </RequireAuth>
              }
            />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
        <Footer />
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
