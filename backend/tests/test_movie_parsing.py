import copy
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from app.services.movies import CACHE_TTL, is_fresh, parse_details

MATRIX = json.loads((Path(__file__).parent / "fixtures" / "tmdb_movie_603.json").read_text())


def test_parses_core_fields() -> None:
    f = parse_details(MATRIX).fields
    assert f["tmdb_id"] == 603
    assert f["title"] == "The Matrix"
    assert f["release_date"] == date(1999, 3, 30)
    assert f["runtime_min"] == 136
    assert f["genres"] == ["Action", "Science Fiction"]
    assert f["keywords"] == [310, 4565, 2964]
    assert f["tmdb_vote_count"] == 26000


def test_directors_are_deduplicated_and_exclude_other_crew() -> None:
    parsed = parse_details(MATRIX)
    assert parsed.fields["directors"] == [9340, 9339]
    assert 1091 not in parsed.people  # producer isn't stored


def test_top_cast_is_first_five_by_billing_order() -> None:
    parsed = parse_details(MATRIX)
    assert parsed.fields["top_cast"] == [6384, 2975, 530, 1331, 532]
    assert 9372 not in parsed.people  # 6th-billed isn't stored
    assert parsed.people[6384] == "Keanu Reeves"


def test_providers_are_us_flatrate_only() -> None:
    services = parse_details(MATRIX).services
    assert {s.name for s in services} == {"Max", "Netflix"}  # no rent, no GB


def test_unknown_values_become_none() -> None:
    raw = copy.deepcopy(MATRIX) | {"release_date": "", "runtime": 0, "overview": ""}
    f = parse_details(raw).fields
    assert f["release_date"] is None
    assert f["runtime_min"] is None
    assert f["overview"] is None


def test_missing_optional_sections() -> None:
    parsed = parse_details({"id": 1, "title": "Bare"})
    assert parsed.fields["directors"] == []
    assert parsed.fields["genres"] == []
    assert parsed.services == []
    assert parsed.people == {}


def test_freshness_window() -> None:
    now = datetime(2026, 9, 30, tzinfo=UTC)
    assert is_fresh(now - timedelta(days=1), now)
    assert not is_fresh(now - CACHE_TTL, now)
    assert not is_fresh(None, now)
