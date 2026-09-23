# Working rules for AI assistants on this repo — Rater

This is Nathan's portfolio project. Read this before touching any code.

## Boundaries
- Code under `ml/` marked with a `# YOU:` comment at the top of the file
  is the core ML/algorithm work for this project. AI can write this
  code, but must go slow and explain-as-you-go: introduce the concept
  and design choice BEFORE writing code, write in small chunks (not
  whole files at once), and explain what each chunk does and why after
  writing it. Never drop a large finished implementation with no
  walkthrough — the goal is for Nathan to understand and be able to
  explain every design decision, not just have working code.
- Everything else (auth, CRUD endpoints, Docker, CI, UI, third-party API
  integration, migrations, boilerplate) is fair game for AI to write
  directly and quickly, no walkthrough needed.
- Data leakage is the #1 risk in this project. Any train/test split MUST
  be temporal (by rating timestamp) or held-out-recent, never random
  shuffling. Flag it loudly if you see a random split anywhere near
  model training code.

## Workflow
- Small, scoped commits. One working step per commit.
- Run `uv run ruff check .` and `uv run pytest` before considering a
  task done.
