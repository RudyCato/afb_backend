# AFB / Grassland — public site + staff portal

Static, no build step. Twelve pages, three data files, two modes.

See `../REVIEW.md` for the full picture. This file covers running and deploying the site.

## Pages

| | |
|---|---|
| Customers | index · shop · product · cart · wholesale · private-label · certifications · about · quote · contact |
| Candidates | careers |
| Staff | sops |

## Run it

```
cd afb-site
python -m http.server 8000
```

Then open `http://localhost:8000`. It must be served over http — `catalog.json` is fetched,
and `file://` blocks that. (There's a fallback: `assets/catalog.js` embeds the same data, so
double-clicking `index.html` still works, just don't edit only one of the two.)

## Mount it on the FastAPI backend

```python
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="afb-site", html=True), name="site")
```

Mount this **last**, after the API routes, or it will swallow them.

## The two modes

A single `afb.mode` value in localStorage drives everything. The stamp toggle in the header sets it;
the homepage fork sets it; `wholesale.html` forces it. Everything else reads it.

| | Retail | Wholesale |
|---|---|---|
| Catalog view | Photo card grid | Sortable data table |
| Item numbers | Hidden | Primary column |
| Pricing | Shown, transacts | Gated — quote request only |
| Cart | Cart → checkout | Quote list → request form |
| Export | — | CSV of the current filter |
| Product page | Price + add to cart | Specs open, gated notice |

Same URLs throughout. `product.html?item=2810501` serves both audiences.

## Data files

| File | Source of truth | Regenerate with |
|---|---|---|
| `catalog.json` | itself | `tools/build_catalog.py` |
| `jobs.json` | itself, but `does` bullets come from the SOPs | `tools/sync_sops.py` |
| `sops.json` | **generated — never hand-edit** | `tools/sync_sops.py` |

The SOP markdown in `../sop-library/` is the source for `sops.json`. Edit the markdown, run
`python tools/sync_sops.py`, and the portal and the job postings both update.

## Catalog

`catalog.json` is the single source of truth — 369 SKUs, 10 categories, 7 packaging formats.
Fields per product: `item, name, category, format, caseQty, unitOz, caseWeightOz, organic,
kosher, price, blurb, slug`.

To change it, edit `tools/build_catalog.py` and run:

```
cd afb-site && python tools/build_catalog.py
python -c "import json;d=json.load(open('catalog.json'));open('assets/catalog.js','w').write('window.AFB_CATALOG='+json.dumps(d,separators=(',',':'))+';')"
```

Or swap in a live endpoint: change the `fetch` URL in `assets/app.js` (`catalog()`) to point at
`/api/products` and drop the JSON file. That's the only line that touches the data source.

## Before it goes live

1. **Payment.** Checkout collects the order and stops at the handoff. Wire it to Stripe /
   Authorize.net / Magento — do not collect card fields on this page.
2. **Forms.** Quote, account request and contact forms all resolve client-side. Point them at
   real endpoints (or the FastAPI backend) so submissions land somewhere.
3. **Prices are placeholders.** Retail prices are derived from a per-ounce rate by category,
   not from the client's actual pricing. Replace before showing this to a customer.
4. **Photography.** Product tiles use a typographic category mark. Drop real photos in and
   swap `.thumb .glyph` for an `<img>`.
5. **Account gate.** "Pricing shown once approved" is currently a promise, not a login.
   Wire it to the backend's auth when Phase 2 lands.
6. **Careers needs the backend.** `careers.html` posts to `/api/applications` — see
   `../backend/CAREERS-SETUP.md`. Pay ranges in `jobs.json` are placeholders and New Jersey
   requires real ones in every posting.
7. **The SOP portal is staff-facing.** `sops.html` should sit behind the ops login, not on the
   public site. It reads `sops.json` directly today; point it at `/api/sops` once auth exists.

## Accessibility & performance

WCAG AA contrast, visible focus rings, table headers with scope, skip link, labelled inputs,
`prefers-reduced-motion` respected, print stylesheet for the item sheet. No framework, no build,
~30 KB of CSS+JS plus the catalog. Fonts come from Google Fonts with local fallbacks, so it
degrades cleanly on a locked-down warehouse network.
