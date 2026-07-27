from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import verify_password, hash_password, get_current_staff
from ..database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=schemas.StaffMeOut)
def login(payload: schemas.LoginRequest, request: Request, db: Session = Depends(get_db)):
    staff = db.query(models.StaffUser).filter(
        models.StaffUser.username == payload.username.strip().lower()
    ).first()
    if not staff or not staff.active or not verify_password(payload.password, staff.password_hash):
        raise HTTPException(401, "Incorrect username or password")

    staff.last_login_at = datetime.utcnow()
    db.commit()

    request.session["username"] = staff.username
    return schemas.StaffMeOut(
        username=staff.username, full_name=staff.full_name, role=staff.role,
        must_change_password=staff.must_change_password,
    )


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/me", response_model=schemas.StaffMeOut)
def me(staff: models.StaffUser = Depends(get_current_staff)):
    return schemas.StaffMeOut(
        username=staff.username, full_name=staff.full_name, role=staff.role,
        must_change_password=staff.must_change_password,
    )


@router.post("/change-password")
def change_password(
    payload: schemas.ChangePasswordRequest,
    staff: models.StaffUser = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, staff.password_hash):
        raise HTTPException(401, "Current password is incorrect")
    if len(payload.new_password) < 8:
        raise HTTPException(400, "New password must be at least 8 characters")
    if payload.new_password == payload.current_password:
        raise HTTPException(400, "New password must be different from your current password")

    staff.password_hash = hash_password(payload.new_password)
    staff.must_change_password = False
    db.commit()
    return {"ok": True}
