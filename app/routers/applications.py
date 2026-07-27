"""
Careers — application intake.

Accepts an application, stores it, emails the applicant a confirmation and
forwards the whole thing (resume attached) to the hiring inbox.

Environment variables (set these in Render → Environment, never in code):

    SMTP_HOST           smtp.gmail.com
    SMTP_PORT           587
    SMTP_USER           the sending mailbox
    SMTP_PASSWORD       app password, NOT the account password
    MAIL_FROM           "American Food & Beverage Careers <careers@...>"
    HIRING_INBOX        rudycato@gmail.com
    MAIL_ENABLED        "1" to actually send; anything else logs only

If MAIL_ENABLED is off the application is still stored and the email is
written to the log, so the flow can be tested without sending anything.
"""

import os
import io
import re
import ssl
import smtplib
import logging
from datetime import datetime, timezone
from email.message import EmailMessage

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, BackgroundTasks
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import Session

from ..database import Base, engine, get_db

log = logging.getLogger("applications")

router = APIRouter(prefix="/api/applications", tags=["careers"])

MAX_RESUME_BYTES = 5 * 1024 * 1024
ALLOWED_EXT = {".pdf", ".doc", ".docx", ".rtf", ".txt", ".jpg", ".jpeg", ".png", ".heic"}
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# --------------------------------------------------------------------------- model
class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    submitted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    role = Column(String(120), nullable=False)
    full_name = Column(String(160), nullable=False)
    email = Column(String(160), nullable=False, index=True)
    phone = Column(String(40), nullable=False)
    city = Column(String(120))

    authorized_to_work = Column(Boolean, default=False)
    over_18 = Column(Boolean, default=False)
    earliest_start = Column(String(60))
    shift_preference = Column(String(60))
    language = Column(String(10), default="en")

    # driver roles only
    cdl_class = Column(String(20))
    clean_license = Column(Boolean)

    experience = Column(Text)
    referred_by = Column(String(160))

    resume_filename = Column(String(255))
    resume_size = Column(Integer)

    status = Column(String(40), default="new", index=True)
    notes = Column(Text)

    source_ip = Column(String(64))


Base.metadata.create_all(bind=engine)


# --------------------------------------------------------------------------- mail
def _smtp_config():
    return dict(
        host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
        port=int(os.getenv("SMTP_PORT", "587")),
        user=os.getenv("SMTP_USER", ""),
        password=os.getenv("SMTP_PASSWORD", ""),
        sender=os.getenv("MAIL_FROM") or os.getenv("SMTP_USER", ""),
        inbox=os.getenv("HIRING_INBOX", "rudycato@gmail.com"),
        enabled=os.getenv("MAIL_ENABLED", "0") == "1",
    )


def _send(msg: EmailMessage):
    cfg = _smtp_config()
    if not cfg["enabled"]:
        log.info("MAIL DISABLED — would have sent to %s: %s", msg["To"], msg["Subject"])
        return
    if not cfg["user"] or not cfg["password"]:
        log.error("SMTP credentials missing; cannot send %s", msg["Subject"])
        return
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=20) as s:
            s.starttls(context=ctx)
            s.login(cfg["user"], cfg["password"])
            s.send_message(msg)
        log.info("sent %r to %s", msg["Subject"], msg["To"])
    except Exception:
        # never let a mail failure lose the application
        log.exception("send failed for %s", msg["To"])


ACK_EN = """Hi {name},

Thanks for applying to American Food & Beverage for the {role} position.
We've received your application and someone will review it shortly. If it
looks like a fit, we'll reach out to arrange a conversation.

A few things worth knowing:
  - We're at our own facility in Paterson, NJ. Everything we sell, we pack.
  - Most roles start with a walk through the plant so you can see the work.
  - If you don't hear back within two weeks, feel free to follow up.

Please don't reply to this message — it's automated. Use the contact details
on our site if you need to reach us.

American Food & Beverage
Premium Food Distributors, DBA Grassland
Paterson, NJ
"""

ACK_ES = """Hola {name}:

Gracias por postularse a American Food & Beverage para el puesto de {role}.
Hemos recibido su solicitud y alguien la revisará en breve. Si su perfil
encaja, nos comunicaremos con usted para conversar.

Algunos datos útiles:
  - Estamos en nuestra propia planta en Paterson, NJ. Todo lo que vendemos,
    lo empacamos nosotros.
  - La mayoría de los puestos comienzan con un recorrido por la planta.
  - Si no recibe respuesta en dos semanas, puede darnos seguimiento.

Por favor no responda a este mensaje: es automático.

American Food & Beverage
Premium Food Distributors, DBA Grassland
Paterson, NJ
"""


def _acknowledge(app_row: Application):
    cfg = _smtp_config()
    body = (ACK_ES if app_row.language == "es" else ACK_EN).format(
        name=app_row.full_name.split(" ")[0], role=app_row.role
    )
    msg = EmailMessage()
    msg["Subject"] = (
        f"Recibimos su solicitud — {app_row.role}" if app_row.language == "es"
        else f"We received your application — {app_row.role}"
    )
    msg["From"] = cfg["sender"]
    msg["To"] = app_row.email
    msg["Reply-To"] = cfg["inbox"]
    msg.set_content(body)
    _send(msg)


