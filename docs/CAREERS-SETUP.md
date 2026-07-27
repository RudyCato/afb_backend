# Careers module — setup

Three files:

| File | Goes where |
|---|---|
| `backend/applications.py` | `app/routers/applications.py` |
| `careers.html` | alongside the other site pages |
| `jobs.json` | alongside `catalog.json` |

## 1. Wire the router

In `app/main.py`, add to the router imports and include it with the others:

```python
from .routers import (customers, products, inventory, orders, packing, shipping,
                      reports, production, pallets, packaging, order_tasks, mixes,
                      applications)
...
app.include_router(applications.router)
```

The router creates its own `applications` table on import. On Render, remember your
`create_all()` only adds new tables — it won't add columns to existing ones. This is a new
table, so it will appear on next deploy without a reseed.

## 2. Environment variables

Set these in **Render → your service → Environment**. Never in code, never in git.

```
SMTP_HOST       smtp.gmail.com
SMTP_PORT       587
SMTP_USER       rudycato@gmail.com
SMTP_PASSWORD   <16-character Google App Password>
MAIL_FROM       American Food & Beverage Careers <rudycato@gmail.com>
HIRING_INBOX    rudycato@gmail.com
MAIL_ENABLED    1
```

`SMTP_PASSWORD` must be a **Google App Password**, not your account password — generate one at
Google Account → Security → 2-Step Verification → App passwords. Your account needs 2-Step
Verification switched on before that option appears.

Leave `MAIL_ENABLED` unset while testing. Applications still save and the email is written to
the log instead of being sent.

## 3. What happens on submit

1. Validated and written to the `applications` table.
2. Response returns immediately — the applicant never waits on SMTP.
3. In the background: a confirmation email to the applicant (English or Spanish, matching the
   language they used), and a full forward to `HIRING_INBOX` with the resume attached and
   `Reply-To` set to the applicant, so hitting reply writes to them directly.

Mail failures are logged and swallowed. An SMTP outage never loses an application.

## 4. Reading applications

`GET /api/applications` returns the queue as JSON, with optional `?status=` and `?role=`
filters. `PATCH /api/applications/{id}` updates status and notes.

**This endpoint is currently unauthenticated.** It exposes applicant contact details. Put it
behind the ops portal login before the site is public, or restrict it at the router level.

## Before this goes live

**Pay ranges in `jobs.json` are placeholders.** Since 1 June 2025, New Jersey employers with
10 or more employees must include the hourly wage or salary — or a range — plus a general
description of benefits and any other compensation programs in every job posting, in any
format. Proposed NJDOL rules also bar open-ended ranges and cap the spread at 60% of the
minimum. Current ranges comply with the 60% rule but the numbers are invented. Get AFB's real
figures and their benefits summary before publishing.

**Resumes are attached to email, not stored.** Only the filename and size go in the database.
Render's disk is ephemeral, so storing files would lose them on redeploy. If AFB wants a
searchable resume archive, that needs S3 or a Render persistent disk — a small, separate piece
of work.

**Deliverability.** Gmail SMTP is fine for testing and low volume. For production, send from
`careers@americanfoodbeverage.com` through a real provider (Resend, Postmark, SES) with SPF and
DKIM on the domain. Auto-responses from a personal Gmail to applicants will land in spam often
enough to cost you candidates.

**What the form deliberately does not ask.** No date of birth, no Social Security number, no
citizenship status, no marital status, no photograph. It asks only whether the applicant is
legally authorized to work and is 18 or over. If AFB wants voluntary EEO self-identification,
that must be optional, kept separate from the application, and not visible to whoever makes the
hiring decision — get their employment counsel to specify it rather than improvising.

**Retention.** Decide how long applications are kept and who can see them, then write it into
the privacy line on the page. Right now the page promises the data is used only for hiring and
not shared outside the company — make sure that stays true.
