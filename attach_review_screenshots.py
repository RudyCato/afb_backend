"""
Attaches the real screenshots committed into web/review-media/ to their
matching review pages by title. Run after add_review_pages.py (needs all
17 pages to already exist) and after the screenshot files are already in
web/review-media/ (they're committed to git, not uploaded at runtime).

Two pages intentionally reuse another page's screenshot because they
aren't standalone screens in the app:
  - "Shipping & Delivery Tracking" reuses the Orders detail screenshot
    (shipment status lives on the order detail view).
  - "Barcode Scanning" reuses the Receiving screenshot (the Scan barcode
    button is a shared capability inside Receiving/Return, not its own page).

Idempotent: safe to run again — it just re-sets the filename each time.

Usage:
    python attach_review_screenshots.py
"""
from app.database import Base, SessionLocal, engine
from app.routers.review import ReviewProject, ReviewPage  # noqa: F401 — registers tables

Base.metadata.create_all(bind=engine)

SLUG = "afb-ops-review"

# title -> filename (must already exist in web/review-media/)
SCREENSHOTS = {
    "Dashboard — Overview & Alerts": "dashboard-overview.jpg",
    "Receiving — Log Inbound Product": "receiving.jpg",
    "Log a Return": "log-a-return.jpg",
    "Reports — PDF Generation & Email": "reports.jpg",
    "Pallets & Manifest": "pallets.jpg",
    "Customers": "customers.jpg",
    "Orders — List, Detail & Status": "order-detail.jpg",
    "Shipping & Delivery Tracking": "order-detail.jpg",  # reused — see module docstring
    "Packing Manager — Assignment Form": "packing-manager.jpg",
    "Packing & Production — Packer Daily Log": "packer-portal.jpg",
    "Materials & Packaging Specs": "product-mixer.jpg",
    "Stock / Inventory — Adjust, Location, History": "stock-inventory.jpg",
    "Applications Admin — External Applicants": "applications-admin.jpg",
    "Public Ordering Site": "public-site.jpg",
    "Employee (Internal) Job Application": "employee-application.jpg",
    "Staff Login & Access": "staff-login.jpg",
    "Barcode Scanning": "receiving.jpg",  # reused — see module docstring
}


def main():
    db = SessionLocal()
    try:
        proj = db.query(ReviewProject).filter(ReviewProject.slug == SLUG).first()
        if not proj:
            print(f"No project with slug '{SLUG}' found — run seed_review.py first.")
            return

        by_title = {p.title: p for p in proj.pages}
        set_count = 0
        for title, filename in SCREENSHOTS.items():
            page = by_title.get(title)
            if not page:
                print(f"Skipping (no matching page): {title}")
                continue
            page.screenshot_filename = filename
            set_count += 1
            print(f"Set screenshot for '{title}' -> {filename}")

        db.commit()
        print(f"\nDone — set screenshots on {set_count} page(s).")
        missing = [t for t in by_title if t not in SCREENSHOTS]
        if missing:
            print("Pages with no screenshot yet:", ", ".join(missing))
    finally:
        db.close()


if __name__ == "__main__":
    main()
