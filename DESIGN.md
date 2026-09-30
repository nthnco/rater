# Rater: Design Document

Rater is a "Beli for movies." Users rank the movies they've seen by answering simple
"which do you prefer?" questions, and Rater learns their taste to recommend what to watch
next, including new releases and what's available on their streaming services.

This document is the source of truth for the project. Read it fully before writing any code.

---

## 0. Working agreement (read this first)

The developer is building Rater to (a) have a strong portfolio project for SWE/ML job
applications and (b) genuinely learn, and needs to be able to explain every decision in an
interview.

Claude Code should:

- **Go slow.** Work on one build phase (Section 11) at a time. Do not scaffold the whole
  project at once. Stop at the end of each phase.
- **Explain as you go, in plain language.** Before writing non-trivial code, say what you're
  about to do and why. After writing it, explain the key concept or design choice (for
  example: "why binary search here," "why store order instead of scores"). Assume the
  developer is smart but new to this specific topic.
- It's fine to write the ML and algorithm code, as long as it comes with explanation the
  developer can repeat back.
- **End each phase with a short recap:** what was built, what decisions were made, and 3
  questions an interviewer might ask about it.
- **Ask before deviating from this document.** If something here seems wrong, say so and
  propose an alternative instead of silently changing course.
- **No generative AI.** No LLM API calls, no embeddings-from-an-API, no "GPT wrapper"
  features anywhere in the product. All ML is classical (content-based similarity, matrix
  factorization, and so on) so the developer can explain it end to end.
- **Write tests as you go**, especially for the ranking logic (Section 5). Use small commits
  with clear messages.

---

## 1. Goals and non-goals

### Goals

- Let users rank any movie they've seen using a Beli-style pairwise flow.
- Show each user a taste profile and a predicted score for any movie.
- Recommend movies they haven't seen, filterable to their streaming services, including new
  releases.
- Be deployed at a public URL with real users, tests, CI, and a README with real metrics.

### Non-goals (v1)

- Generative AI features of any kind.
- Social features (friends, feeds, comments).
- Mobile app.
- Monetization (see Section 4 on TMDB terms; commercial use needs a separate license).
- Auto-importing watch history from streaming services.

---

## 2. Core user flow

1. Sign up, then pick the streaming services you have (used only to filter recommendations).
2. Search any movie (not limited to your services), add it, and rank it (Section 5).
3. After about 10 ranked movies, recommendations unlock. Until then, show popular movies and
   prompt the user to rank more.
4. Browse "For You" (default filter: only my services, with a toggle to include everything),
   "New Releases," a taste profile, and movie pages showing a predicted score.

**Key rule:** ranking is never restricted by streaming services. Services only filter
recommendations.

---

## 3. Tech stack

| Layer           | Choice                                                  | Notes                                                   |
| --------------- | ------------------------------------------------------- | ------------------------------------------------------- |
| Frontend        | React (TypeScript)                                      | Vite for the build                                      |
| Backend         | FastAPI (Python)                                        | ML code lives next to the API                           |
| Database        | PostgreSQL                                              | via SQLAlchemy 2.x + Alembic migrations                 |
| Movie data      | TMDB API                                                | metadata, search, watch providers, now playing/upcoming |
| ML              | NumPy, pandas, scikit-learn, PyTorch                    | classical models only                                   |
| Background jobs | APScheduler or plain cron in a container                | Airflow is overkill here                                |
| Infra           | Docker + docker-compose, GitHub Actions CI              | hosting decided in Phase 8                              |
| Auth            | Email + password (bcrypt or argon2), JWT in an httpOnly cookie | Google OAuth is a later option                   |

---

## 4. Data sources and licensing

**TMDB is the only production data source.** Free for non-commercial use. Requirements:

- Show the TMDB logo and this notice in the footer: "This product uses the TMDB API but is
  not endorsed or certified by TMDB."
- Watch-provider data comes from JustWatch. Show JustWatch attribution wherever provider data
  appears.
- Hotlink posters using TMDB's image URLs. Do not save copies of images.
- Do not republish a bulk copy of TMDB data. Cache metadata for the movies users actually
  touch, and refresh periodically (`metadata_fetched_at`).
