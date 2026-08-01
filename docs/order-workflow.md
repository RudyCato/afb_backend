# Order-to-Delivery Workflow (As-Is)

American Food & Beverage — current state, documented for the dev team ahead of any system work.

## 1. Order Capture — Sales
**Actor:** Sales / Customer
**Tool:** Pepperi *(channel 1)* **or** direct submission to Front Office *(channel 2)*
Order originates one of two ways: through Pepperi, or handed directly to the Front Office.

## 2. Order Entry — Front Office / Accounting
**Actor:** Front Office
**Tool:** BSC (custom accounting system)
The order is entered into BSC, which generates the **Sales Order / Pick Ticket**. BSC routes this to the Operations Manager and the Packing Room Manager.

## 3. Pick Ticket Review — Packing Room
**Actor:** Packing Room Manager
**Tool:** Sales Order / Pick Ticket (from BSC)
Reviews the pick ticket and flags any items not currently on-shelf, requesting those be pulled from the Bulk Room.

## 4. Bulk Fulfillment & Inventory Update — Operations
**Actor:** Operations Manager
**Tool:** Not specified (manual pick; inventory system unclear — see note below)
Reviews the Packing Room Manager's request, pulls the requested bulk material plus any additional bulk product needed to fulfill the order(s), updates inventory, and delivers the product to the Packing Room.

## 5. Production Assignment — Packing Room
**Actor:** Packing Room Manager
**Tool:** None specified
Assigns a Production Associate to handle the order.

## 6. Fill / Weigh / Seal / QC — Production
**Actor:** Production Associate
**Tool:** None specified
Physically fills, weighs, seals, and quality-checks containers pulled from bulk inventory.

## 7. Support & Staging — Floor
**Actor:** Production Support Worker / Floor Assistant
**Tool:** UPC labels + scanner (system unspecified)
General utility support across box building, container staging, and batch prep. Labels boxes with UPC for scanning and moves finished cases by cart to Shipping.

## 8. Palletizing — Shipping
**Actor:** Shipping
**Tool:** None specified
Palletizes the order, assigning order #, product, and box count to a pallet #.

## 9. Load-Out — Carrier Driver
**Actor:** Carrier Driver
**Tool:** Scanner / driver system (unspecified)
Reviews the Pallet Manifest and scans each pallet loaded onto the truck.

## 10. Delivery & Proof of Delivery — Carrier Driver
**Actor:** Carrier Driver
**Tool:** Same driver system
At the store: scans pallet/boxes delivered, captures signature from the store's Receiving Department, enters any payment received (e.g. COD), notes any issues, and the data updates the system.

---

## Tools referenced today

| Step | System | Status |
|---|---|---|
| Order capture | Pepperi | Named |
| Order entry / pick ticket | BSC (custom) | Named |
| Bulk pick / inventory update | — | **Not specified** |
| Production (fill/weigh/seal/QC) | — | **Not specified** |
| Labeling / staging | Scanner (UPC) | Named, system behind it unspecified |
| Palletizing | — | **Not specified** |
| Load scan, delivery scan, signature, payment, notes | Driver-facing system | Named as "the system," not identified |

## Gaps worth flagging to the dev team

- **Pepperi → BSC**: is this integrated/automatic, or does Front Office re-key the order?
- **Bulk Room → Packing**: inventory updates and the pick request/fulfillment loop appear to be manual/paper — no system of record named.
- **Packing Room → Shipping**: no system tracks the Production Associate assignment, QC checks, or palletizing.
- **"the system" the driver updates at delivery**: is this the same as BSC, or a separate app? This matters for where signature/COD/exception data ultimately lands.
