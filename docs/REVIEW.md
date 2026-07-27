# American Food & Beverage — build review

**Prepared by:** Rudy Cato · July 2026
**Status:** Pre-proposal. Nothing here has been signed for.

---

## Review this in twenty minutes

1. Open **`afb-demo.html`** — one file, no server, works on a phone. Tap through:
   **Shop** → toggle **Wholesale** in the header → **Careers** → **SOPs**.
2. Skim **`sop-library/SOP-PKG-001.md`** — the packing-room cleaning procedure, rewritten as a
   controlled document. This is the template the other five follow.
3. Read **section 4** below. That's the list of things only you or AFB can answer.

Everything else is detail.

---

## 1. What exists

| Surface | State | Where |
|---|---|---|
| **Public website** — retail + wholesale, 369 SKUs | Built, working | `afb-site/` |
| **Careers** — 8 roles, bilingual, apply from a phone | Built, working | `afb-site/careers.html` |
| **Application intake** — auto-reply + forward with resume | Built, needs SMTP config | `backend/applications.py` |
| **SOP library** — 6 controlled documents, acknowledgements | Built, working | `backend/sops.py`, `sop-library/` |
| **Cleaning log** — digital form of the SOP's own record | Built, working | `backend/sops.py` |
| **Training records** — built to AFB's own certification framework | Built, working | `backend/sops.py` |
| **Operations backend** — orders, packing, pallets, mixer | Pre-existing, live on Render | your repo |
| **Standalone demo** — everything above in one emailable file | Built | `afb-demo.html` |

### The website, in one line

One site, three doors: **customers** (retail cards or a wholesale item sheet, same catalog,
same URLs), **candidates** (job postings with pay ranges, two-minute application), and
**staff** (SOP library, and eventually the ops portal).

### The SOP library, in one line

Six documents rewritten to a single house style with real document control, where the markdown
files are the source of truth and everything downstream — the portal, acknowledgement records,
even the duty bullets on job postings — is generated from them.

---

## 2. File map

```
afb-demo.html            ← START HERE. Whole thing, one file, offline, mobile.
afb-demo.zip             ← same file zipped, for mail filters that strip .html

AFB-website-pitch.md     ← two-minute client pitch: one address, three doors
AFB-engagement-brief.md  ← full scope of work, phases 0–6, open decisions

afb-site/                ← the real multi-page site (serve over http, not file://)
  index · shop · product · cart · wholesale · private-label
  certifications · about · careers · sops · quote · contact
  catalog.json           ← 369 SKUs, single source
  jobs.json              ← 8 postings; duties generated from the SOPs
  sops.json              ← generated — do not hand-edit
  assets/                ← site.css · app.js · catalog.js
  tools/                 ← build_catalog · write_sops · sync_sops · build_standalone
  README.md              ← how to run and deploy

backend/                 ← drop into app/routers/
  applications.py        ← careers intake, auto-reply, forward to rudycato@gmail.com
  sops.py                ← SOP library, versions, acknowledgements, training, cleaning logs
  sops.json              ← library seed
  CAREERS-SETUP.md       ← SMTP config and pre-launch checklist

sop-library/             ← THE SOURCE. Edit here, then run tools/sync_sops.py
  SOP-PKG-001  Cleaning tables between products      (SQF — critical)
  SOP-SLS-001  Sales representative routine & targets
  SOP-SLS-002  New Jersey territories                 (DRAFT — unassigned)
  SOP-SLS-003  Sales Director
  SOP-CS-001   In-house sales and customer support
  TRN-SLS-001  Sales training and certification
```

---

## 3. How the pieces connect

```
sop-library/*.md  ──tools/sync_sops.py──▶  sops.json  ──┬──▶  staff portal (read + acknowledge)
   (source of truth)                                    │
                                                        ├──▶  job postings (duty bullets)
                                                        │
                                                        └──▶  training records ──▶ SQF evidence

catalog.json  ──▶  retail grid  ·  wholesale item sheet  ·  product pages  ·  cart / quote

careers form  ──▶  applications table  ──▶  auto-reply to applicant
                                        └─▶  forward to hiring inbox, resume attached
```

Edit a SOP, re-run one script, and the portal and the job postings both update. That's the
point of the structure — a procedure and the record of it can't drift apart.

---

## 4. Decisions needed

### 4.1 Yours

