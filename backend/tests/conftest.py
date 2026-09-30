from collections.abc import Callable, Iterator

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.tmdb import BASE_URL, TMDBClient, get_tmdb

Handler = Callable[[httpx.Request], httpx.Response]


@pytest.fixture
def fake_tmdb() -> Iterator[Callable[[Handler], list[httpx.Request]]]:
    """Point the app at a scripted TMDB. Returns the list of requests it received."""

    def install(handler: Handler) -> list[httpx.Request]:
        calls: list[httpx.Request] = []

        def recording(request: httpx.Request) -> httpx.Response:
            calls.append(request)
            return handler(request)

        http = httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(recording))
        client = TMDBClient("test-token", http=http, sleep=lambda _: None)
        app.dependency_overrides[get_tmdb] = lambda: client
        return calls

    yield install
    app.dependency_overrides.pop(get_tmdb, None)


@pytest.fixture
def api() -> TestClient:
    return TestClient(app)
