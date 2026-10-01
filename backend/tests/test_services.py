from app.services.streaming import SUPPORTED_SERVICE_IDS

NETFLIX, HULU, MAX = 8, 15, 1899


def login(api) -> None:
    api.post("/auth/signup", json={"email": "viewer@example.com", "password": "long enough pw"})


def ids(response) -> list[int]:
    return [s["id"] for s in response.json()]


# --- GET /services ---


def test_services_match_supported_ids_and_migration(api, db) -> None:
    # The seed migration and SUPPORTED_SERVICE_IDS must agree.
    services = api.get("/services").json()
    assert {s["id"] for s in services} == SUPPORTED_SERVICE_IDS


def test_services_sorted_by_name_with_logos(api, db) -> None:
    services = api.get("/services").json()
    names = [s["name"] for s in services]
    # Postgres sorts by its collation (case-insensitive, human order: "Amazon" before "AMC+"),
    # unlike Python's default code-point sort.
    assert names == sorted(names, key=str.casefold)
    assert all(s["logo_path"] for s in services)


def test_services_is_public(api, db) -> None:
    assert api.get("/services").status_code == 200  # no login


# --- GET/PUT /me/services ---


def test_my_services_require_login(api, db) -> None:
    assert api.get("/me/services").status_code == 401
    assert api.put("/me/services", json={"service_ids": [NETFLIX]}).status_code == 401


def test_new_user_has_no_services(api, db) -> None:
    login(api)
    assert api.get("/me/services").json() == []


def test_put_saves_and_get_returns_sorted(api, db) -> None:
    login(api)

    response = api.put("/me/services", json={"service_ids": [NETFLIX, MAX, HULU]})

    assert response.status_code == 200
    assert [s["name"] for s in response.json()] == ["HBO Max", "Hulu", "Netflix"]
    assert ids(api.get("/me/services")) == ids(response)


def test_put_replaces_rather_than_adds(api, db) -> None:
    login(api)
    api.put("/me/services", json={"service_ids": [NETFLIX, HULU]})

    api.put("/me/services", json={"service_ids": [MAX]})

    assert ids(api.get("/me/services")) == [MAX]


def test_duplicates_collapse(api, db) -> None:
    login(api)
    assert ids(api.put("/me/services", json={"service_ids": [NETFLIX, NETFLIX]})) == [NETFLIX]


def test_empty_list_clears(api, db) -> None:
    login(api)
    api.put("/me/services", json={"service_ids": [NETFLIX]})

    assert api.put("/me/services", json={"service_ids": []}).json() == []


def test_unsupported_id_is_rejected_and_nothing_changes(api, db) -> None:
    login(api)
    api.put("/me/services", json={"service_ids": [NETFLIX]})

    response = api.put("/me/services", json={"service_ids": [HULU, 2528]})  # 2528 = YouTube TV

    assert response.status_code == 422
    assert "2528" in response.json()["detail"]
    assert ids(api.get("/me/services")) == [NETFLIX]  # unchanged


def test_users_services_are_independent(api, db) -> None:
    login(api)
    api.put("/me/services", json={"service_ids": [NETFLIX]})
    api.post("/auth/logout")
    api.post("/auth/signup", json={"email": "other@example.com", "password": "long enough pw"})

    assert api.get("/me/services").json() == []
