"""
Thin convenience wrapper around Supabase Auth.

In production the React frontend should talk to Supabase Auth directly
using the Supabase JS client (this is the standard, recommended
pattern - it handles refresh tokens, session storage, etc. far better
than proxying through our own backend). These endpoints exist mainly so
the backend can be exercised and demoed end-to-end (register -> login ->
call protected endpoints) without also standing up the frontend first.

`/register` and `/login` use the ANON key client, matching what a public
signup/login form would use. `/guest` is different on purpose - see its
docstring below.
"""
import secrets
import string

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.core.dependencies import CurrentUser, get_current_user
from app.database.supabase import get_anon_client, get_service_client
from fastapi import Depends

router = APIRouter(prefix="/auth", tags=["Auth"])

# Well-known guest account identifier - not a secret (just like any
# other account's email address). A SINGLE guest account is reused
# across every "Continue as Guest" click rather than creating a new
# Supabase user each time; see guest_session() below for why.
GUEST_EMAIL = "guest@stockpilot.demo"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    business_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    user_id: str
    email: str


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(payload: RegisterRequest):
    client = get_anon_client()
    try:
        result = client.auth.sign_up(
            {"email": payload.email, "password": payload.password}
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Registration failed: {exc}")

    if not result.user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registration failed.")

    # Create the profile row using the service client (bypasses RLS,
    # since the user's own session may still need email confirmation
    # before it can write under its own RLS policy).
    service_client = get_service_client()
    service_client.table("profiles").upsert(
        {
            "id": result.user.id,
            "email": payload.email,
            "business_name": payload.business_name,
        }
    ).execute()

    session = result.session
    return AuthResponse(
        access_token=session.access_token if session else "",
        refresh_token=session.refresh_token if session else None,
        user_id=result.user.id,
        email=payload.email,
    )


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest):
    client = get_anon_client()
    try:
        result = client.auth.sign_in_with_password(
            {"email": payload.email, "password": payload.password}
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Login failed: {exc}")

    if not result.session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    return AuthResponse(
        access_token=result.session.access_token,
        refresh_token=result.session.refresh_token,
        user_id=result.user.id,
        email=payload.email,
    )


@router.post("/guest", response_model=AuthResponse, status_code=201)
def guest_session():
    """
    Dedicated "Continue as Guest" endpoint for hackathon/demo testing.

    This intentionally does NOT call `client.auth.sign_up` (the path
    `/register` uses). Supabase's public sign-up flow sends a
    confirmation email and is subject to an aggressive per-project email
    rate limit - fine for real users signing up occasionally, but a
    guest button that a judge might click several times in a demo would
    quickly trip "email rate limit exceeded" and break the feature.

    It also reuses a SINGLE well-known guest account across every guest
    session, rather than provisioning a brand new Supabase user on each
    click. A well-known email (not a secret - just an identifier, like
    any other account's email) is looked up in `profiles`; if it already
    exists we reuse that same user id, otherwise we create it once via
    the Supabase Auth **admin** API (`auth.admin`, service-role only,
    `email_confirm=True`) - never through the rate-limited public
    sign-up flow. Either way, a fresh random password is generated for
    THIS request only, set via the admin API, and immediately used to
    sign in - the password is never stored, logged, or reused, so
    nothing here hardcodes a secret; it just avoids proliferating guest
    accounts in `auth.users` on every click.

    The resulting session is a completely ordinary Supabase Auth
    session: real row in `auth.users`, real `profiles` row, and a real
    access/refresh token pair issued by Supabase Auth itself. It is
    subject to exactly the same JWT verification and RLS policies as any
    other account (see supabase_schema.sql). Because it is one shared
    account, its data (seeded via the existing `/demo/seed` endpoint) is
    demo/sample data only and is naturally isolated from every real
    user's data by the same RLS + user-id filtering that isolates any
    two accounts from each other - it never grants access to anyone
    else's rows.
    """
    service_client = get_service_client()

    try:
        existing = (
            service_client.table("profiles")
            .select("id")
            .eq("email", GUEST_EMAIL)
            .limit(1)
            .execute()
        )
        existing_rows = existing.data or []
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Could not start guest session: {exc}")

    new_password = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24))

    if existing_rows:
        user_id = existing_rows[0]["id"]
        try:
            service_client.auth.admin.update_user_by_id(user_id, {"password": new_password})
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Could not start guest session: {exc}"
            )
    else:
        try:
            admin_result = service_client.auth.admin.create_user(
                {
                    "email": GUEST_EMAIL,
                    "password": new_password,
                    "email_confirm": True,
                    "user_metadata": {"guest": True},
                }
            )
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Could not start guest session: {exc}"
            )

        if not admin_result.user:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Could not start guest session.")

        user_id = admin_result.user.id
        try:
            service_client.table("profiles").upsert(
                {
                    "id": user_id,
                    "email": GUEST_EMAIL,
                    "business_name": "Guest Demo Store",
                }
            ).execute()
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Could not start guest session: {exc}"
            )

    # Sign in with the freshly-set password to obtain a real session.
    # Password sign-in is not subject to the sign-up email rate limit.
    anon_client = get_anon_client()
    try:
        result = anon_client.auth.sign_in_with_password({"email": GUEST_EMAIL, "password": new_password})
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Could not start guest session: {exc}")

    if not result.session:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Could not start guest session.")

    return AuthResponse(
        access_token=result.session.access_token,
        refresh_token=result.session.refresh_token,
        user_id=user_id,
        email=GUEST_EMAIL,
    )


@router.get("/me")
def me(user: CurrentUser = Depends(get_current_user)):
    return {"user_id": user.id, "email": user.email}