- Keep the API key server-side. The frontend calls our backend, never TMDB directly.
- Respect TMDB's rate limits and cache aggressively.
- If the app ever earns money, contact TMDB about a commercial license first.

**MovieLens** (GroupLens research dataset) is used **offline only**, for developing and
evaluating models (Section 8). Never ship it in the repo, never redistribute it, and never use
it to serve production recommendations. Use its `links.csv` to map MovieLens IDs to TMDB IDs.

**User rankings and comparisons are the project's own data.**

---

## 5. The ranking mechanic (the heart of the app)

### 5.1 How it feels to the user

1. The user searches a movie and picks it.
2. "Did you like it?" gives three buckets: **liked**, **fine**, **disliked**.
3. Rater asks "Which do you prefer?" against a movie already in that bucket, starting with the
   middle one.
4. Each answer halves the remaining range (binary search). About 3 to 5 questions place the
   movie, even in a long list.
5. A "too close to call" button places the new movie directly below the one it was compared
   to.
6. If the bucket is empty, the movie is placed immediately with no questions.

### 5.2 Data invariants (test these constantly)

Each user has one ordered list. For every user:

- `position` values are exactly `0..n-1` with no gaps and no duplicates (0 = best).
- Buckets are contiguous: every liked movie has a lower position than every fine movie, which
  has a lower position than every disliked movie.
- Bucket coding is 0 = liked, 1 = fine, 2 = disliked, so sorting ascending by
  `(bucket, position)` matches sorting by `position`.

### 5.3 Insertion algorithm

Let `lo` be the number of movies in buckets ranked above the target bucket, and
`hi = lo + (number of movies in the target bucket)`. The new movie will be inserted at some
index in `[lo, hi]`.

```python
def start_ranking(user, movie, bucket):
    lo = count(user, bucket < bucket)
    hi = lo + count(user, bucket == bucket)
    if lo == hi:
        insert_at(user, movie, bucket, lo)       # empty bucket: no questions
        return Done()
    session = create_session(user, movie, bucket, low=lo, high=hi, n_at_start=count(user))
    return NextComparison(compare_to=movie_at(user, position=(lo + hi) // 2))

def answer(session, choice):                     # choice in {"new", "existing", "tie"}
    mid = (session.low + session.high) // 2
    record_comparison(session, mid, choice)
    if choice == "new":        session.high = mid          # new movie ranks above mid
    elif choice == "existing": session.low = mid + 1       # new movie ranks below mid
    else:                      session.low = session.high = mid + 1   # tie: just below mid
    if session.low == session.high:
        insert_at(session.user, session.movie, session.bucket, session.low)
        return Done()
    return NextComparison(compare_to=movie_at(session.user, (session.low + session.high) // 2))
```

**Worked example:** bucket slice is `[A, B, C]` (A best). Compare with B first. If the new
movie N beats B, compare with A: if N beats A it goes first, otherwise it goes between A and
B. If B beats N, compare with C, and N lands either between B and C or last. At most
`ceil(log2(k + 1))` questions for a bucket of k movies.

### 5.4 Inserting and deleting (single transaction)

```sql
-- insert at position p
UPDATE rankings SET position = position + 1 WHERE user_id = :u AND position >= :p;
INSERT INTO rankings (user_id, movie_id, bucket, position) VALUES (:u, :m, :b, :p);

-- delete
DELETE FROM rankings WHERE user_id = :u AND movie_id = :m RETURNING position;
UPDATE rankings SET position = position - 1 WHERE user_id = :u AND position > :deleted_position;
```

The `(user_id, position)` unique constraint must be `DEFERRABLE INITIALLY DEFERRED` so the
shift doesn't trip over itself mid-transaction.

**Concurrency:** two sessions for the same user could interleave their shifts. Each
insert/delete transaction first locks the user's row (`SELECT ... FROM users WHERE id = :u FOR
UPDATE`) so a user's list is only ever modified by one transaction at a time.

**Re-ranking** a movie = delete it, then run the flow again. Preserve the original
`created_at` on re-insert (set `updated_at` to now), since `created_at` is what temporal
train/test splits use.

**Sessions:** a ranking takes several requests, so state lives in a `ranking_sessions` row. If
the user's list changed since the session began (`n_at_start` no longer matches), invalidate
the session and restart it. Sessions expire after about 30 minutes.

### 5.5 Score = f(position), computed on read, never stored

Store the order, not the score. Inserting a movie shifts everyone's relative spot in the
bucket, so saved scores would go stale.

```python
BUCKET_RANGES = {0: (7.0, 10.0), 1: (4.0, 6.9), 2: (0.0, 3.9)}   # liked, fine, disliked

