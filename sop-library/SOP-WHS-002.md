<!-- Controlled document. The current version lives in the AFB operations
portal. A printed copy is uncontrolled once it leaves the screen. -->

# SOP-WHS-002 · Shipping Outbound Orders

| Field | Value |
|---|---|
| Document code | `SOP-WHS-002` |
| Version | 1.0 |
| Status | Active — pending approval |
| Scope | **SQF + FSMA 204.** Every pallet leaving the building carries a unique SSCC that ties the case-level lot codes on that pallet back to the customer it went to. This is the "one up, one down" traceability requirement. |
| Department | Warehouse — Shipping |
| Applies to | Warehouse Manager · Shipping Clerk · Forklift Operator |
| Owner | Warehouse Manager |
| Approved by | ______________________  *(signature required before issue)* |
| Effective date | ______________________ |
| Review cycle | Annual, or on any change to carrier requirements or scanning hardware |
| Supersedes | None — first controlled shipping procedure |
| Records generated | Pallet record with SSCC-18, order → pallet mapping, signed BOL |

---

## 1. Purpose

To load outbound orders onto pallets, uniquely label each pallet, and hand
the load to the carrier in a way that ties every case's lot code to the
customer it shipped to — so a downstream recall or shortage can be
traced to one truck, one pallet, and one customer.

## 2. Why this matters

If a case with a recalled lot leaves this building without an SSCC on
its pallet and without a matching order → pallet record in the portal,
we cannot answer "which customer got it" in the timeframe a recall
demands. Under FSMA 204 that is a reportable failure.

## 3. Responsibilities

| Who | Does what |
|---|---|
| Shipping Clerk | Verifies the pack against the order, scans cases onto the pallet, prints the SSCC pallet label |
| Forklift Operator | Moves the labeled pallet to the outbound staging area, then onto the truck under the Shipping Clerk's direction |
| Warehouse Manager | Signs the BOL, releases the truck, resolves any short-ship with customer service same day |

## 4. Materials

- Bluetooth or handheld barcode scanner
- Phone/tablet logged in to `/dashboard`
- ZD621 thermal transfer printer + 4×6 pallet label media
- Corner protectors, stretch wrap
- Paper BOL

## 5. Procedure

### 5.1 Build the pallet
1. On `/dashboard`, open the order to be shipped. Confirm status is `packed`.
2. Create a new Pallet: enter your name as **Loaded by** and the carrier if known.
3. Assign the order to the pallet.
4. For every case going on the pallet, press **Scan** and pull the trigger on the case's GS1-128 label.
    - Each scan verifies GTIN/lot/sell-by against the order line and increments the packed count.
    - A case that doesn't match the order is flagged — set it aside, do not force it onto the pallet.

### 5.2 Stack, wrap, corner-protect
5. Stack cases per the packing chart; heaviest on the bottom, no overhang.
6. Corner-protect all four corners.
7. Wrap top-to-bottom, minimum 3 revolutions, capturing the top boards and the pallet skid.

### 5.3 Generate + apply the SSCC label
8. In the Pallet view, press **Generate SSCC**. The portal returns an 18-digit SSCC and locks it to this pallet.
9. Print the pallet label on the ZD621 — 4×6 label showing:
    - `PLT-######` (internal pallet number) — human readable, big
    - GS1-128 barcode encoding `(00)` + the SSCC-18
    - Customer name and delivery city
    - Number of cases and total weight
10. Apply the label to a flat, non-seam surface, **between 16 and 32 inches from the bottom** of the pallet, at least 2 inches from any edge. Do **not** wrap the label around a corner.
11. Apply a duplicate label to an adjacent side. Two labels per pallet is required.

### 5.4 Stage
12. Move the labeled, wrapped pallet to the outbound staging lane for the correct carrier / delivery run.
13. Update the Pallet status to `staged`.

### 5.5 Load the truck
14. When the carrier arrives, verify carrier and truck number against the BOL.
15. Forklift Operator loads pallets under the Shipping Clerk's direction.
16. Shipping Clerk scans each pallet's SSCC as it goes onto the truck — this records exactly what went on this truck.
17. Update each Pallet status to `shipped` — the portal auto-stamps the shipped time.

### 5.6 Hand over
18. Warehouse Manager reviews the truck manifest against the pallets scanned onto it.
19. If everything matches: sign the BOL, hand a copy to the driver, keep the office copy.
20. If anything is short or damaged: do **not** sign until it is either corrected or noted on the BOL. The driver initials any note.

## 6. Records

| Record | Where | Retained |
|---|---|---|
| Pallet record with SSCC-18 | `/dashboard` → Pallets, and `GET /pallets` API | Minimum 2 years per FSMA 204 |
| Order → Pallet → Shipment linkage | Same | Same |
| Signed BOL | Physical file + scan in shared drive | Per retention schedule |
| Loading discrepancy note | Attached to BOL scan + Pallet notes | Per retention schedule |

## 7. If something goes wrong

| Situation | Do this |
|---|---|
| Case scan doesn't match the order | Set it aside. Do not load. Notify the Warehouse Manager. Correct the order or the case before continuing. |
| SSCC printer is down | Do **not** hand-write an SSCC. Reprint from a backup printer, or hold the load. |
| Label falls off in transit (reported later) | The carrier can pair the load by the pallet's `PLT-######` — the SSCC + PLT number both point to the same record. |
| Customer reports a short-ship | Pull the pallet by its SSCC in `/pallets` → look at what was scanned on. Cross-check to the truck manifest. Resolve same day. |
| Truck leaves with an uncorrected shortage | Not acceptable. If it happens, log it as an OOP (Out Of Procedure) event and escalate to the Warehouse Manager and Owner the same day. |

Any of the above is reported to the Warehouse Manager the same shift.

---

## Revision history

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | *(pending)* | Warehouse Manager | First controlled issue. Introduces SSCC-18 on every outbound pallet. |
