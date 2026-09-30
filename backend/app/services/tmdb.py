"""Thin HTTP client for the TMDB API.

Knows URLs, auth, retries, and error mapping. Returns TMDB's raw JSON; turning it into our
own models happens in app.services.movies.
"""

import time
from collections.abc import Callable
from typing import Any

import httpx

from app.config import settings

BASE_URL = "https://api.themoviedb.org/3"
TIMEOUT_S = 10.0
MAX_RETRY_AFTER_S = 5.0


class TMDBError(Exception):
    """Base class for TMDB failures."""


class TMDBNotFoundError(TMDBError):
    """TMDB has no such resource (maps to our 404)."""


class TMDBUnavailableError(TMDBError):
    """TMDB is down, slow, rate-limiting us, or rejected our credentials (maps to our 502)."""


class TMDBClient:
    def __init__(
        self,
        read_token: str,
        http: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._http = http or httpx.Client(base_url=BASE_URL, timeout=TIMEOUT_S)
        self._headers = {"Authorization": f"Bearer {read_token}", "Accept": "application/json"}
        self._sleep = sleep

    def search(self, query: str) -> list[dict[str, Any]]:
        """First page of movie search results."""
        data = self._get("/search/movie", {"query": query, "include_adult": "false"})
        return data.get("results", [])

    def movie_details(self, tmdb_id: int) -> dict[str, Any]:
        """Details + credits + keywords + watch providers in a single request."""
        return self._get(
            f"/movie/{tmdb_id}",
            {"append_to_response": "credits,keywords,watch/providers"},
        )

    def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        # One retry on 429, honoring Retry-After (capped so a request never hangs for long).
        for attempt in range(2):
            try:
                response = self._http.get(path, params=params, headers=self._headers)
            except httpx.HTTPError as exc:
                raise TMDBUnavailableError(f"TMDB request failed: {exc}") from exc

            if response.status_code == 429 and attempt == 0:
                self._sleep(_retry_after_seconds(response))
                continue
            if response.status_code == 404:
                raise TMDBNotFoundError(path)
            if response.status_code != 200:
                raise TMDBUnavailableError(f"TMDB returned {response.status_code} for {path}")
            return response.json()

        raise TMDBUnavailableError(f"TMDB rate limit persisted for {path}")


def _retry_after_seconds(response: httpx.Response) -> float:
    try:
        return min(float(response.headers.get("Retry-After", "1")), MAX_RETRY_AFTER_S)
    except ValueError:
        return 1.0


_client: TMDBClient | None = None


def get_tmdb() -> TMDBClient:
    """FastAPI dependency. One shared client so connections are pooled across requests."""
    global _client
    if _client is None:
        _client = TMDBClient(settings.tmdb_read_token)
    return _client