def display_score(bucket, index_in_bucket, bucket_size):          # index 0 = best in bucket
    lo, hi = BUCKET_RANGES[bucket]
    if bucket_size == 1:
        return round((lo + hi) / 2, 1)
    frac = index_in_bucket / (bucket_size - 1)
    return round(hi - frac * (hi - lo), 1)
```

### 5.6 Required tests

- **Oracle test:** create a hidden "true" ordering, simulate a user answering comparisons from
  it, insert many random movies, and assert the final list matches the true order.
- **Comparison count:** assert no insertion asks more than `ceil(log2(k + 1))` questions.
- **Invariants:** after random inserts and deletes, positions are `0..n-1` and buckets are
  contiguous.
- **Edge cases:** first movie ever, empty bucket, last-in-bucket, tie, re-rank, stale session.

---

## 6. Database schema (PostgreSQL)

```sql
CREATE TABLE users (
  id            BIGSERIAL PRIMARY KEY,
  email         TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  region        CHAR(2) NOT NULL DEFAULT 'US',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE streaming_services (
  id        INT PRIMARY KEY,          -- TMDB provider_id
  name      TEXT NOT NULL,
  logo_path TEXT
);

CREATE TABLE user_services (
  user_id    BIGINT REFERENCES users(id) ON DELETE CASCADE,
  service_id INT    REFERENCES streaming_services(id),
  PRIMARY KEY (user_id, service_id)
);

CREATE TABLE movies (
  id                  BIGSERIAL PRIMARY KEY,
  tmdb_id             INT UNIQUE NOT NULL,
  title               TEXT NOT NULL,
  release_date        DATE,
  overview            TEXT,
  poster_path         TEXT,
  runtime_min         INT,
  genres              TEXT[],
  directors           INT[],          -- TMDB person ids (people.id)
  top_cast            INT[],          -- top ~5 billed, TMDB person ids (people.id)
  keywords            INT[],          -- TMDB keyword ids
  tmdb_popularity     REAL,
  tmdb_vote_average   REAL,
  tmdb_vote_count     INT,
  metadata_fetched_at TIMESTAMPTZ
);

CREATE TABLE people (                 -- names for directors/top_cast (display, taste profile)
  id   INT PRIMARY KEY,               -- TMDB person id
  name TEXT NOT NULL
);

CREATE TABLE movie_providers (        -- which services carry a movie, per region
  movie_id   BIGINT REFERENCES movies(id) ON DELETE CASCADE,
  region     CHAR(2) NOT NULL,
  service_id INT REFERENCES streaming_services(id),
  fetched_at TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (movie_id, region, service_id)    -- flat-rate (subscription) only in v1
);

CREATE TABLE rankings (
  user_id    BIGINT REFERENCES users(id) ON DELETE CASCADE,
  movie_id   BIGINT REFERENCES movies(id),
  bucket     SMALLINT NOT NULL CHECK (bucket IN (0, 1, 2)),   -- 0 liked, 1 fine, 2 disliked
  position   INT NOT NULL CHECK (position >= 0),              -- 0 = best
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, movie_id),
  CONSTRAINT rankings_user_position_uq UNIQUE (user_id, position) DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE ranking_sessions (
  id         UUID PRIMARY KEY,
  user_id    BIGINT REFERENCES users(id) ON DELETE CASCADE,
  movie_id   BIGINT REFERENCES movies(id),
  bucket     SMALLINT NOT NULL,
  low        INT NOT NULL,
  high       INT NOT NULL,
  n_at_start INT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ NOT NULL
);

-- Every answered "which do you prefer?" is a clean pairwise preference. Cheap to record now,
-- valuable later as training data.
CREATE TABLE comparisons (
  id              BIGSERIAL PRIMARY KEY,
  user_id         BIGINT REFERENCES users(id) ON DELETE CASCADE,
  winner_movie_id BIGINT REFERENCES movies(id),
  loser_movie_id  BIGINT REFERENCES movies(id),
  is_tie          BOOLEAN NOT NULL DEFAULT FALSE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE recommendations (        -- precomputed by background jobs
  user_id       BIGINT REFERENCES users(id) ON DELETE CASCADE,
  movie_id      BIGINT REFERENCES movies(id),
  predicted     REAL NOT NULL,        -- predicted score on the 0-10 scale
  source        TEXT NOT NULL,        -- 'popularity' | 'content' | 'cf' | 'hybrid'
  model_version TEXT NOT NULL,
  generated_at  TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (user_id, movie_id)
);
```

Add indexes on `rankings(user_id, bucket, position)`, `movies(release_date)`, and
`recommendations(user_id, predicted DESC)`.

---

## 7. API (FastAPI, all `/me/*` routes require auth)

| Method | Route                                         | Purpose                                                   |
| ------ | --------------------------------------------- | --------------------------------------------------------- |
| POST   | `/auth/signup`, `/auth/login`, `/auth/logout` | account basics                                            |
| GET    | `/me`                                         | current user                                              |
| GET    | `/services`                                   | list of supported streaming services                      |
| PUT    | `/me/services`                                | set the user's services                                   |
| GET    | `/movies/search?q=`                           | proxy to TMDB search (all movies)                         |
| GET    | `/movies/{tmdb_id}`                           | movie details plus providers, cached                      |
| GET    | `/movies/{tmdb_id}/prediction`                | predicted score for this user                             |
| GET    | `/me/rankings`                                | ordered list with computed scores                         |
| POST   | `/me/rankings/start`                          | body: `{tmdb_id, bucket}`; returns the first comparison or Done |
| POST   | `/me/rankings/sessions/{id}/answer`           | body: `{choice: new/existing/tie}`; returns the next comparison or Done |
| DELETE | `/me/rankings/{tmdb_id}`                      | remove a movie                                            |
| GET    | `/me/taste`                                   | taste profile                                             |
| GET    | `/me/recommendations?only_my_services=true&limit=` | "For You"                                            |
| GET    | `/me/new-releases?only_my_services=true`      | now playing and upcoming, scored for this user            |

---

## 8. Recommender (classical ML, built in layers)

Each layer must beat the one before it on the offline evaluation (Section 9) or it doesn't
ship.

### Layer 0: Popularity baseline

Rank unseen movies by a weighted rating (a Bayesian average of `vote_average` and
`vote_count`, so a 9.5 from 12 votes doesn't beat an 8.2 from 30,000). Filter by the user's
services if requested. This is the number to beat.

### Layer 1: Content-based

- **Movie vector:** multi-hot genres, TF-IDF of keywords, multi-hot directors and top cast,
  decade, and a runtime bucket. Normalize.
- **User profile vector:** weighted average of the vectors of their ranked movies, with weight
  `(score - 5.0)`, so liked movies pull the profile toward them and disliked movies push it
  away.
- **Recommendation score:** cosine similarity between the profile and each candidate.
- **Predicted score for a movie:** k-nearest-neighbors over the user's own ranked movies (k
  about 20). Take the similarity-weighted average of their scores, and fall back to the user's
  mean if nothing is similar.

This works with a single user and works for brand-new releases, since it needs no other users'
data.

### Layer 2: Collaborative filtering (matrix factorization)

- Learn latent "taste" factors for users and movies from the user-by-movie score matrix.
  Implement it in PyTorch (biases plus latent factors, MSE loss with L2 regularization) so the
  math is understood, and compare it to a library implementation.
- Develop and tune on MovieLens offline (ratings converted to the 0-10 scale). **Never serve
  MovieLens-trained output in production.**
- In production, train on Rater's own data once there are enough users (a rough bar: 30+
  users with 20+ rankings each). Until then, content-based drives production.

### Layer 3: Hybrid

`final = alpha * cf + (1 - alpha) * content`, where `alpha` grows with how many rankings the
user has and how many rankings the movie has. New releases have zero rankings, so
`alpha = 0` and they're scored on content alone.

### Stretch

Use the `comparisons` table to fit a Bradley-Terry model on pairwise preferences.

### Background jobs

- **Nightly:** pull TMDB `now_playing` and `upcoming`, upsert into `movies`, build feature
  vectors, and refresh recommendations for active users.
- **Weekly:** refresh `movie_providers` and stale `movies` metadata.
- **On ranking change:** mark that user's recommendations stale (or recompute cheaply on
  request in early versions).

---

## 9. Evaluation (this is what goes on the resume)

**Offline, on MovieLens** (time-based split, or leave-*latest*-out per user: hold out each
user's most recent rating(s) by timestamp. Never a random split or random leave-one-out; that
leaks future taste into training):

- **Score prediction:** RMSE and MAE, compared against "global mean," "user mean," and Layer 0.
- **Ranking quality:** NDCG@10 and Recall@10 for held-out liked movies.

**Online, on real Rater users** once there are some: hide part of each user's rankings,
predict them, and compare against the popularity baseline. Log the numbers in the README (for
example: "collected N rankings from M users; hybrid model improved NDCG@10 by X% over the
popularity baseline").

Keep a `notebooks/` or `ml/experiments/` folder with reproducible evaluation scripts.

---

## 10. Frontend pages

- **Signup / Login**
- **Onboarding:** pick services, then rank about 10 starter movies (offer a popular list to
  seed from)
- **My List:** ordered by rank, grouped by bucket, with computed scores
- **Add Movie:** search, choose a bucket, answer comparisons, see the result
- **Movie Detail:** poster, providers ("Where to watch," with JustWatch credit), your rank if
  ranked, and a predicted score if not
- **For You:** recommendations with an "only on my services" toggle (default on)
- **New Releases**
- **Taste Profile:** top genres, directors, actors, and decades from their list (simple
  counting and averaging, useful before any ML)
- **Footer:** TMDB logo and required notice

---

## 11. Build phases (do them in order, stop after each)

- **Phase 0: Setup.** Repo layout, docker-compose (Postgres, API, frontend), FastAPI
  hello-world, React scaffold, Alembic, GitHub Actions running lint and tests.
  *Done when:* `docker compose up` runs everything and CI is green.
- **Phase 1: Movie data.** TMDB client, `/movies/search`, `/movies/{id}` with caching into
  `movies`, footer attribution.
  *Done when:* searching returns results and detail pages are cached after the first view.
- **Phase 2: Accounts and services.** Signup/login, `/services`, `/me/services`.
  *Done when:* a user can sign up and save their services.
- **Phase 3: Ranking (the core).** Schema, sessions, insertion and deletion, score
  calculation, the Add Movie UI, My List.
  *Done when:* every test in Section 5.6 passes and a user can rank 20 movies smoothly.
- **Phase 4: Baseline recommendations and first deploy.** Layer 0 plus the provider filter,
  "For You" page, deploy publicly.
  *Done when:* there is a live URL and a friend can sign up and get recommendations on their
  services.
- **Phase 5: Taste profile.** `/me/taste` and its page.
- **Phase 6: Content-based and new releases.** Layer 1, predicted score on movie pages, the
  nightly job, the New Releases page.
  *Done when:* predicted scores appear and new releases are scored per user.
- **Phase 7: Evaluation and collaborative filtering.** MovieLens offline pipeline, Layer 2 and
  Layer 3, results written up.
  *Done when:* there is a results table comparing all layers, and only layers that beat the
  baseline ship.
- **Phase 8: Polish and launch.** Hosting decision (a small VM or Fly/Render, or AWS if wanted
  for the resume), README with screenshots, architecture diagram, and metrics, invite 20 to 50
  real users.

---

## 12. Suggested repo layout

```
rater/
  DESIGN.md
  README.md
  docker-compose.yml
  .github/workflows/ci.yml
  backend/
    app/
      api/          # routes
      models/       # SQLAlchemy models
      services/     # ranking logic, TMDB client, business logic
      ml/           # features, recommenders, evaluation
      jobs/         # nightly and weekly tasks
    alembic/
    tests/
  frontend/
    src/
  ml/
    experiments/    # MovieLens evaluation scripts and notebooks
```

---

## 13. Decisions still open

- Hosting provider (decide in Phase 8).
- Whether to add Google OAuth after email/password works.
- Region support beyond US (default US for now; the schema already stores region).
- Whether ties should count as a distinct signal in the models (start by treating them as
  equal preference).
