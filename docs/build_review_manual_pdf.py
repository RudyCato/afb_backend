"""
Builds `AFB-App-Review-Manual.pdf` — a step-by-step walkthrough of every
screen and form in the AFB portal, for stakeholders reviewing the app.

Run:
    python docs/build_review_manual_pdf.py

Emits `docs/AFB-App-Review-Manual.pdf`.
"""
from __future__ import annotations

import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    ListFlowable, ListItem,
)

INK = colors.HexColor("#241A10")
CREAM = colors.HexColor("#FBF6E9")
RUST = colors.HexColor("#a3402a")
OLIVE = colors.HexColor("#4f5c3a")
LINE = colors.HexColor("#d8c79a")
GOLD = colors.HexColor("#c2932f")

_styles = getSampleStyleSheet()

TITLE = ParagraphStyle("title", parent=_styles["Heading1"], textColor=INK,
                       fontName="Helvetica-Bold", fontSize=22, leading=26, spaceAfter=6)
SUBTITLE = ParagraphStyle("subtitle", parent=_styles["Heading2"], textColor=OLIVE,
                          fontName="Helvetica", fontSize=12, leading=16, spaceAfter=14)
SECTION = ParagraphStyle("section", parent=_styles["Heading1"], textColor=INK,
                         fontName="Helvetica-Bold", fontSize=16, leading=20,
                         spaceBefore=18, spaceAfter=8, borderColor=RUST, borderWidth=0,
                         borderPadding=0, keepWithNext=True)
H2 = ParagraphStyle("h2", parent=_styles["Heading2"], textColor=INK,
                    fontName="Helvetica-Bold", fontSize=12, leading=15,
                    spaceBefore=10, spaceAfter=4, keepWithNext=True)
BODY = ParagraphStyle("body", parent=_styles["BodyText"], textColor=INK,
                      fontName="Helvetica", fontSize=10, leading=13.5, spaceAfter=4)
CODE = ParagraphStyle("code", parent=BODY, fontName="Courier", fontSize=9,
                      leading=12, textColor=INK, leftIndent=8, spaceAfter=6,
                      backColor=colors.HexColor("#F7F1DE"))
CALLOUT = ParagraphStyle("callout", parent=BODY, textColor=RUST,
                         fontName="Helvetica-Bold", fontSize=10, leading=13,
                         spaceAfter=6)
META = ParagraphStyle("meta", parent=_styles["BodyText"], textColor=OLIVE,
                      fontName="Helvetica-Oblique", fontSize=8, leading=11)
TOC_ROW = ParagraphStyle("toc", parent=BODY, fontSize=10, leading=15, spaceAfter=2)


def _table_style() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("TEXTCOLOR", (0, 0), (-1, 0), CREAM),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F1DE")]),
        ("GRID", (0, 0), (-1, -1), 0.25, LINE),
    ])


def _bullets(items):
    return ListFlowable(
        [ListItem(Paragraph(t, BODY), leftIndent=10, bulletColor=RUST) for t in items],
        bulletType="bullet", start="•", leftIndent=14,
    )


def _footer(canvas_, doc):
    canvas_.saveState()
    canvas_.setFont("Helvetica-Oblique", 7)
    canvas_.setFillColor(OLIVE)
    canvas_.drawString(0.5 * inch, 0.35 * inch, "American Food & Beverage — App Review Manual")
    canvas_.drawRightString(doc.pagesize[0] - 0.5 * inch, 0.35 * inch, f"Page {doc.page}")
    canvas_.restoreState()


def _section(story, num, title):
    story.append(PageBreak())
    story.append(Paragraph(f"{num}. {title}", SECTION))


def _screen_block(story, url_path, what_you_see, what_to_test):
    tbl = Table(
        [
            ["URL", Paragraph(f'<font face="Courier">{url_path}</font>', BODY)],
            ["What you see", Paragraph(what_you_see, BODY)],
            ["What to test", Paragraph(what_to_test, BODY)],
        ],
        colWidths=[1.1 * inch, 5.8 * inch],
    )
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F7F1DE")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.25, LINE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 8))


