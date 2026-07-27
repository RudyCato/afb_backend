"""
Lightweight staff authentication.

Uses stdlib PBKDF2 password hashing (no extra dependency) and Starlette's
signed-cookie session (already ships with FastAPI/Starlette) — no JWT
library, no separate sessions table, nothing extra to run in production.
"""
import hashlib
import hmac
import os
import secrets

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from . import models
from .database import get_db

PBKDF2_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        salt, digest_hex = password_hash.split("$", 1)
    except ValueError:
        return False
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PBKDF2_ITERATIONS)
    return hmac.compare_digest(check.hex(), digest_hex)


def get_current_staff(request: Request, db: Session = Depends(get_db)) -> models.StaffUser:
    """Dependency for JSON API endpoints — 401s if not logged in."""
    username = request.session.get("username")
    if not username:
        raise HTTPException(401, "Not logged in")
    staff = db.query(models.StaffUser).filter(models.StaffUser.username == username).first()
    if not staff or not staff.active:
        request.session.clear()
        raise HTTPException(401, "Session invalid")
    return staff


def get_current_staff_optional(request: Request, db: Session = Depends(get_db)):
    """Same as above but returns None instead of raising — for page routes
    that need to decide whether to redirect to /login."""
    username = request.session.get("username")
    if not username:
        return None
    staff = db.query(models.StaffUser).filter(models.StaffUser.username == username).first()
    if not staff or not staff.active:
        return None
    return staff


def require_role(*roles: str):
    def _dep(staff: models.StaffUser = Depends(get_current_staff)):
        if staff.role.value not in roles:
            raise HTTPException(403, "Not permitted for this role")
        return staff
    return _dep
