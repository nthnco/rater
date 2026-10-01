from datetime import UTC, datetime, timedelta

import jwt

from app.services.security import (
    JWT_ALGORITHM,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

# --- passwords ---


def test_hash_is_not_the_password_and_uses_argon2id() -> None:
    hashed = hash_password("correct horse battery staple")
    assert "correct horse" not in hashed
    assert hashed.startswith("$argon2id$")


def test_verify_accepts_right_password_and_rejects_wrong_one() -> None:
    hashed = hash_password("hunter2!!")
    assert verify_password(hashed, "hunter2!!")
    assert not verify_password(hashed, "hunter3!!")


def test_same_password_hashes_differently_each_time() -> None:
    # A random salt per hash means identical passwords don't produce identical hashes.
    assert hash_password("same-password") != hash_password("same-password")


def test_corrupt_stored_hash_fails_closed() -> None:
    assert not verify_password("not-a-real-hash", "anything")


# --- tokens ---


def test_token_round_trips_user_id() -> None:
    assert decode_access_token(create_access_token(42)) == 42


def test_expired_token_is_rejected() -> None:
    issued = datetime.now(UTC) - timedelta(days=8)  # TTL is 7 days
    assert decode_access_token(create_access_token(42, now=issued)) is None


def test_token_signed_with_another_secret_is_rejected() -> None:
    forged = create_access_token(42, secret="an-attacker-chosen-secret-at-least-32-bytes")
    assert decode_access_token(forged) is None


def test_tampered_payload_is_rejected() -> None:
    header, _payload, signature = create_access_token(42).split(".")
    other_payload = create_access_token(43).split(".")[1]
    assert decode_access_token(f"{header}.{other_payload}.{signature}") is None


def test_unsigned_alg_none_token_is_rejected() -> None:
    unsigned = jwt.encode({"sub": "42", "exp": datetime.now(UTC) + timedelta(days=1)}, None,
                          algorithm="none")
    assert decode_access_token(unsigned) is None


def test_token_without_expiry_is_rejected() -> None:
    from app.config import settings

    no_exp = jwt.encode({"sub": "42"}, settings.jwt_secret, algorithm=JWT_ALGORITHM)
    assert decode_access_token(no_exp) is None


def test_garbage_is_rejected() -> None:
    assert decode_access_token("not.a.jwt") is None
    assert decode_access_token("") is None
