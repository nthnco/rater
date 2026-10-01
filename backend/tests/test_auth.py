from sqlalchemy import delete, select

from app.api.deps import ACCESS_COOKIE
from app.models import User

EMAIL = "Nathan@Example.com"
PASSWORD = "correct horse battery"


def signup(api, email=EMAIL, password=PASSWORD):
    return api.post("/auth/signup", json={"email": email, "password": password})


# --- signup ---


def test_signup_creates_user_and_logs_in(api, db) -> None:
    response = signup(api)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "nathan@example.com"  # lowercased
    assert body["region"] == "US"  # DB default
    assert "password_hash" not in body
    assert api.get("/me").json()["id"] == body["id"]  # the cookie works


def test_signup_cookie_flags(api, db) -> None:
    cookie = signup(api).headers["set-cookie"]
    assert cookie.startswith(f"{ACCESS_COOKIE}=")
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert "Path=/" in cookie


def test_password_is_stored_hashed(api, db) -> None:
    signup(api)
    stored = db.scalar(select(User.password_hash).where(User.email == "nathan@example.com"))
    assert stored.startswith("$argon2id$")
    assert PASSWORD not in stored


def test_duplicate_email_is_409_case_insensitive(api, db) -> None:
    signup(api)
    assert signup(api, email="nathan@EXAMPLE.com").status_code == 409


def test_signup_validation(api, db) -> None:
    assert signup(api, password="short").status_code == 422
    assert signup(api, password="x" * 129).status_code == 422
    assert signup(api, email="not-an-email").status_code == 422


# --- login ---


def test_login_with_correct_password(api, db) -> None:
    signup(api)
    api.cookies.clear()

    response = api.post("/auth/login", json={"email": "NATHAN@example.com", "password": PASSWORD})

    assert response.status_code == 200
    assert ACCESS_COOKIE in response.cookies
    assert api.get("/me").status_code == 200


def test_wrong_password_and_unknown_email_look_identical(api, db) -> None:
    signup(api)
    api.cookies.clear()

    wrong_pw = api.post("/auth/login", json={"email": EMAIL, "password": "wrong password"})
    no_user = api.post("/auth/login", json={"email": "nobody@example.com", "password": PASSWORD})

    assert wrong_pw.status_code == no_user.status_code == 401
    assert wrong_pw.json() == no_user.json() == {"detail": "Invalid email or password"}
    assert ACCESS_COOKIE not in wrong_pw.cookies


# --- /me and logout ---


def test_me_requires_login(api, db) -> None:
    assert api.get("/me").status_code == 401


def test_me_rejects_tampered_cookie(api, db) -> None:
    signup(api)
    token = api.cookies[ACCESS_COOKIE]
    api.cookies.set(ACCESS_COOKIE, token[:-2] + ("AA" if not token.endswith("AA") else "BB"))
    assert api.get("/me").status_code == 401


def test_logout_clears_cookie(api, db) -> None:
    signup(api)

    response = api.post("/auth/logout")

    assert response.status_code == 204
    assert api.get("/me").status_code == 401


def test_token_for_deleted_user_is_rejected(api, db) -> None:
    signup(api)
    db.execute(delete(User))
    assert api.get("/me").status_code == 401
