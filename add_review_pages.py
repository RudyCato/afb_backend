"""
Adds the REST of the app's screens to the AFB Operations review project —
the first pass (seed_review.py) only covered 6 core workflows. This adds
the rest: dashboard overview, orders, customers, shipping, pallets,
packer daily log, materials/packaging specs, login & access, the external
applications admin view, the public ordering site, and barcode scanning.

Idempotent per page: skips any page whose title already exists on the
project, so it's safe to run again after adding pages by hand too.

Usage:
    python add_review_pages.py
"""
import json

from app.database import Base, SessionLocal, engine
from app.routers.review import ReviewProject, ReviewPage  # noqa: F401 — registers tables

Base.metadata.create_all(bind=engine)

SLUG = "afb-ops-review"


def f(label, type_="text", note=None):
    return {"label": label, "type": type_, "note": note}


PAGES = [
    dict(
        title="Dashboard — Overview & Alerts",
        summary="/dashboard. Landing page for staff — KPI summary, low-stock and exception alerts, and quick-action cards into every other workflow.",
        fields=[
            f("KPI cards", "readout", "Open orders (clickable), low-stock count, pending shipments, today's receipts"),
            f("Alerts feed", "table", "Low stock, on-hold orders, shipment exceptions — flagged critical vs. normal"),
            f("Quick action cards", "section"),
            f("Log a Return", "button"),
            f("Receiving", "button"),
            f("Packing & Production", "button"),
            f("Pallets", "button"),
            f("Reports", "button"),
            f("Inventory preview table", "table", "SKU · Name · Barcode · On-hand · Location · Actions"),
            f("Production/shipping charts", "readout"),
        ],
        flow_notes=(
            "1. Staff logs in and lands here by default.\n"
            "2. KPI cards and alerts load from live data on page load.\n"
            "3. Clicking a KPI or quick-action card opens the relevant modal or page "
            "(Open Orders, Log Return, Receiving, Reports, etc.) without navigating away.\n"
            "4. Inventory table and alerts refresh on manual refresh or after any modal submit."
        ),
        downstream_notes=(
            "Reads from every other domain — Orders, Inventory, Receipts, Shipments — but "
            "writes nothing itself except through the modals it opens."
        ),
    ),
    dict(
        title="Orders — List, Detail & Status",
        summary="Order lifecycle management — every order from received through delivered, plus the granular picking/packaging/labeling/boxing tasks under each one.",
        fields=[
            f("Order list", "table", "Order # · Customer · Status · Total · Created"),
            f("Status filter", "select"),
            f("Order detail", "section"),
            f("Line items", "table", "Product · Qty · Price"),
            f("Customer info", "readout"),
            f("Status", "select", "received / confirmed / on_hold / picking / packing / packed / out_for_delivery / delivered / cancelled"),
            f("Order tasks", "table", "Picking · Packaging · Labeling · Boxing — each independently assignable and timed"),
            f("Assign task to staff", "select"),
            f("Notes"),
            f("Update Order", "button"),
        ],
        flow_notes=(
            "1. Staff opens an order from the list or via the dashboard's Open Orders KPI.\n"
            "2. Status changes move the order through its lifecycle; each status change is "
            "an open write with no approval step currently.\n"
            "3. Order tasks can be assigned and timed independently of the overall order status, "
            "so multiple staff can work different steps of the same order in parallel."
        ),
        downstream_notes=(
            "Feeds: packing assignments, shipping, cycle-time reports, and inventory reservation "
            "(order_reserved / order_released / order_shipped transaction reasons)."
        ),
    ),
    dict(
        title="Customers",
        summary="Customer records — contact info, account type (retail/wholesale), and order history.",
        fields=[
            f("Customer list", "table", "Name · Contact · Type · Orders"),
            f("Add / Edit customer", "section"),
            f("Name"), f("Email"), f("Phone"), f("Address", "textarea"),
            f("Customer type", "select", "retail / wholesale — affects site pricing mode"),
            f("Order history", "table", "per-customer past orders"),
            f("Save Customer", "button"),
        ],
        flow_notes=(
            "1. Staff searches or adds a customer.\n"
            "2. Customer type determines which pricing/ordering mode they see on the public site.\n"
            "3. Order history pulls live from the Orders table filtered by customer."
        ),
        downstream_notes="Feeds: Orders (customer picker), Returns (customer picker), public site checkout.",
    ),
    dict(
        title="Shipping & Delivery Tracking",
        summary="Tracks shipments from staged/loaded through delivered, including exceptions.",
        fields=[
            f("Shipment list", "table", "Order # · Status · Carrier · Tracking #"),
            f("Status", "select", "pending / in_transit / delivered / exception"),
            f("Carrier"), f("Tracking #"),
            f("Delivery confirmation", "button"),
            f("Exception notes", "textarea"),
        ],
        flow_notes=(
            "1. Order reaches 'packed' status and a shipment record is created.\n"
            "2. Staff updates status as the shipment moves; 'exception' captures anything "
            "gone wrong (damaged, refused, lost) with notes.\n"
            "3. Delivery confirmation closes out the shipment and, via the order, marks it delivered."
        ),
        downstream_notes="Feeds: order status, shipping/packing productivity reports.",
    ),
    dict(
        title="Pallets & Manifest",
        summary="Builds outbound pallets, wraps/labels them, generates an SSCC (GS1 pallet serial code), and stages them for loading with a bill of lading.",
        fields=[
            f("Pallet list", "table", "Pallet ID · SSCC · Status · Contents"),
            f("Build pallet", "button", "adds orders/boxes to a new pallet"),
            f("Generate SSCC", "button", "idempotent — assigns a GS1 mod-10-checked serial code"),
            f("Wrap & label", "button"),
            f("Stage for loading", "button"),
            f("Manifest / BOL", "table", "readout of everything on the pallet, printable"),
        ],
        flow_notes=(
            "1. Staff builds a pallet from ready orders/boxes.\n"
            "2. SSCC is generated once per pallet (calling it again on an already-assigned "
            "pallet is a no-op, not a new code).\n"
            "3. Pallet is wrapped, labeled with the SSCC barcode, and staged.\n"
            "4. Manifest/BOL is generated for the driver at load time."
        ),
        downstream_notes="Feeds: Shipping (pallet → shipment), barcode scanning at load-out.",
    ),
    dict(
        title="Packing & Production — Packer Daily Log",
        summary="/production, packer-facing tab. A packer works an assignment from the packing manager, logs quantity packed and time, and marks it complete.",
        fields=[
            f("My assignment", "readout", "packer's currently assigned job — product, purpose, order ref, qty"),
            f("Qty packed", "number"),
            f("Start / end time", "readout", "captured automatically, not manually entered"),
            f("Mark Complete", "button"),
            f("Daily log table", "table", "Packer · Product · Qty · Start · End · Status — for the manager to review"),
        ],
        flow_notes=(
            "1. Packer sees their current assignment (created by the Packing Manager form).\n"
            "2. Logs quantity as they pack; marks complete when done.\n"
            "3. Completion updates the assignment status and, for inventory-purpose "
            "assignments, feeds expected replenishment."
        ),
        downstream_notes="Feeds: packing productivity reports, inventory (for inventory-purpose jobs).",
    ),
    dict(
        title="Materials & Packaging Specs",
        summary="/production, materials tab. Indirect-material specs (containers/lids/boxes per packing job) and recipe/mix breakdowns for blended products like granola.",
        fields=[
            f("Product", "select"),
            f("Packaging spec", "table", "Containers · Lids · Boxes needed per case run"),
            f("Mix / recipe breakdown", "table", "Cases → lbs of each raw ingredient"),
            f("Preview materials needed", "button", "shown live on the Packing Manager assignment form"),
        ],
        flow_notes=(
            "1. Manager or packer previews materials before starting a job.\n"
            "2. Packaging spec answers 'how many containers/lids/boxes do I need.'\n"
            "3. Mix breakdown answers 'how many lbs of each ingredient for this many cases' "
            "for blended products."
        ),
        downstream_notes="Feeds: the live materials preview on the Packing Manager Assignment Form.",
    ),
    dict(
        title="Staff Login & Access",
        summary="Staff authentication — login, forced/optional password change, and role-based access (no per-endpoint authorization yet, see note).",
        fields=[
            f("Username"), f("Password"),
            f("Log In", "button"),
            f("Current password"), f("New password"), f("Confirm new password"),
            f("Change Password", "button"),
            f("Staff role", "readout", "admin / warehouse manager / etc. — shown, not editable here"),
            f("Log Out", "button"),
        ],
        flow_notes=(
            "1. Staff logs in with username/password; session cookie set for 12 hours.\n"
            "2. New accounts (or admin resets) may be flagged must_change_password, forcing "
            "a password change before continuing.\n"
            "3. Role is assigned by an admin elsewhere — this page only displays it."
        ),
        downstream_notes=(
            "IMPORTANT: there is currently no per-endpoint authorization by role — every "
            "write endpoint (status changes, packing, shipping, applications review) is open "
            "to any logged-in staff account. This is a known, accepted gap for the pilot "
            "stage — reviewers should flag if that's no longer acceptable."
        ),
    ),
    dict(
        title="Applications Admin — External Applicants",
        summary="/applications-admin, external tab. Staff review external job applications submitted through the public careers page.",
        fields=[
            f("Tab switcher", "section", "External applicants / Internal transfers"),
            f("Applicant list", "table", "Name · Role · Status · Submitted"),
            f("Status", "select", "submitted / under_review / approved / declined / withdrawn"),
            f("Notes", "textarea"),
            f("Resume", "button", "download attached resume"),
        ],
        flow_notes=(
            "1. External applicant submits via the public careers page; email optionally "
            "fires to the hiring inbox with the resume attached (MAIL_ENABLED-gated).\n"
            "2. Staff reviews here, updates status and notes.\n"
            "3. A send failure never loses the stored application — logged, not raised."
        ),
        downstream_notes="Separate data + status workflow from Internal/employee transfer applications (see that page).",
    ),
    dict(
        title="Public Ordering Site",
        summary="afb-site/, mounted at /store — the customer-facing marketing and ordering site, retail and wholesale modes.",
        fields=[
            f("Product catalog", "table", "browse by category, retail or wholesale pricing depending on customer type"),
            f("Add to cart", "button"),
            f("Checkout", "section"),
            f("Name"), f("Email"), f("Address", "textarea"), f("Order notes", "textarea"),
            f("Place Order", "button"),
            f("Careers page", "section", "job list, pulled from jobs.json"),
            f("Apply for a job", "button"),
            f("Apply for internal transfer", "button", "employees only — links to the internal application form"),
        ],
        flow_notes=(
            "1. Visitor browses the catalog; pricing/mode depends on retail vs. wholesale.\n"
            "2. Checkout creates a new Order (status=received).\n"
            "3. Careers page lists open roles; applying goes through the external application flow.\n"
            "4. A separate link lets current employees apply for an internal transfer instead."
        ),
        downstream_notes="Feeds: Orders (new order creation), Applications (external hires).",
    ),
    dict(
        title="Barcode Scanning",
        summary="GS1-128 barcode scan-to-fill, used inside Receiving and Log-a-Return, plus SSCC generation at pallet close.",
        fields=[
            f("Scan barcode", "button", "opens a scan/manual-entry prompt from Receiving or Return"),
            f("Manual entry fallback", "text", "hand-type a barcode if the scanner isn't available"),
            f("Decoded fields", "readout", "GTIN/product match, lot code, sell-by date — auto-fills the form"),
            f("SSCC on pallet close", "readout", "GS1 mod-10-checked pallet serial code, generated once per pallet"),
        ],
        flow_notes=(
            "1. Staff scans (or types) a GS1-128 barcode from a case or pallet label.\n"
            "2. The app decodes Application Identifiers (00=SSCC, 01=GTIN, 10=lot, 11/13/15/17=dates) "
            "and looks up the matching product by GTIN-14/EAN-13/UPC-A.\n"
            "3. Matched fields auto-fill the Receiving or Return form — product, lot, sell-by.\n"
            "4. On pallet close, a new SSCC is generated and printed for the outbound label."
        ),
        downstream_notes="Feeds: Receiving, Returns, Pallets — this isn't a screen of its own so much as a shared capability used inside those three.",
    ),
]


def main():
    db = SessionLocal()
    try:
        proj = db.query(ReviewProject).filter(ReviewProject.slug == SLUG).first()
        if not proj:
            print(f"No project with slug '{SLUG}' found — run seed_review.py first.")
            return

        existing_titles = {p.title for p in proj.pages}
        next_index = max([p.order_index or 0 for p in proj.pages], default=-1) + 1

        added = 0
        for page in PAGES:
            if page["title"] in existing_titles:
                print(f"Skipping (already exists): {page['title']}")
                continue
            db.add(ReviewPage(
                project_id=proj.id,
                order_index=next_index,
                title=page["title"],
                summary=page["summary"],
                fields_json=json.dumps(page["fields"]),
                flow_notes=page["flow_notes"],
                downstream_notes=page["downstream_notes"],
            ))
            next_index += 1
            added += 1
            print(f"Added: {page['title']}")

        db.commit()
        print(f"\nDone — added {added} new page(s). Project now has {len(existing_titles) + added} total.")
        print(f"Reviewer link: /review/{proj.token}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
