from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.api.schemas import MovieSearchResult
from app.services.tmdb import TMDBClient, get_tmdb

router = APIRouter(prefix="/movies", tags=["movies"])


@router.get("/search", response_model=list[MovieSearchResult])
def search_movies(
    q: Annotated[str, Query(min_length=1, max_length=200)],
    tmdb: Annotated[TMDBClient, Depends(get_tmdb)],
) -> list[MovieSearchResult]:
    """Proxy to TMDB search. Not cached in our DB: results are ephemeral (DESIGN.md §4)."""
    query = q.strip()
    if not query:
        return []
    return [_to_search_result(r) for r in tmdb.search(query)]


def _to_search_result(raw: dict[str, Any]) -> MovieSearchResult:
    release = raw.get("release_date") or ""  # TMDB sends "" when unknown
    return MovieSearchResult(
        tmdb_id=raw["id"],
        title=raw.get("title") or raw.get("original_title") or "Untitled",
        year=int(release[:4]) if release[:4].isdigit() else None,
        poster_path=raw.get("poster_path"),
    )