| Decision | Why it's blocking |
|---|---|
| **Commercial model** — hourly, fixed-phase, or licence + maintenance | Nothing should be built past this point without a signed scope |
| **Render spend** — ~$7/mo Starter + ~$6–7/mo Postgres | Kills demo cold starts. Static demo is free. Do it and stop thinking about it |
| **Whether to keep building before the sale** | My recommendation is no. Phase 0 is "sell it" for a reason |

### 4.2 AFB's

| Decision | Owner there | Blocks |
|---|---|---|
| Real wholesale pricing, MOQs, order minimums | Sales / ownership | Commerce accuracy |
| Real pay ranges + benefits sentence for postings | Whoever hires | **Legal — NJ requires this in every posting** |
| New-customer target: 5/week or 30/quarter | Sales Director | `SOP-SLS-001` issue |
| Five NJ territories — named owners and boundaries | Sales Team Leader | `SOP-SLS-002` is in draft until then |
| Approver + effective date on all six SOPs | Document owners | Nothing is a controlled document until signed |
| Retail transacts here, or hands off to Magento | Ownership | Cart architecture |
| Hosted / in-house / hybrid | Ownership, informed by you | Phase 1 |
| Pepperi API access | IT / ownership | Phase 2 scoping |
| SQF Practitioner's time | Ownership | The whole SQF module |

---

## 5. Everything that is a placeholder

Consolidated so nothing gets shown to a client by accident.

| Item | State |
|---|---|
| Retail prices | **Invented.** Derived from a per-ounce rate by category |
| Order minimums (20 cases / 250 lb, MOQ by format) | **Invented.** Configurable in one place |
| Job pay ranges | **Invented.** Legally required to be real before publishing |
| Benefits and other-compensation text | **Invented** |
| Product photography | None — typographic category marks stand in |
| Checkout payment | Stops at the handoff. No processor wired. Deliberate |
| Quote / contact / account-request forms | Resolve client-side, send nothing |
| Wholesale pricing gate | A stated policy, not authentication |
| `GET /api/applications` | **Unauthenticated.** Exposes applicant contact details |
| SOP approver + effective date | Blank by design — needs a signature |
| NJ territory assignments | Blank by design — placeholders aren't assignments |
| Warehouse Associate / CDL Driver / Forklift Operator duties | **Invented.** No SOP exists for these roles |

---

## 6. What isn't built

- Order intake from Pepperi, Magento, email or EDI — the unified queue
- Warehouse locations, bins, barcoding, catch-weight, batch and expiry tracking
- Production scheduling, changeover control, label reconciliation, yield capture
- The rest of the SQF record set (sanitation schedule, environmental monitoring,
  calibration, pest control, supplier approval, CAPA, complaints, mock recall)
- Authentication and roles
- Data migration from CSTA-Financials
- Backups, tested

Phasing for all of it is in `AFB-engagement-brief.md` §7.

---

## 7. Known gaps worth naming out loud

**Three of eight advertised roles have no SOP.** Warehouse Associate, CDL Driver and Forklift
Operator. Their job-posting duties are my invention, not AFB's documented process.

**The Train the Trainers guide was cut from ~40 pages to four.** Only the auditable commitments
stayed under version control — targets, pass marks, retake rules, recertification. Curriculum
and facilitation notes became an uncontrolled trainer annex. Worth confirming AFB agrees with
that split before it's issued.

**The cleaning log form has not been matched to their paper one.** I built it from the
procedure text. Until I see the sheet the packing room actually fills in, field-for-field, it's
a good guess rather than a fit.

**A reporting module does not make anyone SQF compliant.** It captures and retrieves records.
Their Practitioner and their auditor decide adequacy. Never sell it as compliance.

---

## 8. What I'd do next, in order

1. **Interview the SQF Practitioner.** One hour. It's the module nobody else can build, and it
   tells you immediately whether this sale is real.
2. **Get the packing-room cleaning log sheet** and match the digital form to it exactly.
3. **Deploy the demo as a Render static site** so the client link is one tap, not an attachment.
4. **Write the proposal** — phases, acceptance criteria, price. Then stop building until it's
   signed.

The SQF angle is the strongest card in the deck. SQF Edition 10 was published in March 2026
with audits anticipated no earlier than January 2027, so AFB has roughly a year to prepare for
a code transition their current ClickOnce system cannot help with at all. That is a reason to
buy now, and it expires.
