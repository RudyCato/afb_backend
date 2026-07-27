# American Food & Beverage — Operations Platform
## Engagement brief and development prompt

**Client:** American Food & Beverage / Premium Food Distributors, DBA Grassland — Paterson, NJ
**Prepared by:** Rudy Cato
**Version:** Draft, July 2026

---

## 1. What this is

American Food & Beverage is a wholesale importer, roaster, packer and distributor of dried
fruits, nuts, seeds, trail mixes, granolas, plantain chips, chocolate-covered items, candies,
grains, beans and lentils. They run a 60,000 sq ft SQF-certified facility in Paterson, NJ, hold
USDA Organic and OU Kosher certification, and deliver next-day across the Tri-State area on
their own fleet.

They currently run operations on **CSTA-Financials** by Commerce Solutions LLC — a ClickOnce
.NET 4.6.1 desktop application with an embedded Adobe Flash dependency and SQL credentials
stored in plaintext. It is unsupported technology carrying live business risk.

The objective is to replace it with a single connected platform covering commerce, order
intake, warehouse operations, and food-safety record keeping — and to sell that platform as a
paid engagement rather than continue building on speculation.

---

## 2. Commercial objective

**Convert the existing demo into a signed, paid engagement.**

Every technical decision below is subordinate to that. The build exists to make the sale
credible and the delivery deliverable — not the other way around.

Three things carry the sale:

1. **Risk.** The incumbent system has documented security exposure and a dead Flash dependency.
   This is an audit finding waiting to happen.
2. **Consolidation.** Orders currently arrive by email, phone, Pepperi and Magento and are
   re-keyed. Every re-key is an error and a labor cost.
3. **Audit readiness.** SQF record retrieval is manual today. SQF Edition 10 was published in
   March 2026 with audits anticipated no earlier than January 2027, so a code transition is
   coming. This is the wedge the incumbent cannot answer.

**Deliverable before further build:** a priced proposal with defined phases, acceptance criteria
per phase, and a decision on commercial model (hourly, fixed-phase, or perpetual license plus
annual maintenance).

---

## 3. System scope

Four surfaces, one data model.

### 3.1 Public commerce — *built, needs decisions*

Dual-audience website: retail shoppers and wholesale buyers on the same catalog, same URLs,
mode-aware presentation. 369 SKUs across 10 categories and 7 packaging formats. Wholesale
pricing gated behind account approval; retail transacts.

Open: does retail transact on this platform or hand off to their existing Magento? Does the
catalog stay a flat file or become backend-driven?

### 3.2 Order intake — *not built*

Orders must land in one queue regardless of origin:

- **Pepperi** — their existing sales-rep ordering tool. Needs API discovery: available
  endpoints, auth model, webhook support, whether it can push or must be polled.
- **Magento** — existing e-commerce. REST/GraphQL API available; order webhook on placement.
- **Email** — unstructured POs and spreadsheets from buyers. Needs a parse-and-review queue,
  not blind automation. A human confirms before it becomes an order.
- **Phone / manual** — direct entry by CSR.
- **EDI** — likely required by supermarket chains. Confirm which trading partners and which
  document sets (850 purchase order, 855 acknowledgement, 856 ASN, 810 invoice) before scoping.

Requirement: every order carries its source, arrives in one review queue, and is never re-keyed.

### 3.3 Operations backend — *substantially built*

Live at `afb-backend-58ys.onrender.com`. FastAPI + SQLAlchemy + Postgres.

Existing: five-stage order lifecycle, executive dashboard with drill-downs, packing and
production module with manager assignment and packer portal, packaging-materials bill of
materials, pallets and manifests, product mixer with weight-percentage scaling, timed and
reassignable order tasks (picking, raw material packaging, labeling, boxing).

To add: warehouse locations and bin management, returns processing, barcode scanning,
catch-weight items, batch and expiration tracking, purchasing and receiving, inventory
adjustments with reason codes, and the production and packing depth detailed in Phase 4 —
scheduling, changeover control, lot coding, label reconciliation, yield and rework.

### 3.4 SQF reporting module — *new, detailed in section 5*

---

## 4. Data and hosting decision

**This decision must be made with the client before Phase 2 work begins**, because it changes
architecture, cost and contract structure.

| | Hosted (Render/cloud) | In-house server |
|---|---|---|
| Uptime | Provider-managed | Their responsibility |
| Cost shape | Monthly operating expense | Capital purchase + maintenance |
| Backups | Managed, point-in-time on higher tiers | Must be built and tested |
| Access offsite | Native | Requires VPN or exposure |
| Warehouse resilience | Fails if internet fails | Survives internet loss |
| Audit posture | Vendor SOC 2 inherited | Fully self-attested |
| Data control | Third-party custody | Complete |

**Recommendation to present:** hosted primary with local read-only fallback for the packing
floor. Warehouse operations must not stop because an ISP does. A hybrid keeps floor terminals
working offline and syncs on reconnect.

