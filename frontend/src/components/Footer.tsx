// TMDB's free API terms require their logo and this exact notice (DESIGN.md §4).
// The logo is TMDB's official file from themoviedb.org/about/logos-attribution.
export default function Footer() {
  return (
    <footer className="site-footer">
      <a href="https://www.themoviedb.org/" target="_blank" rel="noopener noreferrer">
        <img src="/tmdb-logo.svg" alt="TMDB" className="tmdb-logo" />
      </a>
      <p>This product uses the TMDB API but is not endorsed or certified by TMDB.</p>
    </footer>
  )
}
