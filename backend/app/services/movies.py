"""Movie metadata: parse TMDB details and cache them in our DB (read-through, DESIGN.md §4)."""

from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, selectinload

from app.models import Movie, MovieProvider, Person, StreamingService
from app.services.tmdb import TMDBClient, TMDBUnavailableError

CACHE_TTL = timedelta(days=7)
PROVIDER_REGION = "US"  # v1 default; becomes the user's region once users have one
TOP_CAST_SIZE = 5


@dataclass
class ParsedService:
    id: int
    name: str
    logo_path: str | None


@dataclass
class ParsedMovie:
    """TMDB details flattened into exactly what we store. No DB or network involved."""

    fields: dict[str, Any]  # column name -> value for the movies table
    people: dict[int, str] = field(default_factory=dict)  # person id -> name
    services: list[ParsedService] = field(default_factory=list)  # flat-rate in PROVIDER_REGION


def parse_details(raw: dict[str, Any]) -> ParsedMovie:
    credits = raw.get("credits") or {}
    crew = credits.get("crew") or []
    cast = sorted(credits.get("cast") or [], key=lambda c: c.get("order", 1_000_000))

    # A person can appear in crew more than once (e.g. Director and Writer); keep each once.
    directors = list(dict.fromkeys(c["id"] for c in crew if c.get("job") == "Director"))
    top_cast = [c["id"] for c in cast[:TOP_CAST_SIZE]]

    people = {c["id"]: c["name"] for c in crew if c["id"] in directors}
    people |= {c["id"]: c["name"] for c in cast[:TOP_CAST_SIZE]}

    region = ((raw.get("watch/providers") or {}).get("results") or {}).get(PROVIDER_REGION) or {}
    services = [
        ParsedService(p["provider_id"], p["provider_name"], p.get("logo_path"))
        for p in region.get("flatrate") or []
    ]

    fields = {
        "tmdb_id": raw["id"],
        "title": raw.get("title") or raw.get("original_title") or "Untitled",
        "release_date": _parse_date(raw.get("release_date")),
        "overview": raw.get("overview") or None,
        "poster_path": raw.get("poster_path"),
        "runtime_min": raw.get("runtime") or None,  # TMDB uses 0 for unknown
        "genres": [g["name"] for g in raw.get("genres") or []],
        "directors": directors,
        "top_cast": top_cast,
        "keywords": [k["id"] for k in (raw.get("keywords") or {}).get("keywords") or []],
        "tmdb_popularity": raw.get("popularity"),
        "tmdb_vote_average": raw.get("vote_average"),
        "tmdb_vote_count": raw.get("vote_count"),
    }
    return ParsedMovie(fields=fields, people=people, services=services)


def _parse_date(value: str | None) -> date | None:
    try:
        return date.fromisoformat(value) if value else None  # TMDB sends "" when unknown
    except ValueError:
        return None


def is_fresh(fetched_at: datetime | None, now: datetime) -> bool:
    return fetched_at is not None and now - fetched_at < CACHE_TTL


def get_movie(db: Session, tmdb: TMDBClient, tmdb_id: int, now: datetime | None = None) -> Movie:
    """Read-through cache: serve from our DB if fresh, otherwise fetch from TMDB and upsert.

    If TMDB is unavailable but we hold a stale copy, serve the stale copy.
    """
    now = now or datetime.now(UTC)
    cached = _load(db, tmdb_id)
    if cached is not None and is_fresh(cached.metadata_fetched_at, now):
        return cached

    try:
        raw = tmdb.movie_details(tmdb_id)
    except TMDBUnavailableError:
        if cached is not None:
            return cached
        raise

    save_movie(db, parse_details(raw), now)
    db.commit()
    movie = _load(db, tmdb_id)
    assert movie is not None
    return movie


def save_movie(db: Session, parsed: ParsedMovie, now: datetime) -> int:
    """Upsert a parsed movie plus its people and providers. Caller commits. Returns movies.id."""
    if parsed.people:
        stmt = insert(Person).values([{"id": i, "name": n} for i, n in parsed.people.items()])
        db.execute(
            stmt.on_conflict_do_update(
                index_elements=[Person.id], set_={"name": stmt.excluded.name}
            )
        )

    if parsed.services:
        stmt = insert(StreamingService).values(
            [{"id": s.id, "name": s.name, "logo_path": s.logo_path} for s in parsed.services]
        )
        db.execute(
            stmt.on_conflict_do_update(
                index_elements=[StreamingService.id],
                set_={"name": stmt.excluded.name, "logo_path": stmt.excluded.logo_path},
            )
        )

    values = parsed.fields | {"metadata_fetched_at": now}
    stmt = insert(Movie).values(values)
    stmt = stmt.on_conflict_do_update(
        index_elements=[Movie.tmdb_id],
        set_={k: stmt.excluded[k] for k in values if k != "tmdb_id"},
    ).returning(Movie.id)
    movie_id = db.execute(stmt).scalar_one()

    # Replace (not merge) this region's providers, so services that dropped the movie disappear.
    db.execute(
        delete(MovieProvider).where(
            MovieProvider.movie_id == movie_id, MovieProvider.region == PROVIDER_REGION
        )
    )
    if parsed.services:
        rows = [
            {"movie_id": movie_id, "region": PROVIDER_REGION, "service_id": s.id, "fetched_at": now}
            for s in parsed.services
        ]
        db.execute(insert(MovieProvider).values(rows))
    return movie_id


def people_by_id(db: Session, ids: list[int]) -> dict[int, str]:
    if not ids:
        return {}
    return dict(db.execute(select(Person.id, Person.name).where(Person.id.in_(ids))).tuples().all())


def _load(db: Session, tmdb_id: int) -> Movie | None:
    # populate_existing: the upsert above bypasses the ORM, so refresh any object already in
    # this session's identity map instead of returning its pre-upsert state.
    return db.scalar(
        select(Movie)
        .where(Movie.tmdb_id == tmdb_id)
        .options(selectinload(Movie.providers))
        .execution_options(populate_existing=True)
    )
