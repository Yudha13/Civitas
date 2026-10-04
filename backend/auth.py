"""Google authentication helpers for CIVITAS.

The simulation engine remains independent from authentication. This module only
verifies Google ID tokens and normalizes the identity claims used by the API.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, Request
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token


@dataclass(frozen=True)
class GoogleUser:
    """Verified Google identity used by CIVITAS."""

    subject: str
    email: str | None
    name: str | None
    picture: str | None


def verify_google_credential(credential: str) -> GoogleUser:
    """Verify a Google ID token and return its trusted identity claims."""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=503, detail="Google authentication is not configured")

    try:
        payload: dict[str, Any] = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            client_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid Google credential") from exc

    if payload.get("iss") not in {"accounts.google.com", "https://accounts.google.com"}:
        raise HTTPException(status_code=401, detail="Invalid Google token issuer")

    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject:
        raise HTTPException(status_code=401, detail="Google token has no subject")

    return GoogleUser(
        subject=subject,
        email=payload.get("email") if isinstance(payload.get("email"), str) else None,
        name=payload.get("name") if isinstance(payload.get("name"), str) else None,
        picture=payload.get("picture") if isinstance(payload.get("picture"), str) else None,
    )


def current_user(request: Request) -> dict[str, Any] | None:
    """Return the authenticated user claims stored in the CIVITAS session."""
    return request.session.get("user")


def require_user(request: Request) -> dict[str, Any]:
    """Return the current user or reject an unauthenticated request."""
    user = current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user
