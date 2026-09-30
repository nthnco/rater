"""Movie metadata: parse TMDB details into the data we store (DESIGN.md §4, §6)."""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

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