def build(out_path: str):
    doc = SimpleDocTemplate(
        out_path, pagesize=LETTER,
        leftMargin=0.6 * inch, rightMargin=0.6 * inch,
        topMargin=0.6 * inch, bottomMargin=0.7 * inch,
        title="AFB App Review Manual",
    )
    story = []
    BASE = "https://afb-backend-58ys.onrender.com"

    # ---------- Cover
    story.append(Paragraph("American Food &amp; Beverage", META))
    story.append(Paragraph("App Review Manual", TITLE))
    story.append(Paragraph("A screen-by-screen walkthrough of every page and form in the operations portal. Written for stakeholders reviewing the pilot before general rollout.", SUBTITLE))
    story.append(Paragraph(f"Version 1.0 · Prepared {datetime.now().strftime('%B %Y')}", META))
    story.append(Spacer(1, 20))

    story.append(Paragraph("How to use this manual", H2))
    story.append(Paragraph(
        "Open the app in one window and this manual in another. Each section covers one screen. "
        "Every screen block shows the URL, what you should see when you land, and a short list of "
        "things to click or type to verify the screen behaves. Take notes in the margins — the "
        "final section is a review checklist you can hand back with your feedback.", BODY))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        f"Live URL: <font face=\"Courier\">{BASE}</font>", BODY))
    story.append(Paragraph(
        "First-time login: <b>rudy</b> / <b>afb2026</b> — you will be forced to change the password immediately. "
        "Do that first; all subsequent screens require an authenticated session.", CALLOUT))
    story.append(Spacer(1, 12))

    # ---------- TOC
    story.append(Paragraph("Table of contents", H2))
    toc = [
        "1. Getting in — login &amp; forced password change",
        "2. Home &amp; operations landing",
        "3. Dashboard tour — KPIs, alerts, charts",
        "4. Orders — the single tracking entry point",
        "5. Customers",
        "6. Log a return",
        "7. Receiving inbound product",
        "8. Packing &amp; production",
        "9. Pallets &amp; shipping manifest",
        "10. Staff assignment board",
        "11. Reports (print / email PDF)",
        "12. Stock / inventory page",
        "13. Barcode scanning — where and how",
        "14. Applications admin",
        "15. Public marketing &amp; ordering site",
        "16. Change password &amp; logout",
        "17. Reviewer checklist &amp; sign-off",
    ]
    for row in toc:
        story.append(Paragraph(row, TOC_ROW))

    # ---------- 1. Login
    _section(story, 1, "Getting in — login &amp; forced password change")
    _screen_block(story, f"{BASE}/login",
        "A simple login card centered on the AFB brand background. Username and password fields. Submit button.",
        "Type <b>rudy</b> and <b>afb2026</b>. Click Sign in. You should be redirected to a Change Password screen the very first time — the app forces this before letting you into anything else."
    )
    _screen_block(story, f"{BASE}/change-password",
        "Two password fields (new + confirm) and a Save button. A short explanation of the password rules.",
        "Set a real password. On save, you land on the dashboard. Log out (top-right link) and log back in with your new password to confirm it stuck."
    )

    # ---------- 2. Home / Ops landing
    _section(story, 2, "Home &amp; operations landing")
    _screen_block(story, f"{BASE}/",
        "The AFB home page — brand hero, product overview, links to the public store and to Careers.",
        "Confirm images render, the store link goes to <font face=\"Courier\">/store</font>, and no console errors."
    )
    _screen_block(story, f"{BASE}/ops",
        "A plain internal-links page — every operations URL in one list. Handy when the domain isn't bookmarked yet.",
        "Click each link and confirm it reaches the expected page (with a login prompt if you aren't authenticated)."
    )

    # ---------- 3. Dashboard tour
    _section(story, 3, "Dashboard tour — KPIs, alerts, charts")
    _screen_block(story, f"{BASE}/dashboard",
        "The operations hub. Six KPI cards at the top (Customers, Products, Open orders, Delivered, This week, Low stock). An alerts banner above them if anything needs attention. Two charts side-by-side (Orders by status doughnut + Average hours between stages bar). A grid of drill-in cards below (Customers, Log a Return, Packing &amp; Production, Receiving, Pallets, Staff Assignment Board, Reports). Below that, the Backups panel (admin only) and a collapsible full inventory list.",
        "1. Click the <b>Open orders</b> KPI — it should open the Orders modal (this is the single order-tracking entry point). 2. Confirm the alerts banner reads either &#8220;All clear&#8221; or lists real issues. 3. Click each drill-in card; each opens a modal. 4. Click the <b>+ View full product &amp; inventory list</b> toggle at the bottom — the inventory table should slide open."
    )
    story.append(Paragraph("The Alerts banner", H2))
    story.append(Paragraph("A rust-colored banner above the KPIs when something needs attention (low stock at zero, overdue orders, backup failed, etc.). Hidden when everything is fine, replaced with a green &#8220;All clear&#8221; row.", BODY))
    story.append(Paragraph("The KPI row", H2))
    story.append(Paragraph("Six numbers at a glance. Only <b>Open orders</b> is clickable — a small arrow next to the number tells you so. <b>Low stock</b> turns rust-red when the count is above zero.", BODY))
    story.append(Paragraph("The two charts", H2))
    story.append(_bullets([
        "<b>Orders by status</b> — doughnut showing the current split of orders across received / confirmed / packing / delivered / etc.",
        "<b>Average hours between stages</b> — bar chart of how long orders sit at each stage transition. Below it, the total received&#8594;delivered average across completed orders.",
    ]))

    # ---------- 4. Orders
    _section(story, 4, "Orders — the single tracking entry point")
    _screen_block(story, f"{BASE}/dashboard (Open orders KPI)",
        "A modal with a status filter dropdown at the top (defaults to &#8220;Open orders only&#8221;) and a table of orders — order #, customer, status, placed date, pallet number.",
        "Change the filter to &#8220;All orders&#8221; and confirm the list grows. Click any order row to open the Order Detail modal."
    )
    _screen_block(story, "Order Detail modal",
        "Header shows the order number, customer, current status, pallet, and packer. Below that, an action row (Receive/Confirm, Put On Hold, Release to Warehouse, Cancel). Below that, Order Tasks (Picking, Raw Material Packaging, Labeling, Boxing) — each can be assigned to a staff member, started, completed, or reassigned. Then a Timeline of every status change and an Items table.",
        "1. On a <b>received</b> order, click Release to Warehouse — the availability check should appear inline. 2. Assign a picker and confirm — status flips to <b>picking</b> and a picking task appears with the assignee. 3. Try Start on the task, then Complete. 4. Watch the Timeline update in real time."
    )

    # ---------- 5. Customers
    _section(story, 5, "Customers")
    _screen_block(story, "Dashboard &#8594; Customers card",
        "Modal listing every customer with order count, total cases, and last order date. Click a row for the detail modal.",
        "Confirm the count of customers matches the KPI. Click a customer &#8594; detail modal should show contact info, address, and full order history with clickable order rows."
    )

    # ---------- 6. Log Return
    _section(story, 6, "Log a return")
    _screen_block(story, "Dashboard &#8594; Log a Return card",
        "Modal with a form: Order # (text, optional) OR Customer (dropdown, optional), Product (dropdown), Qty, Sell-by date, Reason dropdown (Damaged / Expired / Wrong item / Quality issue / Customer refused / Overshipment / Other), Notes. At top there is also a <b>Scan barcode</b> button that fills the product + sell-by from a GS1-128 scan.",
        "1. Pick a product, qty 1, reason Damaged, save. 2. Open <font face=\"Courier\">/stock</font>, find that product, click History — you should see a &#8220;Returned&#8221; transaction with a positive quantity. On-hand should have gone up by 1."
    )

    # ---------- 7. Receiving
    _section(story, 7, "Receiving inbound product")
    _screen_block(story, "Dashboard &#8594; Receiving card",
        "Modal with the full receipt form: Vendor, PO #, Product (with Scan button), Qty received, Qty expected (optional, for discrepancies), Temp °F (optional), Lot code, Sell-by/Best-by, Condition dropdown (Good / Partial damage / Damaged / Rejected), Put-away Warehouse/Aisle/Bin, Received by, Notes. Below the form, a &#8220;Recent receipts (last 7 days)&#8221; table.",
        "1. Log a receipt with Good condition and a put-away location — on save, <font face=\"Courier\">/stock</font> for that product should show the qty went up and the location updated. 2. Log a receipt with Rejected condition — the row appears in the recent-receipts table but inventory does <b>not</b> change. 3. Log a receipt with Qty expected 20 and Qty received 18 — the recent-receipts table should show <i>18 (exp 20, -2)</i>."
    )

    # ---------- 8. Packing & Production
    _section(story, 8, "Packing &amp; production")
    _screen_block(story, f"{BASE}/production",
        "Three tabs at the top: <b>Packing Manager</b>, <b>Packer Portal</b>, <b>Product Mixer</b>.",
        "Click each tab and confirm the correct view appears without a page reload."
    )
    story.append(Paragraph("Packing Manager tab", H2))
    story.append(_bullets([
        "Assign a Packing Job form — Product, Qty, Purpose (Inventory / Order / Both), Order # / Inventory Reference, Assign To, Assigned By, Notes.",
        "A live &#8220;Current inventory&#8221; readout appears under the product picker as soon as you pick one — red if at or below reorder threshold.",
        "Materials-needed preview appears below the notes field when Product + Qty are set.",
        "On save, the Notes are emailed to <font face=\"Courier\">PACKING_INBOX</font> (or the fallback inbox).",
        "Below the form: All Assignments table with SKU, product, progress, purpose, order/ref, on-hand, packer, status, materials, created.",
        "Below that: Packaging Specs form and table — set the container, lid, box, and units-per-box for each product.",
    ]))
    story.append(Paragraph("Packer Portal tab", H2))
    story.append(_bullets([
        "Packer picks their name from a dropdown.",
        "&#8220;My Assigned Jobs&#8221; shows open assignments with progress, notes, materials to pull, and a &#8220;Log Completed&#8221; button.",
        "&#8220;Log Production Not Tied to a Job&#8221; form for ad-hoc production entries.",
        "&#8220;My Log Today&#8221; table shows everything the packer logged today.",
    ]))
    story.append(Paragraph("Product Mixer tab", H2))
    story.append(_bullets([
        "For blended products like granola — define a recipe (product, unit weight, ingredients + percentages that must sum to 100).",
        "Preview lets you enter an order qty and see the raw ingredient amounts needed.",
    ]))

    # ---------- 9. Pallets & Shipping
    _section(story, 9, "Pallets &amp; shipping manifest")
    _screen_block(story, "Dashboard &#8594; Pallets &amp; Shipping card",
        "Modal listing every pallet: pallet #, loaded by, carrier, order count, status (building / staged / shipped), created date. Click a row to open the Manifest modal.",
        "Confirm the pallet number format is <font face=\"Courier\">PLT-######</font>. Click a pallet with orders on it &#8594; Manifest modal opens."
    )
    _screen_block(story, "Manifest modal",
        "Header with pallet number, loaded-by, carrier, status. For each order on the pallet: order #, customer, address, and an items table (SKU, product, qty). A Print Manifest button at the bottom.",
        "Click Print Manifest — the browser print dialog appears with a clean print stylesheet (no chrome, no buttons)."
    )

    # ---------- 10. Staff board
    _section(story, 10, "Staff assignment board")
    _screen_block(story, "Dashboard &#8594; Staff Assignment Board card",
        "Modal with a single table: Staff member, what they're working on, type (Order Task or Bulk Production), status.",
        "Confirm anyone with an active order task or open production assignment appears here. Nobody &#8594; the modal reads &#8220;No one is actively assigned to anything right now.&#8221;"
    )

    # ---------- 11. Reports
    _section(story, 11, "Reports (print / email PDF)")
    _screen_block(story, "Dashboard &#8594; Reports card",
        "Modal with three report cards: Daily Production, Product Receiving, Inventory Status. Each has parameter inputs, an Open PDF button, and an Email PDF button + recipient email field.",
        "1. Open PDF on Daily Production for today &#8594; PDF opens in a new tab, browser Print/Save works. 2. Enter your email in the Inventory Status card and click Email PDF &#8594; success message appears (email lands only if <font face=\"Courier\">MAIL_ENABLED=1</font> is set on Render, otherwise the API confirms it would have been sent)."
    )

    # ---------- 12. Stock page
    _section(story, 12, "Stock / inventory page")
    _screen_block(story, f"{BASE}/stock",
        "Focused mobile-friendly inventory page. Share buttons at the top (Text, Email, Print, Copy link). Search box, item-type filter, low-stock toggle chip. Summary row. Table columns: SKU, Barcode, Product, Description, Location, On hand, Reserved, Available, Min qty, Counted qty (print-only), Status, Actions.",
        "1. Type into the search box &#8212; the table filters live. 2. Click the Low stock chip &#8212; only rows below reorder threshold show. 3. On any row click Adjust, Location, then History &#8212; each opens the corresponding modal. 4. In the Location modal, paste a test barcode into the Barcode / GTIN field and save. Confirm the Barcode column updates on the row. 5. Click Print count sheet &#8212; a print-optimized stock count sheet renders."
    )
    story.append(Paragraph("Adjust modal", H2))
    story.append(_bullets([
        "Shows current on-hand.",
        "Change amount with +/- buttons or type directly.",
        "Reason dropdown (Manual adjustment / Received stock / Production completed / Removed / Returned).",
        "&#8220;Removed&#8221; always subtracts, &#8220;Returned&#8221; always adds &#8212; regardless of sign.",
        "Note field.",
    ]))
    story.append(Paragraph("Location modal", H2))
    story.append(_bullets([
        "Warehouse, Aisle, Bin / Column fields.",
        "Min qty (reorder point).",
        "Barcode / GTIN &#8212; UPC-12, EAN-13, or GTIN-14 &#8212; used by the scanner.",
    ]))
    story.append(Paragraph("History modal", H2))
    story.append(Paragraph("Every InventoryTransaction for that product &#8212; date, change (+/-), reason, note. This is your audit trail.", BODY))

    # ---------- 13. Barcode scanning
    _section(story, 13, "Barcode scanning &#8212; where and how")
    story.append(Paragraph("The Scan button appears in two forms today, both use the same backend endpoint:", BODY))
    story.append(_bullets([
        "Dashboard &#8594; <b>Log a Return</b> modal &#8594; &#128246; Scan barcode",
        "Dashboard &#8594; <b>Receiving</b> modal &#8594; &#128246; Scan barcode",
    ]))
    story.append(Paragraph("What happens when you click it", H2))
    story.append(_bullets([
        "A prompt opens asking for the barcode.",
        "Bluetooth scanners paired as keyboards will &#8220;type&#8221; the code directly into the prompt when you pull the trigger.",
        "You can also type manually.",
        "The API decodes the payload: if it's GS1-128 with a GTIN (<font face=\"Courier\">(01)</font>), it looks up the product; if the payload includes lot (<font face=\"Courier\">(10)</font>) and/or expiry (<font face=\"Courier\">(17)</font>), those auto-fill too.",
        "A green banner confirms which fields got filled.",
    ]))
    story.append(Paragraph("How to test without a real scanner", H2))
    story.append(Paragraph("On any product with a barcode set (via <font face=\"Courier\">/stock</font> &#8594; Location), open the Receiving Scan prompt and type <font face=\"Courier\">01</font> + the barcode padded to 14 digits + <font face=\"Courier\">17261230</font>. Product should fill and sell-by should read <b>2026-12-30</b>.", BODY))

    # ---------- 14. Applications admin
    _section(story, 14, "Applications admin")
    _screen_block(story, f"{BASE}/applications-admin",
        "Table of every job application submitted through the Careers form. Columns: applicant, role, phone, email, city, submitted, resume link, status. Click a row for the detail view; update status inline.",
        "Confirm the resume link downloads the file. Change a status and reload &#8212; it should persist."
    )

    # ---------- 15. Public site
    _section(story, 15, "Public marketing &amp; ordering site")
    _screen_block(story, f"{BASE}/store/",
        "The customer-facing marketing site. Hero, product catalog, cart, quote request, contact page, careers page, SOPs page.",
        "Walk every page. Add an item to the cart. Submit a test quote request. Submit a test application (small resume file) &#8212; confirm it appears in <font face=\"Courier\">/applications-admin</font>."
    )

    # ---------- 16. Change password & logout
    _section(story, 16, "Change password &amp; logout")
    _screen_block(story, f"{BASE}/change-password",
        "Simple form to change the logged-in staff user's password.",
        "Change it, log out, log back in with the new password."
    )
    story.append(Paragraph("Log out", H2))
    story.append(Paragraph("&#8220;Log out&#8221; is in the header on every authenticated page. Clicking it clears the session cookie and returns you to <font face=\"Courier\">/login</font>.", BODY))

    # ---------- 17. Reviewer checklist
    story.append(PageBreak())
    story.append(Paragraph("17. Reviewer checklist &amp; sign-off", SECTION))
    story.append(Paragraph("Tick each item as you complete the review. Note anything that surprised you.", BODY))

    check_rows = [
        ["#", "Area", "OK", "Notes"],
    ]
    items = [
        "Login and forced password change worked",
        "Dashboard KPI + Open orders KPI is clickable",
        "Alerts banner shows either issues or All Clear",
        "Both charts render with real data",
        "Orders modal opens, filter works, detail modal loads",
        "Order tasks can be assigned, started, completed",
        "Customer list + detail modal loads full history",
        "Log a Return creates a Returned inventory transaction",
        "Receiving accepts a Good receipt and bumps inventory",
        "Receiving Rejected receipt does NOT bump inventory",
        "Packing Manager assignment sends an email",
        "Packer Portal shows the assigned job",
        "Pallets modal opens; Manifest prints cleanly",
        "Staff board reflects current assignments",
        "Daily Production PDF opens with the expected data",
        "Receiving PDF opens with the expected data",
        "Inventory Status PDF opens with the expected data",
        "Email PDF returns success (or the &#8220;would send&#8221; message)",
        "Stock page: Adjust / Location / History all open",
        "Stock page: Barcode column shows what you saved",
        "Scan prompt fills product + lot + sell-by from a GS1-128 payload",
        "Applications admin lists submitted applications",
        "Public store loads on desktop and mobile",
        "Log out clears the session",
    ]
    for i, item in enumerate(items, 1):
        check_rows.append([str(i), Paragraph(item, BODY), "  □  ", ""])

    t = Table(check_rows, colWidths=[0.35 * inch, 4.4 * inch, 0.5 * inch, 2.05 * inch])
    t.setStyle(_table_style())
    story.append(t)
    story.append(Spacer(1, 14))

    # sign-off block
    sign_rows = [
        ["Field", "Value"],
        ["Reviewer name", ""],
        ["Reviewer signature", ""],
        ["Date reviewed", ""],
        ["Overall verdict", "☐ Ready for pilot   ☐ Needs changes (see notes)"],
        ["Top 3 issues to fix before rollout", ""],
    ]
    t = Table(sign_rows, colWidths=[2.0 * inch, 5.3 * inch],
              rowHeights=[0.32 * inch] + [0.4 * inch] * 4 + [1.0 * inch])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, INK),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("TEXTCOLOR", (0, 0), (-1, 0), CREAM),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))
    story.append(Paragraph("Return this signed manual to the Warehouse Manager. Any &#8220;Needs changes&#8221; verdict blocks general rollout until the listed issues are resolved.", META))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "AFB-App-Review-Manual.pdf")
    build(out)
    print(f"Wrote {out}")
