"""
Shared SMTP helper for outbound mail.

Environment variables (set these in Render → Environment, never in code):

    SMTP_HOST           smtp.gmail.com
    SMTP_PORT           587
    SMTP_USER           the sending mailbox
    SMTP_PASSWORD       app password, NOT the account password
    MAIL_FROM           "American Food & Beverage <ops@...>"
    MAIL_ENABLED        "1" to actually send; anything else logs only

Per-purpose recipient inboxes:

    HIRING_INBOX        job applications         (default: rudycato@gmail.com)
    PACKING_INBOX       new packing assignments  (default: rudycato@gmail.com)

If a recipient inbox isn't set, we fall back to HIRING_INBOX so no email is
silently dropped in a partially-configured environment.
"""
from __future__ import annotations

import logging
import os
import smtplib
import ssl
from email.message import EmailMessage

log = logging.getLogger("mail")

_DEFAULT_INBOX = "rudycato@gmail.com"


def smtp_config() -> dict:
    return dict(
        host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
        port=int(os.getenv("SMTP_PORT", "587")),
        user=os.getenv("SMTP_USER", ""),
        password=os.getenv("SMTP_PASSWORD", ""),
        sender=os.getenv("MAIL_FROM") or os.getenv("SMTP_USER", ""),
        enabled=os.getenv("MAIL_ENABLED", "0") == "1",
    )


def inbox_for(purpose_env_var: str) -> str:
    """Return the configured inbox for a given purpose, falling back to HIRING_INBOX
    so a partially-configured environment still delivers somewhere sensible."""
    return (
        os.getenv(purpose_env_var)
        or os.getenv("HIRING_INBOX")
        or _DEFAULT_INBOX
    )


def send(msg: EmailMessage) -> None:
    """Best-effort send. Logs and swallows exceptions — callers should never
    block or fail a user request because SMTP is down."""
    cfg = smtp_config()
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
        log.info("Mail sent to %s: %s", msg["To"], msg["Subject"])
    except Exception:
        log.exception("SMTP send failed for %s", msg["Subject"])


def build_message(*, subject: str, to: str, body: str, reply_to: str | None = None) -> EmailMessage:
    cfg = smtp_config()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg["sender"]
    msg["To"] = to
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(body)
    return msg


def attach_pdf(msg: EmailMessage, *, filename: str, data: bytes) -> None:
    """Attach a PDF byte payload to an existing EmailMessage."""
    msg.add_attachment(
        data,
        maintype="application",
        subtype="pdf",
        filename=filename,
    )
