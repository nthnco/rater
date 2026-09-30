import copy
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from sqlalchemy import func, select, update

from app.models import Movie, MovieProvider, StreamingService

MATRIX = json.loads((Path(__file__).parent / "fixtures" / "tmdb_movie_603.json").read_text())


def serve(payload):
    return lambda request: httpx.Response(200, json=payload)


def test_first_view_fetches_from_tmdb_and_caches(api, db, fake_tmdb) -> None:
    calls = fake_tmdb(serve(MATRIX))

    response = api.get("/movies/603")

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "The Matrix"
    assert body["year"] == 1999
    assert [d["name"] for d in body["directors"]] == ["Lana Wachowski", "Lilly Wachowski"]
    assert [c["name"] for c in body["top_cast"]][:2] == ["Keanu Reeves", "Laurence Fishburne"]
    assert [p["name"] for p in body["providers"]] == ["Max", "Netflix"]
    assert body["providers_region"] == "US"
    assert len(calls) == 1

    movie = db.scalar(select(Movie).where(Movie.tmdb_id == 603))
    assert movie is not None and movie.metadata_fetched_at is not None


def test_second_view_is_served_from_db(api, db, fake_tmdb) -> None:
    calls = fake_tmdb(serve(MATRIX))

    first = api.get("/movies/603").json()
    second = api.get("/movies/603").json()

    assert second == first
    assert len(calls) == 1  # no second TMDB call


def test_stale_cache_is_refreshed(api, db, fake_tmdb) -> None:
    calls = fake_tmdb(serve(MATRIX))
    api.get("/movies/603")
    db.execute(
        update(Movie)
        .where(Movie.tmdb_id == 603)
        .values(metadata_fetched_at=datetime.now(UTC) - timedelta(days=8), title="Old Title")
    )

    assert api.get("/movies/603").json()["title"] == "The Matrix"
    assert len(calls) == 2
    assert db.scalar(select(func.count()).select_from(Movie)) == 1  # upserted, not duplicated


def test_refresh_replaces_providers(api, db, fake_tmdb) -> None:
    fake_tmdb(serve(MATRIX))
    api.get("/movies/603")
    db.execute(update(Movie).values(metadata_fetched_at=datetime.now(UTC) - timedelta(days=8)))

    left_netflix = copy.deepcopy(MATRIX)
    us = left_netflix["watch/providers"]["results"]["US"]
    us["flatrate"] = [p for p in us["flatrate"] if p["provider_name"] != "Netflix"]
    fake_tmdb(serve(left_netflix))

    assert [p["name"] for p in api.get("/movies/603").json()["providers"]] == ["Max"]
    assert db.scalar(select(func.count()).select_from(MovieProvider)) == 1
    assert db.get(StreamingService, 8) is not None  # the service itself stays known


def test_stale_copy_served_when_tmdb_is_down(api, db, fake_tmdb) -> None:
    fake_tmdb(serve(MATRIX))
    api.get("/movies/603")
    db.execute(update(Movie).values(metadata_fetched_at=datetime.now(UTC) - timedelta(days=8)))

    fake_tmdb(lambda request: httpx.Response(503))

    response = api.get("/movies/603")
    assert response.status_code == 200
    assert response.json()["title"] == "The Matrix"


def test_uncached_movie_with_tmdb_down_is_502(api, db, fake_tmdb) -> None:
    fake_tmdb(lambda request: httpx.Response(503))
    assert api.get("/movies/603").status_code == 502


def test_unknown_movie_is_404(api, db, fake_tmdb) -> None:
    fake_tmdb(lambda request: httpx.Response(404, json={"status_code": 34}))
    assert api.get("/movies/999999999").status_code == 404


def test_invalid_id_is_rejected(api, db, fake_tmdb) -> None:
    calls = fake_tmdb(serve(MATRIX))
    assert api.get("/movies/0").status_code == 422
    assert calls == []
