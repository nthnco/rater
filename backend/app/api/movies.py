from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.api.schemas import MovieDetail, MovieSearchResult, PersonOut, ProviderOut
from app.db import get_db
from app.models import Movie
from app.services import movies as movie_service
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


@router.get("/{tmdb_id}", response_model=MovieDetail)
def get_movie(
    tmdb_id: Annotated[int, Path(gt=0)],
    db: Annotated[Session, Depends(get_db)],
    tmdb: Annotated[TMDBClient, Depends(get_tmdb)],
) -> MovieDetail:
    """Movie details plus streaming providers, cached in our DB after the first view."""
    movie = movie_service.get_movie(db, tmdb, tmdb_id)
    return _to_detail(db, movie)


def _to_detail(db: Session, movie: Movie) -> MovieDetail:
    directors = movie.directors or []
    top_cast = movie.top_cast or []
    names = movie_service.people_by_id(db, directors + top_cast)
    providers = [
        p.service for p in movie.providers if p.region == movie_service.PROVIDER_REGION
    ]
    return MovieDetail(
        tmdb_id=movie.tmdb_id,
        title=movie.title,
        year=movie.release_date.year if movie.release_date else None,
        release_date=movie.release_date,
        overview=movie.overview,
        poster_path=movie.poster_path,
        runtime_min=movie.runtime_min,
        genres=movie.genres or [],
        directors=[PersonOut(id=i, name=names[i]) for i in directors if i in names],
        top_cast=[PersonOut(id=i, name=names[i]) for i in top_cast if i in names],
        vote_average=movie.tmdb_vote_average,
        vote_count=movie.tmdb_vote_count,
        providers_region=movie_service.PROVIDER_REGION,
        providers=[
            ProviderOut(id=s.id, name=s.name, logo_path=s.logo_path)
            for s in sorted(providers, key=lambda s: s.name)
        ],
    )
