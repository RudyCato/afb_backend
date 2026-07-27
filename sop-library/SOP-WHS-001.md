<!-- Controlled document. The current version lives in the AFB operations
portal. A printed copy is uncontrolled once it leaves the screen. -->

# SOP-WHS-001 · Receiving Inbound Product

| Field | Value |
|---|---|
| Document code | `SOP-WHS-001` |
| Version | 1.0 |
| Status | Active — pending approval |
| Scope | **SQF + FSMA 204.** This is a food safety and traceability control. Every field is required for a lot recall to work; omitting one breaks the chain. |
| Department | Warehouse — Receiving |
| Applies to | Warehouse Manager · Receiver · Forklift Operator |
| Owner | Warehouse Manager |
| Approved by | ______________________  *(signature required before issue)* |
| Effective date | ______________________ |
| Review cycle | Annual, or on any change to vendors, product mix, or scanning hardware |
| Supersedes | None — first controlled receiving procedure |
| Records generated | Receipt entry in the operations portal (one per line item), scanned BOL photo where available |

---

## 1. Purpose

To move inbound product from the truck into inventory in a way that captures
enough information to trace any lot forward in a recall, catch shortages and
damage before the driver leaves, and land the physical goods in the correct
put-away location the first time.

## 2. Why this matters

Under **FDA FSMA 204** (compliance deadline **July 20, 2028**), every case
of covered food we handle must carry a Traceability Lot Code that we
capture at receipt and preserve through every downstream movement. A
missed lot code, a mistyped sell-by date, or a receipt logged after the
driver has left with an unresolved shortage is not a paperwork problem —
it is a compliance failure and, in a recall, a public health failure.

## 3. Responsibilities

| Who | Does what |
|---|---|
| Receiver | Physically checks the delivery, scans / enters every line, records condition, put-away location, and their own name |
| Forklift Operator | Puts product in the location on the receipt; if it will not fit there, they flag the Warehouse Manager before moving it |
| Warehouse Manager | Verifies rejections, resolves discrepancies with the vendor the same day, signs the paper BOL |

## 4. Materials

- Bluetooth or handheld barcode scanner (see AFB-TRN-BC-001 for setup)
- Phone or tablet, logged in to `/dashboard` on the AFB portal
- Thermal label printer + freezer-grade 4×2 label media (only used when a vendor case has no scannable barcode)
- Digital thermometer (for cold-chain items)
- Camera phone (for damage / seal photos)
- Paper BOL / packing slip from the driver

## 5. Procedure

### 5.1 Before the truck backs in
1. Look up the expected shipment on the portal; note the PO # if one exists.
2. Confirm dock, staging space, and put-away destinations are clear.
3. Confirm scanner is charged and paired to the receiving phone/tablet.

### 5.2 Truck arrival — check-in
4. Verify carrier, driver name, truck seal number (if sealed) against the BOL.
5. **Do not break a broken or missing seal.** Photograph, call the Warehouse Manager, wait.
6. For cold-chain loads: read trailer temperature and note it on the BOL and in the Receiving form (`Notes`).

### 5.3 Log each line — one line at a time
7. In the Receiving modal on `/dashboard`, press **Scan barcode**.
8. Pull the scanner trigger on the vendor case label.
    - If the label is GS1-128, product, lot code, and sell-by/expiration fill automatically.
    - If nothing fills, print an internal AFB label on the ZD621 and scan that instead.
9. Enter **Qty received**. If a PO qty was expected, enter **Qty expected** — the discrepancy appears in the receipts table.
10. Enter **Vendor** and **PO # / Invoice #** if not already filled.
11. Set **Condition on arrival** honestly. Options:
    - **Good** — no visible damage.
    - **Partial damage** — accepted, with damaged units counted in notes.
    - **Damaged** — accepted with reservation. Photograph and note.
    - **Rejected** — refused. The receipt is still logged for the paper trail; inventory is **not** increased.
12. For cold-chain: record **Temp (°F)** at the case, not just the trailer.
13. Enter the **Put-away location** — warehouse, aisle, bin — before you press save. If you save with the wrong location, `/stock` is wrong.
14. Enter **Received by** — your legal name, not a nickname.
15. Save. Repeat 7–14 for every line on the load.

### 5.4 Discrepancies and damage
16. Any discrepancy, any damage, any rejection: notify the Warehouse Manager **before the driver leaves**.
17. Photograph damage from at least two angles. Add photos to the notes field.
18. Warehouse Manager annotates the paper BOL, has the driver initial the annotation.

### 5.5 Put-away
19. Forklift Operator moves product to the location recorded on the receipt.
20. If the location will not hold the product (overflow, wrong pallet size, allergen segregation): stop, tell the Receiver, get the receipt's put-away location updated first, then move.

### 5.6 Close the receipt
21. Confirm every line on the BOL has a matching receipt in the portal.
22. Warehouse Manager signs the paper BOL and files it (or photographs it into the shared folder).
23. Any open discrepancy: create a follow-up note to the vendor the same day, cc: Warehouse Manager.

## 6. Records

| Record | Where | Retained |
|---|---|---|
| Receipt row (one per line item) | `/dashboard` → Receiving → recent receipts table + `GET /receipts` API | Minimum 2 years per FSMA 204 |
| Signed BOL / packing slip | Physical file + scanned copy in shared drive | Per retention schedule |
| Damage / seal photos | Attached to receipt notes, or shared drive | Per retention schedule |
| Discrepancy communication to vendor | Email, filed under vendor | Per retention schedule |

Records are entered as the work is done, not reconstructed at the end of a shift.

## 7. If something goes wrong

| Situation | Do this |
|---|---|
| Vendor case has no barcode | Print an internal AFB label on the ZD621, scan that, note in receipt notes. |
| Barcode scans but no product match | The vendor's GTIN is not linked to a Product in our catalog. Save the product, set its Barcode field, retry. |
| Sell-by date on label looks wrong | Enter what the label says, note the discrepancy, escalate to Warehouse Manager same day. |
| Load arrives out-of-temp (cold-chain) | Do not accept until Warehouse Manager approves. Photograph. Rejected shipments still get a receipt row with condition = rejected. |
| Portal is offline | Log receipts on paper using the offline receipt sheet; enter into portal within 4 hours. Do **not** delay put-away. |
| Wrong put-away recorded after save | Correct it via `/stock` → Adjust → set new location. Notes: "corrected from receipt #NNN". |

Any of the above is reported to the Warehouse Manager the same shift.

---

## Revision history

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | *(pending)* | Warehouse Manager | First controlled issue. Aligned to FSMA 204 KDE requirements and to the /dashboard Receiving flow with barcode scan. |
