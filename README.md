# Rater

A "Beli for movies": rank the movies you've seen by answering "which do you
prefer?" questions, and Rater learns your taste to recommend what to watch
next, filtered to your streaming services. Classical ML only (content-based
similarity, matrix factorization), no LLM wrapper.

See [DESIGN.md](DESIGN.md) for the full design. Write-up and metrics coming
once shipped.

## Running locally

With Docker (Postgres + API + frontend, hot reload):

```sh
cp .env.example .env        # add your TMDB read access token
docker compose up --build
```

- Frontend: http://localhost:5173
- API: http://localhost:8000 (docs at `/docs`)

Without Docker (needs a local Postgres, uv, and Node 24):

```sh
cd backend && uv sync && uv run alembic upgrade head && uv run uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```

Checks (same as CI):

```sh
cd backend && uv run ruff check . ../ml && uv run pytest
cd frontend && npm run lint && npm run build
```

Offline ML experiments (MovieLens, PyTorch) need the extra group:
`cd backend && uv sync --group ml`.
