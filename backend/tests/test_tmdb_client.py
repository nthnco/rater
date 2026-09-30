import httpx
import pytest

from app.services.tmdb import BASE_URL, TMDBClient, TMDBNotFoundError, TMDBUnavailableError


def make_client(handler, sleeps: list[float] | None = None) -> TMDBClient:
    http = httpx.Client(base_url=BASE_URL, transport=httpx.MockTransport(handler))
    sleeps = sleeps if sleeps is not None else []
    return TMDBClient("test-token", http=http, sleep=sleeps.append)


def test_search_sends_bearer_token_and_returns_results() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["auth"] = request.headers["Authorization"]
        seen["path"] = request.url.path
        seen["query"] = request.url.params["query"]
        return httpx.Response(200, json={"results": [{"id": 603, "title": "The Matrix"}]})

    results = make_client(handler).search("matrix")

    assert results == [{"id": 603, "title": "The Matrix"}]
    assert seen == {"auth": "Bearer test-token", "path": "/3/search/movie", "query": "matrix"}


def test_movie_details_requests_everything_in_one_call() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/3/movie/603"
        assert request.url.params["append_to_response"] == "credits,keywords,watch/providers"
        return httpx.Response(200, json={"id": 603})

    assert make_client(handler).movie_details(603) == {"id": 603}


def test_404_raises_not_found() -> None:
    client = make_client(lambda r: httpx.Response(404, json={"status_code": 34}))
    with pytest.raises(TMDBNotFoundError):
        client.movie_details(999999999)


@pytest.mark.parametrize("status", [401, 500, 503])
def test_other_errors_raise_unavailable(status: int) -> None:
    client = make_client(lambda r: httpx.Response(status))
    with pytest.raises(TMDBUnavailableError):
        client.search("x")


def test_network_error_raises_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("timed out", request=request)

    with pytest.raises(TMDBUnavailableError):
        make_client(handler).search("x")


def test_429_retries_once_honoring_retry_after() -> None:
    responses = iter([
        httpx.Response(429, headers={"Retry-After": "2"}),
        httpx.Response(200, json={"results": []}),
    ])
    sleeps: list[float] = []

    assert make_client(lambda r: next(responses), sleeps).search("x") == []
    assert sleeps == [2.0]


def test_retry_after_is_capped() -> None:
    responses = iter([
        httpx.Response(429, headers={"Retry-After": "600"}),
        httpx.Response(200, json={"results": []}),
    ])
    sleeps: list[float] = []

    make_client(lambda r: next(responses), sleeps).search("x")
    assert sleeps == [5.0]


def test_persistent_429_gives_up() -> None:
    client = make_client(lambda r: httpx.Response(429), sleeps=[])
    with pytest.raises(TMDBUnavailableError):
        client.search("x")
