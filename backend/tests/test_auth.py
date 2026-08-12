from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from app.core import security
from app.core.security import InvalidTokenException, decode_supabase_jwt


def make_token(secret, sub="user-123", email="test@example.com", exp_delta_seconds=3600, aud="authenticated"):
    payload = {
        "sub": sub,
        "email": email,
        "aud": aud,
        "exp": datetime.now(timezone.utc) + timedelta(seconds=exp_delta_seconds),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def test_valid_token_decodes(jwt_secret):
    token = make_token(jwt_secret)
    result = decode_supabase_jwt(token)
    assert result.user_id == "user-123"
    assert result.email == "test@example.com"


def test_expired_token_rejected(jwt_secret):
    token = make_token(jwt_secret, exp_delta_seconds=-10)
    with pytest.raises(InvalidTokenException):
        decode_supabase_jwt(token)


def test_wrong_signature_rejected(jwt_secret):
    token = make_token("a-completely-different-secret")
    with pytest.raises(InvalidTokenException):
        decode_supabase_jwt(token)


def test_missing_subject_rejected(jwt_secret):
    payload = {
        "aud": "authenticated",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    token = jwt.encode(payload, jwt_secret, algorithm="HS256")
    with pytest.raises(InvalidTokenException):
        decode_supabase_jwt(token)


def test_wrong_audience_rejected(jwt_secret):
    token = make_token(jwt_secret, aud="not-authenticated")
    with pytest.raises(InvalidTokenException):
        decode_supabase_jwt(token)


def test_get_current_user_dependency_rejects_missing_token():
    from app.core.dependencies import get_current_user

    with pytest.raises(Exception):
        get_current_user(credentials=None)


# --------------------------------------------------------------------------
# ES256 (asymmetric "JWT Signing Keys") coverage.
#
# Modern Supabase projects sign access tokens with an asymmetric key
# (ES256 by default) and publish the public key via a JWKS endpoint,
# instead of a shared HS256 secret. This is the exact scenario that
# previously failed with "The specified alg value is not allowed" - the
# verifier only accepted algorithms=["HS256"]. These tests simulate that
# configuration end-to-end (real ES256 signing, real signature
# verification) without a network call, by substituting a fake JWKS
# client that resolves to a known key pair.
# --------------------------------------------------------------------------


def _make_ec_keypair():
    private_key = ec.generate_private_key(ec.SECP256R1())
    return private_key, private_key.public_key()


def make_es256_token(private_key, sub="guest-user-1", email="guest@stockpilot-guest.demo", exp_delta_seconds=3600):
    payload = {
        "sub": sub,
        "email": email,
        "aud": "authenticated",
        "exp": datetime.now(timezone.utc) + timedelta(seconds=exp_delta_seconds),
    }
    return jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": "test-key-1"})


class _FakeSigningKey:
    def __init__(self, key):
        self.key = key


class _FakeJWKSClient:
    def __init__(self, public_key):
        self._public_key = public_key

    def get_signing_key_from_jwt(self, token):
        return _FakeSigningKey(self._public_key)


def test_es256_token_decodes_via_jwks(monkeypatch):
    private_key, public_key = _make_ec_keypair()
    token = make_es256_token(private_key)

    monkeypatch.setattr(security, "_jwks_client", lambda: _FakeJWKSClient(public_key))

    result = decode_supabase_jwt(token)
    assert result.user_id == "guest-user-1"
    assert result.email == "guest@stockpilot-guest.demo"


def test_es256_token_signed_by_wrong_key_rejected(monkeypatch):
    private_key, _ = _make_ec_keypair()
    _, unrelated_public_key = _make_ec_keypair()
    token = make_es256_token(private_key)

    # Simulates a token whose signature doesn't match the key Supabase
    # actually published - must still be rejected, not silently accepted.
    monkeypatch.setattr(security, "_jwks_client", lambda: _FakeJWKSClient(unrelated_public_key))

    with pytest.raises(InvalidTokenException):
        decode_supabase_jwt(token)


def test_es256_expired_token_rejected(monkeypatch):
    private_key, public_key = _make_ec_keypair()
    token = make_es256_token(private_key, exp_delta_seconds=-10)

    monkeypatch.setattr(security, "_jwks_client", lambda: _FakeJWKSClient(public_key))

    with pytest.raises(InvalidTokenException):
        decode_supabase_jwt(token)


def test_es256_wrong_audience_rejected(monkeypatch):
    private_key, public_key = _make_ec_keypair()
    payload = {
        "sub": "guest-user-1",
        "aud": "not-authenticated",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    token = jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": "test-key-1"})

    monkeypatch.setattr(security, "_jwks_client", lambda: _FakeJWKSClient(public_key))

    with pytest.raises(InvalidTokenException):
        decode_supabase_jwt(token)


def test_unrecognized_algorithm_rejected_outright():
    # A token whose header claims an algorithm we never opt into (e.g. a
    # forged "none"-alg token, the classic JWT downgrade attack) must be
    # rejected before any key lookup - never treated as a wildcard match.
    header = jwt.utils.base64url_encode(b'{"alg":"none","typ":"JWT"}').decode()
    payload = jwt.utils.base64url_encode(
        b'{"sub":"attacker","aud":"authenticated","exp":9999999999}'
    ).decode()
    forged_token = f"{header}.{payload}."

    with pytest.raises(InvalidTokenException):
        decode_supabase_jwt(forged_token)


def test_es256_token_rejected_without_supabase_url(monkeypatch):
    private_key, public_key = _make_ec_keypair()
    token = make_es256_token(private_key)

    monkeypatch.setattr(security, "_jwks_client", lambda: _FakeJWKSClient(public_key))
    monkeypatch.setattr(security.settings, "SUPABASE_URL", "")

    with pytest.raises(InvalidTokenException):
        decode_supabase_jwt(token)