# AFB / Grassland — dual-audience website

Static, no build step. Ten pages, one catalog file, two modes.

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

## Accessibility & performance

WCAG AA contrast, visible focus rings, table headers with scope, skip link, labelled inputs,
`prefers-reduced-motion` respected, print stylesheet for the item sheet. No framework, no build,
~30 KB of CSS+JS plus the catalog. Fonts come from Google Fonts with local fallbacks, so it
degrades cleanly on a locked-down warehouse network.
