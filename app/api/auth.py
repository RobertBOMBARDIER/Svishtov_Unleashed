"""
Authentication endpoints.

Routes
------
POST   /auth/register        — create a new account
POST   /auth/login           — authenticate and receive a JWT
POST   /auth/logout          — invalidate the current session (client-side)
POST   /auth/password-reset  — request a password-reset email
DELETE /auth/account         — permanently delete account + all user photos

Security notes
--------------
- Wrong-credential errors always return the same generic message so that
  neither the existence of an email address nor which field is wrong is
  revealed (Requirement 10.6 / Property 16).
- Passwords are hashed with bcrypt via ``app.core.security``.
- JWTs are HS256-signed with a configurable expiry (``ACCESS_TOKEN_EXPIRE_MINUTES``).
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.dependencies import get_current_user, get_db
from app.models.photo import Photo
from app.models.user import User
from app.schemas.auth import AuthRequest, AuthResponse, PasswordResetRequest, RegisterRequest

router = APIRouter(prefix="/auth", tags=["auth"])

# ── Generic error message (Requirement 10.6) ──────────────────────────────────
_WRONG_CREDENTIALS_MSG = "Email sau parolă incorectă"


# ── POST /auth/register ───────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Înregistrare cont nou",
)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    Create a new user account.

    - Email must be unique (HTTP 409 if already taken).
    - Password is hashed with bcrypt before storage.
    - On success the user is automatically authenticated: a JWT is returned
      so the client does not need a separate login call (Requirement 10.2).
    """
    # Check for duplicate email (Requirement 10.3)
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Adresa de email este deja utilizată.",
        )

    user = User(
        id=str(uuid.uuid4()),
        email=body.email,
        hashed_password=hash_password(body.password),
        is_active=True,
    )
    db.add(user)
    await db.flush()  # populate user.id before creating the token

    token = create_access_token(subject=user.id)
    return AuthResponse(token=token, user_id=user.id)


# ── POST /auth/login ──────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Autentificare",
)
async def login(
    body: AuthRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    Authenticate with email + password and receive a JWT.

    The error message is intentionally generic regardless of whether the
    email does not exist or the password is wrong (Requirement 10.6).
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user: User | None = result.scalar_one_or_none()

    # Constant-time path: always call verify_password to prevent timing attacks
    # even when the user does not exist.
    dummy_hash = "$2b$12$invalidhashfortimingprotection000000000000000000000000"
    stored_hash = user.hashed_password if user is not None else dummy_hash

    password_ok = verify_password(body.password, stored_hash)

    if user is None or not user.is_active or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=_WRONG_CREDENTIALS_MSG,
        )

    token = create_access_token(subject=user.id)
    return AuthResponse(token=token, user_id=user.id)


# ── POST /auth/logout ─────────────────────────────────────────────────────────

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deconectare",
)
async def logout(
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Invalidate the current session.

    JWT tokens are stateless; true server-side invalidation would require a
    token blocklist (Redis / DB table).  For this MVP the endpoint validates
    the token (ensuring the caller is authenticated) and returns 204 — the
    client is responsible for discarding the token locally (Requirement 10.9).
    """
    # No server-side state to clear in this MVP implementation.
    # The client must delete the stored token.
    return None


# ── POST /auth/password-reset ─────────────────────────────────────────────────

@router.post(
    "/password-reset",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Solicitare resetare parolă",
)
async def password_reset(
    body: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Request a password-reset email.

    Always returns 202 regardless of whether the email exists in the database,
    to avoid leaking account existence information (Requirement 10.11).

    In a production deployment this endpoint would enqueue an email via an
    SMTP service or a transactional email provider (SendGrid, Mailgun, etc.).
    For this MVP the endpoint acknowledges the request without sending email.
    """
    # Intentionally do NOT reveal whether the email exists.
    # A production implementation would enqueue an email here.
    _ = await db.execute(select(User).where(User.email == body.email))
    # Result intentionally ignored — same response either way.

    return {"detail": "Dacă adresa de email există, vei primi un email de resetare."}


# ── DELETE /auth/account ──────────────────────────────────────────────────────

@router.delete(
    "/account",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Ștergere cont și toate fotografiile",
)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Permanently delete the authenticated user's account and all their photos.

    The ``User`` model has ``cascade="all, delete-orphan"`` on the ``photos``
    relationship, so deleting the user row also removes all associated
    ``Photo`` rows from the database (Requirement 12.5).

    Note: physical photo files on the Railway Volume / Cloudflare R2 are NOT
    deleted here — a background cleanup job should handle orphaned files.
    That concern is outside the scope of this endpoint.
    """
    # Re-fetch the user within this session to ensure it is attached.
    result = await db.execute(select(User).where(User.id == current_user.id))
    user: User | None = result.scalar_one_or_none()

    if user is None:
        # Already deleted — treat as success.
        return None

    await db.delete(user)
    # Commit is handled by the get_db dependency after the handler returns.
    return None
