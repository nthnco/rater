import os
from collections.abc import Callable, Iterator
from pathlib import Path

from sqlalchemy.engine import make_url

# Point the app at a dedicated test database *before* app modules read settings.
_base_url = make_url(
    os.environ.get("DATABASE_URL", "postgresql+psycopg://rater:rater@localhost:5432/rater")
)
TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", _base_url.set(database="rater_test").render_as_string(hide_password=False)
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import httpx  # noqa: E402
import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db import engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.services.tmdb import BASE_URL, TMDBClient, get_tmdb  # noqa: E402

Handler = Callable[[httpx.Request], httpx.Response]
BACKEND_DIR = Path(__file__).resolve().parents[1]


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


@pytest.fixture(scope="session")
def migrated_db() -> None:
    """Create the test database if needed and run all migrations once per test run."""
    url = make_url(TEST_DATABASE_URL)
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": url.database}
        )
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    admin.dispose()

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(config, "head")


@pytest.fixture
def db(migrated_db: None) -> Iterator[Session]:
    """A session whose work is rolled back after the test, even if the code calls commit().

    The outer transaction is never committed; the session's commits only release savepoints.
    """
    with engine.connect() as conn:
        outer = conn.begin()
        session = Session(
            bind=conn, join_transaction_mode="create_savepoint", expire_on_commit=False
        )
        app.dependency_overrides[get_db] = lambda: session
        try:
            yield session
        finally:
            app.dependency_overrides.pop(get_db, None)
            session.close()
            outer.rollback()
