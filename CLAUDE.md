# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# AFB Backend

FastAPI operations backend for American Food & Beverage — inventory, orders,
packing, shipping, production, SOPs/training, applications/careers, plus the
customer-facing marketing/ordering site. One FastAPI app serves all of it;
there is no separate frontend build.

## Running locally

```
py -3.14 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Then use `.\start.ps1` (activates `venv`, runs `start.py`) rather than
invoking uvicorn directly — it's the expected entry point. `start.py`
supports `--port`, `--host`, `--no-reload`, and `--check` (verifies the
venv, dependencies, `afb-site`, and SOP seed without starting the server;
also seeds the SOP library on every run — safe, since `seed_from_json`
skips codes that already exist).

Seed the operational database (products/customers/sample orders) with
`python seed.py`, or `python seed.py --catalog-only` to reload just the
catalog. **This wipes and rebuilds `afb.db` from scratch** — don't run it
against a database with real data.

There is no test suite in this repo currently.

## Architecture: three UIs, one API

- **`app/routers/`** — the REST API, mounted with no path prefix conflicts
  except where noted below. Grouped by domain:
  - Order lifecycle: `customers`, `products`, `inventory`, `orders`,
    `order_tasks` (granular picking/packaging/labeling/boxing steps per
    order, independently assignable/timed), `packing`, `shipping`, `pallets`
  - Production: `production`, `packaging` (indirect-material specs — how
    many containers/lids/boxes a packing job needs), `mixes` (recipe
    breakdown for blended products like granola, e.g. cases → lbs of each
    ingredient)
  - `reports` — dashboard KPIs, cycle-time, shipping/packing productivity
  - `sops` — SOP documents, acknowledgments, training records, cleaning
    logs (see dedicated section below)
  - `applications` — careers/job application intake + email (see below)
- **`web/`** — internal ops UI (plain HTML/JS, no build step): the
  operations `dashboard`, `production` (packing manager assignments +
  packer logs), and the legacy `order` page. Served directly by routes in
  `app/main.py` (`/dashboard`, `/production`, `/order`, `/`).
- **`afb-site/`** — the public marketing + customer ordering site (static
  HTML, no build step), mounted at **`/store`**. See `afb-site/README.md`
  for how its two modes (retail/wholesale) and data files work.
- **`app/afb-site/`** is a **stale, partial duplicate** of the top-level
  `afb-site/` (missing `careers.html`, `sops.html`, `jobs.json`,
  `sops.json`, `tools/`, and differing on the rest). It is untracked in
  git and not referenced by `app/main.py` — don't edit it or assume it's
  the live copy; the site actually served is the repo-root `afb-site/`.

There is no authentication on any endpoint yet — every write endpoint
(status changes, packing, shipping, applications review) is open. This is
a known, accepted gap for the current pilot stage, not an oversight to
silently fix.

## Routing gotcha: `/store` mount

`app/main.py` mounts the marketing/ordering site (`afb-site/`, static HTML)
at `/store` as the **last line of the file**, after all API routers and page
routes are registered. It has to stay last: `StaticFiles(html=True)` will
otherwise shadow API routes that come after it.

## SOPs: `sop-library/*.md` is the source of truth

`sop-library/*.md` (repo root) are the actual SOP documents, hand-authored
in a fixed control-table format (see `afb-site/tools/write_sops.py` for the
template each document follows: code/title header, a `| Field | Value |`
control table, then numbered `##` sections). `app/sops.json` (read by
`app/routers/sops.py`'s `seed_from_json`) and `afb-site/sops.json` are
**generated from that markdown**, never hand-edited.

`afb-site/tools/sync_sops.py` parses `sop-library/*.md` and writes a
`sops.json` — but it does so relative to whatever directory it's run from
(`SRC = "sop-library"` and the output path `"sops.json"` are both bare
relative paths, not anchored to the script's own location). `sop-library/`
only exists at the repo root, so the script only finds its input when run
from the repo root — and when run from there, it writes `sops.json` to the
repo root, **not** to `app/sops.json` or `afb-site/sops.json` directly.
Regenerating both consumer copies currently means running the script from
the repo root and then copying the resulting root-level `sops.json` into
both `app/` and `afb-site/` yourself (or fixing the script to write to both
locations) — check current behavior before trusting either generated file
is fresh.

The SOP domain model (`app/routers/sops.py`) itself has firm invariants
worth preserving in any change: document bodies are versioned and
append-only (a revision is a new `SopVersion` row, never an edit);
acknowledgments are bound to one specific version and don't carry forward
when the document changes; nothing is silently overwritten or deleted
(retirement is a status change); fields the source markdown doesn't
specify are stored as `NULL`, never guessed or defaulted.

## Careers / applications: email is optional, storage isn't

`app/routers/applications.py` always stores a submitted application first;
whether it *also* emails a confirmation to the applicant and forwards the
full application (with resume attached) to the hiring inbox depends on the
`MAIL_ENABLED` env var. With `MAIL_ENABLED` unset or not `"1"`, sending is
skipped and logged instead — useful for exercising the flow locally without
real SMTP credentials (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`,
`SMTP_PASSWORD`, `MAIL_FROM`, `HIRING_INBOX`). A send failure never loses
the stored application — it's caught and logged, not raised.

## Before deploying to Render

`render.yaml` already wires `DATABASE_URL` from the `afb-db` Postgres
database, and `app/database.py` already falls back to SQLite locally and
normalizes `postgres://` → `postgresql://`. Confirm `DATABASE_URL` is
actually set/working in the Render environment before relying on it in
production — this hasn't been verified against a live deploy yet. See
`docs/HOSTING.md` for the fuller two-service (static site + backend +
Postgres) hosting plan and cost breakdown, and `DEPLOYMENT.md` for the
step-by-step Render Blueprint walkthrough.
