<!-- Controlled document. The current version lives in the AFB operations
portal. A printed copy is uncontrolled once it leaves the screen. -->

# SOP-WHS-003 · Inventory Control — Counts, Adjustments, Reorder

| Field | Value |
|---|---|
| Document code | `SOP-WHS-003` |
| Version | 1.0 |
| Status | Active — pending approval |
| Scope | **Operational + FSMA 204.** Inventory accuracy is what makes lot recall, order fulfillment, and reorder decisions possible. |
| Department | Warehouse — Inventory |
| Applies to | Warehouse Manager · Receiver · Packer · Shipping Clerk |
| Owner | Warehouse Manager |
| Approved by | ______________________  *(signature required before issue)* |
| Effective date | ______________________ |
| Review cycle | Annual, or on any change to product mix, storage layout, or scanning hardware |
| Supersedes | None — first controlled inventory procedure |
| Records generated | InventoryTransaction rows (every change), cycle-count sheets, month-end reconciliation |

---

## 1. Purpose

To keep the on-hand quantity, reserved quantity, and physical location of
every product in `/stock` matching what is actually in the building, so
that orders can be packed against real availability, low stock triggers
real reorders, and recalls can find every affected unit in minutes.

## 2. Why this matters

An inventory system is only useful if it is right. A single silent
count — a case walked out for a sample, a damaged unit thrown away, a
put-away typed into the wrong bin — puts the whole system into a state
where staff stop trusting it. Once staff stop trusting it they start
counting by eye, and the point of the system is lost.

## 3. Responsibilities

| Who | Does what |
|---|---|
| Receiver | Every inbound line becomes a Receipt row. See SOP-WHS-001. |
| Shipping Clerk | Every outbound pallet is scanned to an order. See SOP-WHS-002. |
| Packer | Every packed unit is logged via the Packer Portal — this is what moves stock out of raw and into finished. |
| Any staff removing units for damage, sample, or destruction | Enters an Adjustment on `/stock` with reason = Removed. |
| Any staff putting units back for return-to-stock | Enters an Adjustment with reason = Returned, or uses Log a Return on `/dashboard`. |
| Warehouse Manager | Runs the weekly cycle-count schedule, resolves variances, owns the accuracy KPI |

## 4. Materials

- Bluetooth or handheld barcode scanner
- Phone/tablet on `/stock`
- Printed cycle-count sheet from the Inventory Status PDF (Reports → Inventory Status)
- Pen

## 5. Procedure

### 5.1 Golden rules
1. **Every physical movement generates an entry.** Never move product without a corresponding portal entry. If the portal is down, use the paper offline sheet and enter within 4 hours.
2. **The reason matters as much as the number.** `Removed`, `Returned`, `Manual adjustment`, `Received stock`, `Production completed` are not interchangeable. Recall investigations read the reason.
3. **Location is data.** Warehouse, aisle, bin. Updating location on `/stock` is a two-tap job; not doing it is why the pick face is empty when the pick sheet says it's full.

### 5.2 Every-shift habits
4. Receivers, packers, shippers all follow their own SOP — inventory correctness is a side effect of following those SOPs, not a separate step.
5. Anything removed for damage, sample, waste, or destruction: open `/stock` → **Adjust** → reason `Removed` → enter qty (always subtracts, regardless of sign) → note what happened.
6. Anything returning to stock outside a customer return (e.g. cancelled pull that came back): reason `Returned` → enter qty (always adds) → note the source.

### 5.3 Weekly cycle counts
7. Warehouse Manager generates the Inventory Status PDF (Reports → Inventory Status) for a slice of the catalog — one aisle, one product category, or all low-stock items.
8. Assigns a counter (not the Receiver who put the product away).
9. Counter walks the aisle, ticks physical count next to system count on the printout.
10. Any variance ≥ 1 unit: counter recounts. If still variant, note it on the sheet.
11. Counter returns the sheet to the Warehouse Manager.
12. Warehouse Manager investigates every variance — usually a missed removal, a mis-scan, or a wrong put-away — and enters an Adjustment with reason `Manual adjustment` and a note explaining the source of the variance.
13. Signed cycle-count sheet is filed.

### 5.4 Reorder points
14. Every product's **Min qty** (reorder threshold) is set on `/stock` → Location. Set it high enough that the next inbound receipt arrives before stock hits zero — never at zero.
15. When on-hand ≤ reorder threshold, `/stock` shows the row as `REORDER` (rust color).
16. Warehouse Manager reviews the "REORDER" list at least weekly and initiates POs.

### 5.5 Month-end reconciliation
17. Warehouse Manager runs the Inventory Status PDF for the full catalog on the last business day of the month.
18. Runs the Product Receiving PDF for the month.
19. Runs the Daily Production PDF summed across the month (or exports the raw log).
20. Reconciles: `opening + received + produced - shipped - removed +/- adjustments = closing`.
21. Discrepancies > 1% of any SKU trigger a full recount of that SKU.

## 6. Records

| Record | Where | Retained |
|---|---|---|
| InventoryTransaction rows | Auto — every Receipt / Return / Adjustment / order shipment writes one; visible via each product's History button | Minimum 2 years per FSMA 204 |
| Cycle-count sheets | Physical file (signed) + scan | Per retention schedule |
| Month-end reconciliation | Warehouse Manager's shared folder | Per retention schedule |

## 7. If something goes wrong

| Situation | Do this |
|---|---|
| System qty is wrong and you can't figure out why | Adjust to physical — reason `Manual adjustment`, note "unable to trace source". Flag to Warehouse Manager same day for investigation. |
| Product found in a location the system doesn't know about | Update the Location on `/stock` before doing anything else. Then re-count. |
| Reorder threshold is set to zero | It shouldn't be. Warehouse Manager sets a real min qty. |
| Two staff working on the same aisle at the same time | Stop. One person owns an aisle for the duration of a count. |
| Portal is offline | Paper offline sheet. Enter within 4 hours. **Never** batch-enter a whole day of activity at end-of-shift. |

Any of the above is reported to the Warehouse Manager the same shift.

---

## Revision history

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | *(pending)* | Warehouse Manager | First controlled issue. Ties inventory-control practice to the `/stock` and Reports flows and to FSMA 204 KDE retention. |
