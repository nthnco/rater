from datetime import date, datetime

from sqlalchemy import CHAR, REAL, BigInteger, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Movie(Base):
    """Cached TMDB metadata for movies users have actually touched (DESIGN.md §4, §6)."""

    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tmdb_id: Mapped[int] = mapped_column(Integer, unique=True)
    title: Mapped[str] = mapped_column(Text)
    release_date: Mapped[date | None]
    overview: Mapped[str | None] = mapped_column(Text)
    poster_path: Mapped[str | None] = mapped_column(Text)
    runtime_min: Mapped[int | None] = mapped_column(Integer)
    genres: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    directors: Mapped[list[int] | None] = mapped_column(ARRAY(Integer))  # people.id
    top_cast: Mapped[list[int] | None] = mapped_column(ARRAY(Integer))  # people.id, billing order
    keywords: Mapped[list[int] | None] = mapped_column(ARRAY(Integer))  # TMDB keyword ids
    tmdb_popularity: Mapped[float | None] = mapped_column(REAL)
    tmdb_vote_average: Mapped[float | None] = mapped_column(REAL)
    tmdb_vote_count: Mapped[int | None] = mapped_column(Integer)
    metadata_fetched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    providers: Mapped[list["MovieProvider"]] = relationship(
        back_populates="movie", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_movies_release_date", "release_date"),)


class Person(Base):
    """TMDB person id -> name, so directors/top_cast can be displayed (deviation from §6)."""

    __tablename__ = "people"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # TMDB person id
    name: Mapped[str] = mapped_column(Text)


class StreamingService(Base):
    __tablename__ = "streaming_services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # TMDB provider_id
    name: Mapped[str] = mapped_column(Text)
    logo_path: Mapped[str | None] = mapped_column(Text)


class MovieProvider(Base):
    """Which services carry a movie, per region. Flat-rate (subscription) only in v1."""

    __tablename__ = "movie_providers"

    movie_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("movies.id", ondelete="CASCADE"), primary_key=True
    )
    region: Mapped[str] = mapped_column(CHAR(2), primary_key=True)
    service_id: Mapped[int] = mapped_column(ForeignKey("streaming_services.id"), primary_key=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    movie: Mapped[Movie] = relationship(back_populates="providers")
    service: Mapped[StreamingService] = relationship(lazy="joined")
