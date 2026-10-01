import { BrowserRouter, Link, Route, Routes } from 'react-router-dom'
import SearchPage from './pages/SearchPage'

function NotFound() {
  return (
    <section>
      <h2>Page not found</h2>
      <Link to="/">Back to search</Link>
    </section>
  )
}

function App() {
  return (
    <BrowserRouter>
      <header className="site-header">
        <Link to="/" className="brand">
          Rater
        </Link>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}

export default App