Decision inputs needed from the client: existing IT support arrangement, tolerance for monthly
recurring cost versus capital purchase, any customer contract clauses on data residency, and
whether their insurer or auditors impose requirements.

**Current demo hosting:** Render. Hobby workspace (free) with paid compute per service —
Starter instance at $7/month removes the spin-down that causes cold starts on free instances.
Static sites are free. Note free Postgres expires 30 days after creation with a 14-day grace
period, so the demo database needs upgrading. Legacy Render workspaces migrate to new plans
automatically on August 1, 2026.

---

## 5. SQF reporting module

### 5.1 Framing — read this before writing any code

**The module does not make anyone compliant.** It captures, retains and retrieves records that
reflect what actually happens in the facility. Adequacy is determined by the site's SQF
Practitioner and the certification body's auditor.

Sell it as **audit readiness and record retrieval**. Never as certification, never as
compliance guarantee. Put that distinction in the proposal in writing.

### 5.2 Current code position

- **Edition 9** is the basis for audits at time of writing.
- **Edition 10** was published March 2026; audits anticipated no earlier than January 2, 2027,
  pending GFSI benchmarking, so the effective date may move.
- Reported areas of expansion in Edition 10 include environmental monitoring and food fraud
  prevention.

**Design implication:** do not hard-code clause numbers. Store record types with a mapping
table to code references, so an edition change is a data update rather than a rebuild. This is
itself a selling point — their current system cannot absorb a code transition at all.

### 5.3 Discovery required before build

Do not design from general SQF knowledge. Obtain from the client:

1. Their current SQF certificate — edition, food sector categories, scope, certification body,
   audit date.
2. Their existing record forms — the actual paper or spreadsheet templates in use today.
3. Their last audit report, including any non-conformances raised.
4. The name and availability of their SQF Practitioner. **This person is the primary
   stakeholder for this module.**
5. Their HACCP plan and identified critical control points.

Design the module to reproduce their existing records first. Improve second.

### 5.4 Record categories to support

Subject to confirmation against their certificate and their practitioner's direction. Typical
categories for a repacking and manufacturing operation of this type:

- **Traceability** — one-up/one-back by lot, raw material lot to finished case, with mock
  recall exercise capability and time-to-complete measurement.
- **Supplier approval** — approved supplier list, certificates on file with expiry alerts,
  certificates of analysis per received lot.
- **Receiving** — inspection records, temperature where applicable, rejection records.
- **Production** — batch records, lot codes, best-by assignment, yields, rework disposition.
- **Allergen control** — the facility handles peanuts, tree nuts, sesame, milk and soy.
  Changeover records, cleaning validation, label reconciliation.
- **Sanitation** — master cleaning schedule, completion records, verification results.
- **Environmental monitoring** — sampling plan, results, trending, corrective actions. Expect
  increased scrutiny under Edition 10.
- **Calibration** — scales and thermometers, schedule and records. Directly relevant given
  catch-weight and weight-percentage blending.
- **Pest control** — service reports, trend analysis, corrective actions.
- **Training** — per employee, per task, with competency verification and expiry.
- **Internal audit** — schedule, findings, corrective actions, close-out.
- **Corrective and preventive action** — root cause, action, verification of effectiveness.
- **Customer complaints** — log, investigation, trend analysis.
- **Product identification and labeling** — specification control, label approval and
  reconciliation.
- **Food defense and food fraud** — vulnerability assessments and mitigation records.

### 5.5 Functional requirements

- Every report viewable on screen, exportable to PDF, and printable with facility header,
  date range, generated-by, and generated-at stamp.
- Date-range and lot-number filtering across all record types.
- **Records are append-only.** Corrections create a new versioned entry with reason and
  author; nothing is silently overwritten. This is non-negotiable for audit credibility.
- Full audit trail: who entered, who approved, when, from where.
- Retention policy configurable per record type.
- Electronic signature capture for approvals, with the signer's identity bound to the record.
- Alerting on lapses: overdue calibration, expiring supplier certificates, missed sanitation,
  overdue training.
- **Audit mode** — a read-only export of all records for a given date range, to hand to an
  auditor without giving system access.
- Mock recall: select a lot, return every affected inbound and outbound movement, time the
  exercise, produce a report.

### 5.6 Legacy and integration

Legacy databases identified in their environment: `BSC_Demo_Meat`, `Standard_Beef`,
`Ceramar_New`, `Wise_Kosher`, `Unique_Foods`, `Horizon_Foods`, `Ceramar`. Determine which
contain live AFB data, which are dormant, and what historical records must be migrated versus
archived read-only.

Crystal Reports is in use against the legacy system. Inventory which reports are actually run
and by whom before assuming any need rebuilding.

---

## 6. Working model

Claude operates as the engineering function on this project. That means:

- **Research before building.** Verify current API documentation, current code editions,
  current pricing and current library versions rather than relying on training data. Say so
  when something is unverified.
