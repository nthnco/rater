import httpx


def test_search_maps_tmdb_results(api, fake_tmdb) -> None:
    fake_tmdb(lambda r: httpx.Response(200, json={"results": [
        {"id": 603, "title": "The Matrix", "release_date": "1999-03-30", "poster_path": "/m.jpg"},
        {"id": 1, "title": "Unreleased", "release_date": "", "poster_path": None},
    ]}))

    response = api.get("/movies/search", params={"q": "  matrix "})

    assert response.status_code == 200
    assert response.json() == [
        {"tmdb_id": 603, "title": "The Matrix", "year": 1999, "poster_path": "/m.jpg"},
        {"tmdb_id": 1, "title": "Unreleased", "year": None, "poster_path": None},
    ]


def test_search_strips_query_before_calling_tmdb(api, fake_tmdb) -> None:
    calls = fake_tmdb(lambda r: httpx.Response(200, json={"results": []}))
    api.get("/movies/search", params={"q": "  matrix "})
    assert calls[0].url.params["query"] == "matrix"


def test_empty_query_is_rejected_without_calling_tmdb(api, fake_tmdb) -> None:
    calls = fake_tmdb(lambda r: httpx.Response(200, json={"results": []}))
    assert api.get("/movies/search", params={"q": ""}).status_code == 422
    assert calls == []


def test_whitespace_query_returns_empty_without_calling_tmdb(api, fake_tmdb) -> None:
    calls = fake_tmdb(lambda r: httpx.Response(200, json={"results": []}))
    assert api.get("/movies/search", params={"q": "   "}).json() == []
    assert calls == []


def test_tmdb_outage_returns_502(api, fake_tmdb) -> None:
    fake_tmdb(lambda r: httpx.Response(503))
    assert api.get("/movies/search", params={"q": "x"}).status_code == 502
