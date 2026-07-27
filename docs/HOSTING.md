# Hosting — what has to happen

Two services. One is free, one is $7/month.

| Service | Type | Cost | What it serves |
|---|---|---|---|
| `afb-site` | Static Site | **$0** | The public website, careers page, demo |
| `afb-backend-58ys` | Web Service, Starter | **$7/mo** | API, applications, SOP library |
| Postgres | smallest paid tier | **~$6–7/mo** | The data |

Static sites don't spin down, so the demo link is instant even if the backend is asleep.
Your workspace stays on the free Hobby plan — you pay per service, not per seat.

---

## Before anything: three things that will bite

### 1. SQLite on Render loses your data on every deploy

There's an `afb.db` in your repo root. Render's filesystem is ephemeral — if the app is
writing to a SQLite file, **every deploy wipes it**. Applications, acknowledgements, cleaning
logs, all gone, silently.

Check `app/database.py`:

```python
# BAD on Render
engine = create_engine("sqlite:///./afb.db")

# What it needs to be
import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./afb.db")
if DATABASE_URL.startswith("postgres://"):          # Render hands out the old prefix
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
engine = create_engine(DATABASE_URL)
```

Local runs keep using SQLite. Render uses Postgres because `DATABASE_URL` is set there.

Also add `afb.db` to `.gitignore` — a committed database will overwrite itself in confusing
ways.

### 2. Your free Postgres expires

Free Postgres on Render is deleted 30 days after creation, with a 14-day grace period.
Check the creation date today. If it's close, upgrade before you migrate anything into it.

### 3. Do not point the live domain at this

`americanfoodbeverage.com` is AFB's existing Magento store, serving real customers. Pointing
DNS at a demo would take their shop down.

Use the Render URL, or a subdomain they control — `demo.americanfoodbeverage.com` — and only
with their say-so. Domain cutover is a decision for after the sale, not part of hosting.

---

## Step 1 — Prepare the repo

```powershell
cd E:\data\claude\afb_website\afb_backend

# keep the venv and the local db out of git
Add-Content .gitignore "`nvenv/`n*.db`n__pycache__/"

# new backend modules into place
Copy-Item ..\backend\sops.py        app\routers\
Copy-Item ..\backend\applications.py app\routers\
Copy-Item ..\backend\sops.json      app\

# the site itself
Copy-Item -Recurse ..\afb-site .\afb-site
```

In `app/main.py`, add to the router imports and includes:

```python
from .routers import (..., applications, sops)
app.include_router(applications.router)
app.include_router(sops.router)
```

Commit and push.

---

## Step 2 — Static site

Render dashboard → **New → Static Site** → pick the repo.

| Setting | Value |
|---|---|
| Name | `afb-site` |
| Root directory | `afb-site` |
| Build command | *(leave empty)* |
| Publish directory | `.` |

Deploys in under a minute. You get `https://afb-site.onrender.com`.

**Then tell the site where the API is.** Hosted separately, the careers form has no backend
unless you point it. Add this line to `careers.html` and `sops.html`, just above
`<script src="assets/app.js">`:

```html
<script>window.AFB_API = "https://afb-backend-58ys.onrender.com";</script>
```

---

## Step 3 — Backend to Starter

Render dashboard → `afb-backend-58ys` → **Settings → Instance Type → Starter** ($7/mo).

Cold starts stop immediately. Free instances spin down after 15 minutes idle; paid ones don't.

---

## Step 4 — Environment variables

`afb-backend-58ys` → **Environment**. Never in code, never in git.

```
DATABASE_URL      (Render fills this from the linked Postgres)
SMTP_HOST         smtp.gmail.com
SMTP_PORT         587
SMTP_USER         rudycato@gmail.com
SMTP_PASSWORD     <16-char Google App Password — not your account password>
MAIL_FROM         American Food & Beverage Careers <rudycato@gmail.com>
HIRING_INBOX      rudycato@gmail.com
MAIL_ENABLED      0        ← leave at 0 until you've tested
```

The app password needs 2-Step Verification switched on first, at Google Account → Security →
App passwords.

---

## Step 5 — Tighten CORS

`main.py` currently allows every origin:

```python
allow_origins=["*"]           # fine for local, careless in production
```

Change to:

```python
allow_origins=[
    "https://afb-site.onrender.com",
    "http://localhost:8000",
]
```

---

## Step 6 — Seed the SOP library

Once, after the first deploy with Postgres attached. Render → your service → **Shell**:

```bash
python -c "from app.routers.sops import seed_from_json; print(seed_from_json('app/sops.json'))"
```

It's idempotent — existing documents are left alone.

---

## Step 7 — Check it

| Check | Expect |
|---|---|
| `https://afb-site.onrender.com` | Homepage, styled, catalog loads |
| `/careers.html` | Eight roles with pay ranges |
| `/sops.html` | Six documents |
| `https://afb-backend-58ys.onrender.com/ops` | Internal links page |
| `/docs` | FastAPI docs, applications + sops routes listed |
| `/api/sops` | Five active documents |
| Submit a test application | 201, and it appears in `/api/applications` |
| Redeploy, then re-check `/api/applications` | **Your test application is still there.** If it vanished, you're still on SQLite — go back to the top |

Then set `MAIL_ENABLED=1` and submit one more. Two emails should arrive: the acknowledgement
and the forward with the resume attached.

---

## Do not make this public until

These are gates, not suggestions.

- [ ] **Real pay ranges in `jobs.json`.** New Jersey requires the wage or range, a benefits
      description, and any other compensation programs in every posting. The current numbers
      are invented.
- [ ] **`GET /api/applications` behind auth.** It exposes applicant names, emails and phone
      numbers to anyone who guesses the URL. This is the most serious item on the list.
- [ ] **Retail prices replaced**, or the retail cart disabled.
- [ ] **Forms wired** — quote, contact and account request currently send nothing.
- [ ] **`sops.html` behind the staff login.** It's internal; it should not sit on the public
      site.
- [ ] **AFB's approval** to publish anything under their name.

Until those are done, treat the Render URL as a private demo link and don't index it. Adding
`robots.txt` with `Disallow: /` to `afb-site` takes ten seconds and prevents an accidental
Google listing of a half-finished site under the client's brand.

---

## Running total

| | |
|---|---|
| Static site | $0 |
| Backend Starter | $7/mo |
| Postgres, smallest paid | ~$6–7/mo |
| **Total** | **~$13–14/mo** |

Note also that legacy Render workspaces migrated to the new plans on 1 August 2026. Included
outbound bandwidth on Hobby is 5 GB with overage billed per GB. At the demo's size that's tens
of thousands of page loads — not a concern, just don't be surprised by a small line item.
