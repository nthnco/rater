import { useEffect, useState } from 'react'

type Status = 'loading' | 'ok' | 'error'

function App() {
  const [apiStatus, setApiStatus] = useState<Status>('loading')

  useEffect(() => {
    fetch('/api/health')
      .then((res) => (res.ok ? res.json() : Promise.reject(res.status)))
      .then((body: { status: string }) => setApiStatus(body.status === 'ok' ? 'ok' : 'error'))
      .catch(() => setApiStatus('error'))
  }, [])

  return (
    <main>
      <h1>Rater</h1>
      <p>Rank the movies you've seen. Get recommendations you'll actually like.</p>
      <p>API: {apiStatus}</p>
    </main>
  )
}

export default App
