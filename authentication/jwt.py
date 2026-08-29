from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from django.conf import settings
from rest_framework import authentication, exceptions
from sqlalchemy import select

from .models import BlacklistedToken, OutstandingToken, User


ALGORITHM = "HS256"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _encode(user: User, token_type: str, lifetime: timedelta) -> tuple[str, str, datetime]:
    issued_at = _now()
    expires_at = issued_at + lifetime
    jti = uuid4().hex
    payload = {
        "token_type": token_type,
        "exp": expires_at,
        "iat": issued_at,
        "jti": jti,
        "user_id": str(user.id),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM), jti, expires_at


def create_token_pair(user: User, session) -> tuple[str, str]:
    jwt_settings = settings.SIMPLE_JWT
    access, _, _ = _encode(
        user, "access", jwt_settings["ACCESS_TOKEN_LIFETIME"])
    refresh, jti, expires_at = _encode(
        user, "refresh", jwt_settings["REFRESH_TOKEN_LIFETIME"])
    session.add(
        OutstandingToken(
            user_id=user.id,
            token=refresh,
            jti=jti,
            created_at=_now(),
            expires_at=expires_at,
        )
    )
    return access, refresh


def create_access_token(user: User) -> str:
    access, _, _ = _encode(
        user, "access", settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"])
    return access


def decode_token(raw_token: str, expected_type: str | None = None) -> dict:
    try:
        payload = jwt.decode(raw_token, settings.SECRET_KEY,
                             algorithms=[ALGORITHM])
    except jwt.PyJWTError as error:
        raise exceptions.AuthenticationFailed(
            "Invalid or expired token.") from error
    token_type = payload.get("token_type")
    if expected_type and token_type and token_type != expected_type:
        raise exceptions.AuthenticationFailed("Invalid token type.")
    return payload


def blacklist_refresh_token(raw_token: str, session) -> None:
    payload = decode_token(raw_token, "refresh")
    outstanding = session.scalar(select(OutstandingToken).where(
        OutstandingToken.jti == payload["jti"]))
    if outstanding is None or outstanding.blacklisted_token is not None:
        raise exceptions.AuthenticationFailed(
            "Invalid or expired refresh token.")
    session.add(BlacklistedToken(token=outstanding))


def validate_refresh_token(raw_token: str, session) -> dict:
    payload = decode_token(raw_token, "refresh")
    outstanding = session.scalar(select(OutstandingToken).where(
        OutstandingToken.jti == payload["jti"]))
    if outstanding is None or outstanding.blacklisted_token is not None:
        raise exceptions.AuthenticationFailed(
            "Invalid or expired refresh token.")
    return payload


class SQLAlchemyJWTAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate_header(self, request) -> str:
        return self.keyword

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).split()
        if not header:
            return None
        if len(header) != 2 or header[0].decode().lower() != self.keyword.lower():
            raise exceptions.AuthenticationFailed(
                "Invalid authorization header.")

        token_str = header[1].decode().strip('"\'')
        payload = decode_token(token_str, "access")

        try:
            user_id = int(payload["user_id"])
        except (KeyError, TypeError, ValueError) as error:
            raise exceptions.AuthenticationFailed(
                "Invalid token user.") from error

        session = getattr(request, "db", None)
        if not session:
            raise exceptions.AuthenticationFailed("Database session missing.")

        user = session.get(User, user_id)
        if user is None or getattr(user, "is_active", True) is False:
            raise exceptions.AuthenticationFailed(
                "User not found or inactive.")

        if not hasattr(user, "is_authenticated"):
            setattr(user, "is_authenticated", True)

        return user, payload