def _forward(app_row: Application, resume_bytes: bytes, resume_name: str, content_type: str):
    cfg = _smtp_config()
    lines = [
        f"New application — {app_row.role}",
        "",
        f"Name              {app_row.full_name}",
        f"Email             {app_row.email}",
        f"Phone             {app_row.phone}",
        f"City              {app_row.city or '—'}",
        f"Authorized to work {'yes' if app_row.authorized_to_work else 'NO'}",
        f"18 or over        {'yes' if app_row.over_18 else 'NO'}",
        f"Earliest start    {app_row.earliest_start or '—'}",
        f"Shift preference  {app_row.shift_preference or '—'}",
        f"Language          {app_row.language}",
    ]
    if app_row.cdl_class:
        lines += [
            f"CDL class         {app_row.cdl_class}",
            f"Clean license     {'yes' if app_row.clean_license else 'no'}",
        ]
    lines += [
        f"Referred by       {app_row.referred_by or '—'}",
        "",
        "Experience:",
        app_row.experience or "(none given)",
        "",
        f"Resume            {resume_name or 'not attached'}",
        f"Submitted         {app_row.submitted_at:%Y-%m-%d %H:%M UTC}",
        f"Record ID         {app_row.id}",
    ]

    msg = EmailMessage()
    msg["Subject"] = f"[Application] {app_row.role} — {app_row.full_name}"
    msg["From"] = cfg["sender"]
    msg["To"] = cfg["inbox"]
    msg["Reply-To"] = f"{app_row.full_name} <{app_row.email}>"
    msg.set_content("\n".join(lines))

    if resume_bytes and resume_name:
        maintype, _, subtype = (content_type or "application/octet-stream").partition("/")
        msg.add_attachment(
            resume_bytes, maintype=maintype or "application",
            subtype=subtype or "octet-stream", filename=resume_name,
        )
    _send(msg)


# --------------------------------------------------------------------------- routes
@router.post("", status_code=201)
async def submit_application(
    background: BackgroundTasks,
    role: str = Form(...),
    full_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    city: str = Form(""),
    authorized_to_work: bool = Form(False),
    over_18: bool = Form(False),
    earliest_start: str = Form(""),
    shift_preference: str = Form(""),
    language: str = Form("en"),
    cdl_class: str = Form(""),
    clean_license: bool = Form(False),
    experience: str = Form(""),
    referred_by: str = Form(""),
    resume: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    full_name = full_name.strip()
    email = email.strip().lower()

    if len(full_name) < 2:
        raise HTTPException(422, "Please give your full name.")
    if not EMAIL_RE.match(email):
        raise HTTPException(422, "That email address doesn't look right.")
    if len(re.sub(r"\D", "", phone)) < 10:
        raise HTTPException(422, "Please give a phone number we can reach you on.")

    resume_bytes, resume_name, content_type = b"", "", ""
    if resume is not None and resume.filename:
        resume_name = os.path.basename(resume.filename)
        ext = os.path.splitext(resume_name)[1].lower()
        if ext not in ALLOWED_EXT:
            raise HTTPException(422, f"Resume must be one of: {', '.join(sorted(ALLOWED_EXT))}")
        resume_bytes = await resume.read()
        if len(resume_bytes) > MAX_RESUME_BYTES:
            raise HTTPException(413, "Resume is over 5 MB. Please send a smaller file.")
        content_type = resume.content_type or "application/octet-stream"

    row = Application(
        role=role.strip()[:120],
        full_name=full_name[:160],
        email=email[:160],
        phone=phone.strip()[:40],
        city=city.strip()[:120] or None,
        authorized_to_work=bool(authorized_to_work),
        over_18=bool(over_18),
        earliest_start=earliest_start.strip()[:60] or None,
        shift_preference=shift_preference.strip()[:60] or None,
        language="es" if language == "es" else "en",
        cdl_class=cdl_class.strip()[:20] or None,
        clean_license=bool(clean_license) if cdl_class.strip() else None,
        experience=experience.strip() or None,
        referred_by=referred_by.strip()[:160] or None,
        resume_filename=resume_name or None,
        resume_size=len(resume_bytes) or None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    # send after responding — the applicant shouldn't wait on SMTP
    background.add_task(_acknowledge, row)
    background.add_task(_forward, row, resume_bytes, resume_name, content_type)

    return {"ok": True, "id": row.id,
            "message": "Application received. Check your email for confirmation."}


@router.get("")
def list_applications(status: str | None = None, role: str | None = None,
                      limit: int = 100, db: Session = Depends(get_db)):
    """Internal listing for the ops portal. Put this behind auth before launch."""
    q = db.query(Application).order_by(Application.submitted_at.desc())
    if status:
        q = q.filter(Application.status == status)
    if role:
        q = q.filter(Application.role == role)
    return [
        {
            "id": a.id, "submitted_at": a.submitted_at, "role": a.role,
            "full_name": a.full_name, "email": a.email, "phone": a.phone,
            "city": a.city, "authorized_to_work": a.authorized_to_work,
            "over_18": a.over_18, "earliest_start": a.earliest_start,
            "shift_preference": a.shift_preference, "cdl_class": a.cdl_class,
            "resume_filename": a.resume_filename, "status": a.status,
            "language": a.language,
        }
        for a in q.limit(min(limit, 500)).all()
    ]


@router.patch("/{app_id}")
def update_status(app_id: int, status: str = Form(...), notes: str = Form(""),
                  db: Session = Depends(get_db)):
    row = db.get(Application, app_id)
    if not row:
        raise HTTPException(404, "No such application")
    row.status = status[:40]
    if notes:
        row.notes = notes
    db.commit()
    return {"ok": True, "id": row.id, "status": row.status}