- **Make implementation decisions independently.** Do not ask which library or which pattern.
  Do ask about business rules, client-specific numbers, and anything that would be expensive
  to reverse.
- **Flag risk plainly**, including when a request is unwise, when scope is drifting, or when
  something is being built ahead of the sale.
- **Test before delivering.** Render it, run it, exercise the flow. Report what was verified
  and what was not.
- **Produce both halves.** Technical builds and the business-facing artifacts that sell and
  support them: proposals, SOPs, stakeholder interviews, training material, decks.
- **State assumptions in writing** whenever a number, rule or spec was invented to keep moving.
  Placeholder values must be labelled as placeholders.

Environment: Windows, PowerShell, VS Code. Python 3.14 in a project venv. FastAPI, SQLAlchemy,
Postgres. GitHub `RudyCato`. Render for hosting. Brand aesthetic: kraft paper — warm browns,
cream, terracotta.

---

## 7. Phasing

**Phase 0 — Sell it.** Discovery interviews (Shipping & Receiving Manager, Packing Room
Manager, SQF Practitioner, CEO), documented findings, priced proposal, signed scope.
*No further build until this closes.*

**Phase 1 — Foundation.** Hosting decision. Production-grade deployment. Auth and roles.
Data migration plan. Backup and restore, tested.

**Phase 2 — Order intake.** Unified order queue. Pepperi integration. Magento integration.
Email parse-and-review. EDI if trading partners require it.

**Phase 3 — Warehouse depth.** Locations and bins. Barcoding. Catch-weight. Batch and
expiration tracking. Returns. Receiving and purchasing.

**Phase 4 — Production and packing.** The packing room is where most of the labor cost sits
and where nearly every food-safety record originates. This phase must precede the SQF module,
because the SQF module reports on data this phase captures.

Already built: packing and production module with manager assignment, packer portal, timed and
reassignable order tasks (picking, raw material packaging, labeling, boxing), product mixer
with weight-percentage scaling, packaging-materials bill of materials.

To add:

- **Production scheduling and work orders** — what runs on which line, in what order, on what
  day. Roasting, flavoring, blending, chocolate panning and packing each scheduled.
- **Changeover control** — sequencing, cleaning between runs, and sign-off. This is the
  allergen control point: peanuts, tree nuts, sesame, milk and soy are all in the facility, so
  run order is a food-safety decision, not just a scheduling one.
- **Lot code and best-by assignment** at pack, linked to the raw material lots consumed. This
  is what makes one-up/one-back traceability possible downstream.
- **Label control and reconciliation** — labels issued, applied, damaged and destroyed,
  reconciled per run. A standing audit finding across the industry.
- **Yield and loss capture** — input weight versus output weight per run, with variance
  flagged. Gives the client a hard number for the ROI case.
- **Rework disposition** — what happens to product that doesn't pass, who authorized it, and
  which run it re-entered.
- **Packaging material consumption** — containers, lids, boxes, film and PPE drawn down against
  the BOM, with reorder points. Running out of 16 oz lids stops a line.
- **Catch-weight capture at pack** for items sold by actual weight.
- **Line and equipment assignment**, including scale identity per run so calibration records
  tie to the product that passed over them.

**Phase 5 — SQF module.** Record capture, reporting, audit mode, mock recall, alerting.
Delivered against their actual forms and their practitioner's sign-off. Depends on Phase 4.

**Phase 6 — Transition and support.** Training, SOPs, parallel running, cutover, maintenance
agreement.

---

## 8. Open decisions

| Decision | Owner | Blocks |
|---|---|---|
| Commercial model — hourly vs fixed-phase vs license + maintenance | Rudy + AFB | Proposal |
| Hosted vs in-house vs hybrid | AFB, informed by Rudy | Phase 1 |
| Retail transacts here or hands off to Magento | AFB | Commerce build |
| Pepperi API capability and access | AFB to provide credentials | Phase 2 scoping |
| Which EDI trading partners and document sets | AFB | Phase 2 scoping |
| Real wholesale minimums, MOQs and price tiers | AFB | Commerce accuracy |
| SQF Practitioner availability as stakeholder | AFB | Phase 5 |
| Line/equipment list and realistic changeover rules | AFB, Packing Room Manager | Phase 4 |
| Who authorizes rework, and on what basis | AFB | Phase 4 |
| Historical data migration scope | Rudy to assess, AFB to approve | Phase 1 |

---

## 9. Known caveats in current work

- Retail prices on the demo site are derived placeholders, not AFB pricing.
- Order minimums (20 cases / 250 lb, MOQ by format) are invented defaults, configurable in one
  place, requiring client confirmation.
- Checkout stops at the payment handoff; no processor is wired.
- Quote, contact and account-request forms resolve client-side and do not send.
- The wholesale pricing gate is a stated policy, not enforced authentication.
- Product imagery is typographic placeholder, not photography.
