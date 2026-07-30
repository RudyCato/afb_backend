"""
Seeds the Review Portal with AFB as Project #1 — six real workflow pages
pulled straight from the live app (Receiving, Log a Return, Packing
Assignments, Employee Application, Stock/Inventory, Reports), so there's
something to send to reviewers immediately instead of starting from a
blank project.

Idempotent: if a project with slug "afb-ops-review" already exists, this
script does nothing and just prints the existing reviewer link. Safe to
run again after adding more pages by hand through /review-admin.

Usage:
    python seed_review.py
"""
import json

from app.database import Base, SessionLocal, engine
from app.routers.review import ReviewProject, ReviewPage  # noqa: F401 — import registers the tables

Base.metadata.create_all(bind=engine)

SLUG = "afb-ops-review"


def f(label, type_="text", note=None):
    return {"label": label, "type": type_, "note": note}


PAGES = [
    dict(
        title="Receiving — Log Inbound Product",
        summary="Dashboard → Receiving. Logs a delivery line from a vendor and, unless it's rejected, puts the product into stock at a shelf location.",
        fields=[
            f("Vendor / Supplier"),
            f("PO #"),
            f("Product", "select", "picked from the catalog"),
            f("Scan barcode", "button", "opens the scanner/manual-entry prompt, fills product+lot+sell-by"),
            f("Qty received", "number"),
            f("Qty expected", "number", "used to compute a discrepancy"),
            f("Temp °F", "number"),
            f("Lot code"),
            f("Sell-by date", "date"),
            f("Condition", "select", "Good / Partial damage / Damaged / Rejected — Rejected never touches inventory"),
            f("Put-away location", "section"),
            f("Warehouse"), f("Aisle"), f("Bin / Column"),
            f("Received by", "text", "required — staff name"),
            f("Notes", "textarea"),
            f("Log Receipt", "button"),
            f("Recent receipts (7 days)", "table", "When · Vendor/PO · Product · Qty · Condition"),
        ],
        flow_notes=(
            "1. Staff opens Receiving from the dashboard.\n"
            "2. Picks or scans the product, enters vendor/PO/qty/condition.\n"
            "3. On submit: a Receipt row is saved for the paper trail.\n"
            "4. If condition != Rejected, Inventory.qty_on_hand is increased and an "
            "InventoryTransaction (reason=received_stock) is written.\n"
            "5. If put-away fields were entered, they overwrite the product's stored location.\n"
            "6. Recent-receipts table refreshes to show the new line."
        ),
        downstream_notes=(
            "Feeds: /stock inventory levels, the Daily Production / Receiving PDF reports, "
            "and reorder-threshold alerts on the dashboard. Rejected receipts are logged but "
            "never change inventory, so they won't trigger a false 'restocked' signal."
        ),
    ),
    dict(
        title="Log a Return",
        summary="Dashboard → Log a Return. Records a customer return against an order or customer, and puts the product back into stock.",
        fields=[
            f("Order # or Customer", "select", "either an order number lookup or a customer picker"),
            f("Product", "select"),
            f("Scan barcode", "button"),
            f("Qty", "number"),
            f("Sell-by date", "date"),
            f("Reason", "select", "reason-code dropdown, e.g. damaged / wrong item / customer changed mind"),
            f("Notes", "textarea"),
            f("Submit Return", "button"),
        ],
        flow_notes=(
            "1. Staff selects the order/customer and product being returned.\n"
            "2. On submit: a CustomerReturn row is saved.\n"
            "3. Inventory.qty_on_hand is increased by the returned qty.\n"
            "4. An InventoryTransaction (reason=returned) is written for the audit trail."
        ),
        downstream_notes=(
            "Feeds: /stock inventory levels, inventory transaction history. Does not currently "
            "reverse the original order's line-item total — reviewers should flag if that's expected."
        ),
    ),
    dict(
        title="Packing Manager — Assignment Form",
        summary="/production. A packing manager assigns a packer to a job — either fulfilling a specific order, replenishing general inventory, or both — and can see live on-hand stock while assigning.",
        fields=[
            f("Packer", "select"),
            f("Product", "select"),
            f("Current inventory", "readout", "live qty on hand, shown red if at/below reorder threshold"),
            f("Purpose", "select", "Order / Inventory / Both"),
            f("Order # / Inventory reference", "text"),
            f("Qty to pack"),
            f("Notes"),
            f("Create Assignment", "button", "also emails the notes + purpose to the packing inbox"),
            f("Assignments table", "table", "Packer · Product · Purpose · Order ref · On-hand · Status"),
        ],
        flow_notes=(
            "1. Manager picks packer + product; current inventory loads live from the API.\n"
            "2. Manager sets Purpose (order/inventory/both) and, if order-related, an order number.\n"
            "3. On create: PackingAssignment row saved, background task emails the packing inbox.\n"
            "4. Assignment appears in the table for the packer to pick up and log against."
        ),
        downstream_notes=(
            "Feeds: packer daily logs, the packing/shipping productivity reports, and — for "
            "inventory-purpose assignments — expected replenishment once the packer logs completion."
        ),
    ),
    dict(
        title="Employee (Internal) Job Application",
        summary="Public site → 'Apply for an internal transfer'. Lets a current employee apply for a different internal role, and requires them to acknowledge the SOPs for that role before submitting.",
        fields=[
            f("Employee name"), f("Employee email"), f("Employee phone"),
            f("Current role"), f("Current department"), f("Hire date", "date"),
            f("Supervisor name"),
            f("Role applying for", "select", "populated from GET /jobs"),
            f("SOPs for this role", "section"),
            f("SOP acknowledgment checkboxes", "checkbox", "one per required SOP — all must be checked to submit"),
            f("Earliest start date", "date"),
            f("Shift preference", "select"),
            f("Reason for applying", "textarea", "minimum 20 characters, enforced client-side"),
            f("Relevant experience", "textarea"),
            f("Submit Application", "button", "emails HR + sends applicant a confirmation"),
        ],
        flow_notes=(
            "1. Employee picks a role; the SOP panel loads that role's required SOPs from the library.\n"
            "2. Employee must check every SOP acknowledgment box before Submit is enabled.\n"
            "3. On submit: EmployeeApplication row saved first (always), then best-effort emails "
            "fire to HR and the applicant — an email failure never loses the saved application.\n"
            "4. Appears on /applications-admin under the 'Internal / employee transfers' tab."
        ),
        downstream_notes=(
            "Feeds: /applications-admin internal-tab review queue, status workflow "
            "(submitted → under_review → approved/declined/withdrawn)."
        ),
    ),
    dict(
        title="Stock / Inventory — Adjust, Location, History",
        summary="/stock. The main inventory table — every product's on-hand qty, reorder threshold, shelf location, and barcode, with per-row actions.",
        fields=[
            f("Inventory table", "table", "SKU · Name · Barcode · On-hand · Reorder pt · Location · Actions"),
            f("Adjust", "button", "manual qty correction with a reason"),
            f("Location", "button", "edit warehouse/aisle/bin + barcode/GTIN"),
            f("History", "button", "full InventoryTransaction log for that product"),
        ],
        flow_notes=(
            "1. Table loads all products with current on-hand qty, color-flagging anything "
            "at/below its reorder threshold.\n"
            "2. Adjust writes an InventoryTransaction (reason=adjustment) and updates qty_on_hand.\n"
            "3. Location edits warehouse/aisle/bin, and — if the barcode field changed — PATCHes "
            "the product record directly (barcode collisions are rejected with a 409).\n"
            "4. History opens a read-only feed of every transaction that touched this product."
        ),
        downstream_notes=(
            "This is the canonical read of current stock — Receiving, Returns, Packing "
            "assignments, and Orders all write into the same Inventory/InventoryTransaction "
            "tables this page reads from."
        ),
    ),
    dict(
        title="Reports — PDF Generation & Email",
        summary="Dashboard → Reports. Generates and optionally emails PDF reports for daily production, product receiving, and inventory status.",
        fields=[
            f("Report type tabs", "section", "Daily Production / Product Receiving / Inventory Status"),
            f("Date / date range", "date"),
            f("Open PDF", "button", "opens the generated PDF in a new tab"),
            f("Recipient email"),
            f("Email PDF", "button", "generates the PDF server-side and emails it as an attachment"),
        ],
        flow_notes=(
            "1. Staff picks a report type and parameters (date/date range).\n"
            "2. Open PDF streams a reportlab-generated PDF directly.\n"
            "3. Email PDF re-generates the same PDF server-side, attaches it to an email via the "
            "shared mail helper, and sends it — failures are logged, not silently lost."
        ),
        downstream_notes=(
            "Read-only reporting layer — pulls from Production, Receipt, and Inventory tables; "
            "does not write anything back."
        ),
    ),
]


