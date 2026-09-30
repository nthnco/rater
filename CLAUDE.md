# Working rules for AI assistants on this repo — Rater

This is Nathan's portfolio project. **`DESIGN.md` is the source of truth** —
read it fully (especially Section 0, the working agreement) before touching
any code. If this file and DESIGN.md disagree, ask.

## Boundaries
- Work one build phase (DESIGN.md Section 11) at a time. Stop at the end of
  each phase with a recap: what was built, decisions made, and 3 interview
  questions about it.
- ML/algorithm code (ranking logic, recommenders, evaluation) — and any file
  marked with a `# YOU:` comment at the top — must go slow and
  explain-as-you-go: introduce the concept and design choice BEFORE writing
  code, write in small chunks (not whole files at once), and explain what
  each chunk does and why after writing it. The goal is for Nathan to
  understand and be able to explain every design decision.
- Everything else (auth, CRUD endpoints, Docker, CI, UI, TMDB integration,
  migrations, boilerplate) is fair game to write directly and quickly.
- No generative AI anywhere in the product: no LLM API calls, no API
  embeddings. Classical ML only.
- Data leakage is the #1 ML risk. Any train/test split MUST be temporal (by
  rating timestamp) or held-out-most-recent per user, never random
  shuffling. Flag it loudly if you see a random split near model training.
- MovieLens is offline-only: never commit it, never serve predictions
  trained on it. TMDB API key stays server-side.
- Ask before deviating from DESIGN.md.

## Workflow
- Small, scoped commits. One working step per commit.
- Run `uv run ruff check .` and `uv run pytest` before considering a
  task done.
