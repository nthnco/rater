"""Response models: our API contract. The frontend never sees raw TMDB JSON."""

from datetime import date

from pydantic import BaseModel


class MovieSearchResult(BaseModel):
    tmdb_id: int
    title: str
    year: int | None
    poster_path: str | None


class PersonOut(BaseModel):
    id: int
    name: str


class ProviderOut(BaseModel):
    id: int
    name: str
    logo_path: str | None


class MovieDetail(BaseModel):
    tmdb_id: int
    title: str
    year: int | None
    release_date: date | None
    overview: str | None
    poster_path: str | None
    runtime_min: int | None
    genres: list[str]
    directors: list[PersonOut]
    top_cast: list[PersonOut]
    vote_average: float | None
    vote_count: int | None
    providers_region: str
    providers: list[ProviderOut]  # flat-rate (subscription); source: JustWatch via TMDB
