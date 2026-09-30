"""Import every model here so Base.metadata sees them (Alembic autogenerate relies on it)."""

from app.models.movie import Movie, MovieProvider, Person, StreamingService

__all__ = ["Movie", "MovieProvider", "Person", "StreamingService"]
