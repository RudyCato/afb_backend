<!-- Controlled document. The current version lives in the AFB operations
portal. A printed copy is uncontrolled once it leaves the screen. -->

# SOP-WHS-004 · Assigning &amp; Managing Product Barcodes

| Field | Value |
|---|---|
| Document code | `SOP-WHS-004` |
| Version | 1.0 |
| Status | Active — pending approval |
| Scope | **Operational + Traceability.** The barcode on a product is what every scanner in the building matches against — get this wrong and receiving, packing, and shipping all match to the wrong SKU. |
| Department | Warehouse — Inventory |
| Applies to | Warehouse Manager · Receiver · Product Owner |
| Owner | Warehouse Manager |
| Approved by | ______________________  *(signature required before issue)* |
| Effective date | ______________________ |
| Review cycle | Annual, or on any change to GS1 registration status, vendor sources, or scanning hardware |
| Supersedes | None — first controlled barcode procedure |
| Records generated | Product.barcode field on each SKU; change audit via Product update history |

---

## 1. Purpose

To ensure every Product in the AFB catalog has one — and only one — correct
barcode assigned, so that every scan in Receiving, Returns, Packing, and
Shipping reliably identifies the right SKU.

## 2. Why this matters

A wrong barcode is worse than no barcode. No barcode fails loudly — the
scanner says "unknown". A wrong barcode fails silently — the scanner
happily matches the wrong SKU, and every downstream count, order fill,
recall trace, and reorder decision is quietly corrupted. Recovering
from a silent mismatch that ran for two weeks means recounting the
whole aisle.

## 3. Responsibilities

| Who | Does what |
|---|---|
| Receiver | On any inbound case with no matching product barcode, flags to Warehouse Manager the same shift — does **not** guess. |
| Product Owner (buyer / owner of the SKU) | Decides make-vs-buy for new barcodes per §5. Records the decision. |
| Warehouse Manager | Owns this procedure. Signs off on every new barcode entry. Runs the quarterly barcode audit (§6). |

## 4. Materials

- Access to `/stock` on the AFB portal
- Physical case in hand (for reading vendor labels)
- Zebra ZD621 label printer + freezer-grade 4×2 media (for AFB-generated labels)
- GS1 US account (only for products going to retail — see §5.3)

## 5. Procedure — deciding which barcode to assign

### 5.1 Vendor case (product we buy in)
1. Pick up the physical case.
2. Find the barcode with digits printed underneath.
3. Read the digits, ignoring parentheses. Two common cases:
    - **Plain UPC/EAN** — enter the 12 or 13 digits exactly as printed.
    - **GS1-128 label** (a wide label with sections like `(01)10614141999996(10)LMR2038(17)261230`) — enter **only the digits after `(01)`**, which is the 14-digit GTIN. Do not enter the lot, expiry, or parentheses.
4. On `/stock`, find the matching SKU → **Location** → paste into **Barcode / GTIN** → **Save**.

### 5.2 Product we make, sold only inside AFB (staff scan only)
5. Make one up. The rule is only that it must be unique across the catalog.
6. Format we use: `AFB-` prefix, uppercase SKU-like short code. Example: `AFB-GRAN-CINN-8OZ`.
7. Enter on `/stock` → Location → Barcode / GTIN → Save.
8. Print a matching label on the ZD621 and apply to the case. Every case leaving the packing room needs one physical label.

### 5.3 Product we make, will ship to retail (grocery, distributor, Walmart, Sysco)
9. Retailers accept only real GS1-issued barcodes. Made-up codes will be rejected at the receiving DC.
10. Product Owner registers at **[gs1us.org](https://www.gs1us.org)** → "Get a Barcode":
    - **Single UPCs** — ~$30 each, fine for &lt; 10 SKUs.
    - **GS1 Company Prefix** — $250 setup + ~$50/year, gives a pool of 100+ barcodes to assign. Preferred once we have a real product catalog.
11. Once assigned, enter the 12-digit UPC on `/stock` → Location → Barcode / GTIN → Save.
12. Update the Render env var `COMPANY_GS1_PREFIX` to the AFB-assigned prefix so pallet SSCC labels also become retailer-scannable. (Warehouse Manager coordinates with whoever owns the Render environment.)

### 5.4 Common validation before saving
13. Re-check the digits — one wrong digit is a silent mismatch.
14. Do not save a barcode that is already assigned to another SKU. The system blocks this (409 error), and the error message names the conflicting SKU. Resolve first, then save.
15. If the vendor changes packaging and the barcode changes, treat it as a **new** barcode: update the field, do not keep the old one "just in case".

## 6. Quarterly barcode audit

Warehouse Manager runs this the first business day of each quarter.

16. Generate the Inventory Status PDF (Reports → Inventory Status → All active products).
17. Filter for rows where the Barcode column is blank. Assign these to Product Owners for source-and-set within one week.
18. For a 10% random sample of assigned barcodes: pull the physical case, re-scan, confirm the scan lands on the same SKU shown on the label.
19. Any mismatch: correct on the spot, note it, investigate whether it explains any recent shrinkage.
20. File the audit sheet in the Warehouse Manager's shared folder.

## 7. Records

| Record | Where | Retained |
|---|---|---|
| Product.barcode value per SKU | `/stock` (Location modal), `GET /products/{id}` API | Life of the SKU |
| Quarterly barcode audit sheet | Warehouse Manager's shared folder | 2 years |
| Change communication when a vendor changes their barcode | Email + note on the affected SKU | Per retention schedule |

## 8. If something goes wrong

| Situation | Do this |
|---|---|
| Scan says "unknown barcode" | Do **not** guess a SKU. Flag to Warehouse Manager. Set the barcode on the correct SKU via §5, then retry the scan. |
| Two SKUs have the same barcode | System blocks the save. Figure out which SKU the barcode legitimately belongs to. Remove from the wrong SKU (clear the field), then save on the right one. |
| Vendor changed their barcode overnight (new case design) | Update per §5.4 step 15. Note the change in the SKU. Do not keep the old barcode. |
| Made-up AFB code accidentally sent to a retailer | Rebrand under a real GS1 UPC per §5.3 before the next shipment. Notify the retailer's compliance contact. |
| Product Owner isn't sure make-vs-buy | Default to §5.2 (internal-only, made-up code). Upgrading to a real GS1 UPC later is easy; rolling back mislabeled retail cases is not. |

Any of the above is reported to the Warehouse Manager the same shift.

---

## Revision history

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | *(pending)* | Warehouse Manager | First controlled issue. Aligns to the barcode field on `/stock` and the GS1-128 scan flow in Receiving. |
