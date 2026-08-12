"""
JWT verification for Supabase-issued access tokens.

Supabase Auth issues a JWT whenever a user logs in. The signing
algorithm depends on the project's configuration:

- Legacy projects sign with a shared secret using HS256
  (`SUPABASE_JWT_SECRET`, from Dashboard -> Project Settings -> API ->
  JWT Settings).
- Newer projects use asymmetric "JWT Signing Keys" (ES256 by default,
  RS256 is also possible) and publish the corresponding public keys at
  `{SUPABASE_URL}/auth/v1/.well-known/jwks.json`. There is no shared
  secret to configure for these - the backend verifies signatures using
  Supabase's own published public key instead.

Both normal login/signup and the guest session endpoint go through
Supabase Auth, so both issue tokens signed the same way by the same
project - this module has to correctly handle whichever algorithm THIS
project is actually configured for, rather than assuming HS256.

The React frontend sends the resulting token as:

    Authorization: Bearer <token>

This module verifies the token's signature/expiry/audience and extracts
the Supabase user id (the JWT's `sub` claim), which is also the primary
key of `auth.users` / `profiles`.
"""
import ssl
from functools import lru_cache
from typing import Optional

import certifi
import jwt
from jwt import InvalidTokenError, PyJWKClient

from app.core.config import get_settings

settings = get_settings()

# Algorithms this backend will ever accept, matched by branch below - an
# explicit allow-list per branch, never a wildcard, and never used to
# verify a token with the "wrong kind" of key (an HS256-headed token is
# only ever checked against our own shared secret; an ES256/RS256-headed
# token is only ever checked against a key Supabase itself published).
_SYMMETRIC_ALGORITHMS = ["HS256"]
_ASYMMETRIC_ALGORITHMS = ["ES256", "RS256"]


class TokenPayload:
    def __init__(self, user_id: str, email: Optional[str], raw: dict):
        self.user_id = user_id
        self.email = email
        self.raw = raw


class InvalidTokenException(Exception):
    pass


@lru_cache
def _jwks_client() -> PyJWKClient:
    """
    Cached client for Supabase's published JWKS (public signing keys for
    ES256/RS256-configured projects).

    Builds its SSL context from BOTH the system's default trust store
    AND `certifi`'s CA bundle (additively - `load_verify_locations` adds
    trust anchors, it does not replace the ones `create_default_context`
    already loaded). This fixes "CERTIFICATE_VERIFY_FAILED: unable to
    get local issuer certificate" in environments whose system trust
    store is missing or incomplete (common in minimal Docker images
    that don't ship the OS `ca-certificates` package) by supplying
    `certifi`'s complete, self-contained Mozilla CA bundle as a
    fallback - while still fully respecting any additional/private CAs
    a given system's own store may already have configured. This is NOT
    a security downgrade: certificate chain and hostname verification
    are still fully performed, just against a strictly larger, still
    fully-legitimate set of trusted certificate authorities.

    PyJWKClient also caches the fetched key set in-memory (5 minute
    default lifespan) so this does not fetch the JWKS on every request.
    """
    jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
    ssl_context = ssl.create_default_context()
    ssl_context.load_verify_locations(cafile=certifi.where())
    return PyJWKClient(jwks_url, cache_jwk_set=True, ssl_context=ssl_context)


def decode_supabase_jwt(token: str) -> TokenPayload:
    """
    Decode and validate a Supabase Auth JWT, auto-detecting whether this
    project signs with a shared secret (HS256) or a published public key
    (ES256/RS256) and verifying accordingly. Signature and audience
    validation are enforced on every path; nothing here weakens either
    check versus the previous HS256-only implementation - it only adds
    support for the algorithm(s) this project may actually use.

    Raises InvalidTokenException on any failure (expired, bad signature,
    unsupported/unrecognized algorithm, malformed, missing subject).
    """
    try:
        header = jwt.get_unverified_header(token)
    except InvalidTokenError as exc:
        raise InvalidTokenException(f"Invalid or expired token: {exc}") from exc

    alg = header.get("alg")

    if alg in _SYMMETRIC_ALGORITHMS:
        if not settings.SUPABASE_JWT_SECRET:
            raise InvalidTokenException(
                "Server is missing SUPABASE_JWT_SECRET configuration for an HS256-signed token."
            )
        try:
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=_SYMMETRIC_ALGORITHMS,
                audience="authenticated",
                options={"verify_aud": True},
            )
        except InvalidTokenError as exc:
            raise InvalidTokenException(f"Invalid or expired token: {exc}") from exc

    elif alg in _ASYMMETRIC_ALGORITHMS:
        if not settings.SUPABASE_URL:
            raise InvalidTokenException(
                "Server is missing SUPABASE_URL configuration needed to verify this token."
            )
        try:
            signing_key = _jwks_client().get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=_ASYMMETRIC_ALGORITHMS,
                audience="authenticated",
                options={"verify_aud": True},
            )
        except InvalidTokenError as exc:
            raise InvalidTokenException(f"Invalid or expired token: {exc}") from exc
        except InvalidTokenException:
            raise
        except Exception as exc:
            # PyJWKClient network/lookup failures (unreachable JWKS
            # endpoint, unknown `kid`, etc.) - never leak internals.
            raise InvalidTokenException(f"Could not verify token signature: {exc}") from exc

    else:
        raise InvalidTokenException(f"Unsupported token signing algorithm: {alg!r}")

    user_id = payload.get("sub")
    if not user_id:
        raise InvalidTokenException("Token missing 'sub' (user id) claim.")

    email = payload.get("email")
    return TokenPayload(user_id=user_id, email=email, raw=payload)