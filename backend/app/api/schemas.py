"""Response models: our API contract. The frontend never sees raw TMDB JSON."""

from pydantic import BaseModel


class MovieSearchResult(BaseModel):
    tmdb_id: int
    title: str
    year: int | None
    poster_path: str | None