def main():
    db = SessionLocal()
    try:
        existing = db.query(ReviewProject).filter(ReviewProject.slug == SLUG).first()
        if existing:
            print(f"Project '{SLUG}' already exists (id={existing.id}). Not creating a duplicate.")
            print(f"Reviewer link: /review/{existing.token}")
            print("Add more pages any time from /review-admin.")
            return

        import secrets
        proj = ReviewProject(
            name="AFB Operations — App Review",
            slug=SLUG,
            token=secrets.token_urlsafe(20),
            owner_email="rudycato@gmail.com",
            description=(
                "Review of the AFB operations app — receiving, returns, packing assignments, "
                "employee applications, inventory, and reporting. Leave a comment on any screen: "
                "flag a bug, suggest a change, ask a question, or just approve it as-is."
            ),
        )
        db.add(proj)
        db.flush()

        for i, page in enumerate(PAGES):
            db.add(ReviewPage(
                project_id=proj.id,
                order_index=i,
                title=page["title"],
                summary=page["summary"],
                fields_json=json.dumps(page["fields"]),
                flow_notes=page["flow_notes"],
                downstream_notes=page["downstream_notes"],
            ))
        db.commit()

        print(f"Created project '{proj.name}' (id={proj.id}) with {len(PAGES)} workflow pages.")
        print(f"Reviewer link: /review/{proj.token}")
        print("Full URL once deployed: https://afb-backend-58ys.onrender.com/review/" + proj.token)
        print("Admin/triage view: /review-admin (staff login required)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
