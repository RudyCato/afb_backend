from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .. import models, schemas
from ..auth import verify_password, get_current_staff
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
    return schemas.StaffMeOut(username=staff.username, full_name=staff.full_name, role=staff.role)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/me", response_model=schemas.StaffMeOut)
def me(staff: models.StaffUser = Depends(get_current_staff)):
    return schemas.StaffMeOut(username=staff.username, full_name=staff.full_name, role=staff.role)
