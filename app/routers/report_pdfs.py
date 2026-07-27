"""
Printable / emailable PDF reports.

Three reports for the pilot rollout:

    daily-production   packer log for a given date (defaults to today)
    receipts           inbound receipts for the last N days (default 7)
    inventory          current on-hand + reserved + reorder status

Each report has TWO delivery paths:

    GET  /reports/pdf/<report>?<params>              → streams the PDF (browser
                                                       opens it inline, and the
                                                       browser's native PDF
                                                       viewer handles Print /
                                                       Download / Save).

    POST /reports/pdf/<report>/email?to=address      → generates the PDF and
                                                       emails it as an attachment
                                                       via the shared SMTP helper.

Kept intentionally simple — reportlab.platypus with a Table per section, one
header block, one footer with generation timestamp. No client-side rendering,
no headless browser, no system dependencies.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from io import BytesIO
from typing import Iterable

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak,
)

from .. import models
from ..database import get_db
from .. import mail

router = APIRouter(prefix="/reports/pdf", tags=["reports"])

# --------------------------------------------------------------------------- style
BRAND_INK = colors.HexColor("#241A10")
BRAND_RUST = colors.HexColor("#a3402a")
BRAND_OLIVE = colors.HexColor("#4f5c3a")
BRAND_LINE = colors.HexColor("#d8c79a")
BRAND_CREAM = colors.HexColor("#FBF6E9")

_styles = getSampleStyleSheet()
_H1 = ParagraphStyle("h1", parent=_styles["Heading1"], textColor=BRAND_INK,
                     fontName="Helvetica-Bold", fontSize=16, leading=20, spaceAfter=6)
_H2 = ParagraphStyle("h2", parent=_styles["Heading2"], textColor=BRAND_INK,
                     fontName="Helvetica-Bold", fontSize=11, leading=14, spaceBefore=10, spaceAfter=4)
_META = ParagraphStyle("meta", parent=_styles["BodyText"], textColor=BRAND_OLIVE,
                       fontName="Helvetica", fontSize=8, leading=11)
_BODY = ParagraphStyle("body", parent=_styles["BodyText"], textColor=BRAND_INK,
                       fontName="Helvetica", fontSize=9, leading=12)
_FOOTER = ParagraphStyle("footer", parent=_styles["BodyText"], textColor=BRAND_OLIVE,
                         fontName="Helvetica-Oblique", fontSize=7, leading=9, alignment=1)


def _table_style() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND_INK),
        ("TEXTCOLOR", (0, 0), (-1, 0), BRAND_CREAM),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),
        ("LINEBELOW", (0, 0), (-1, 0), 0.75, BRAND_INK),
        ("LINEBELOW", (0, "splitfirst"), (-1, -2), 0.25, BRAND_LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F1DE")]),
    ])


def _header(title: str, subtitle: str) -> list:
    now = datetime.now().strftime("%a %b %d %Y — %I:%M %p")
    return [
        Paragraph("American Food &amp; Beverage", _META),
        Paragraph(title, _H1),
        Paragraph(subtitle, _META),
        Paragraph(f"Generated {now}", _META),
        Spacer(1, 10),
    ]


def _footer_on_page(canvas_, doc):
    canvas_.saveState()
    canvas_.setFont("Helvetica-Oblique", 7)
    canvas_.setFillColor(BRAND_OLIVE)
    canvas_.drawCentredString(
        doc.pagesize[0] / 2.0, 0.35 * inch,
        f"Page {doc.page} — American Food & Beverage Operations",
    )
    canvas_.restoreState()


def _build_pdf(story: Iterable, *, landscape_mode: bool = False) -> bytes:
    buf = BytesIO()
    page_size = landscape(LETTER) if landscape_mode else LETTER
    doc = SimpleDocTemplate(
        buf, pagesize=page_size,
        leftMargin=0.5 * inch, rightMargin=0.5 * inch,
        topMargin=0.5 * inch, bottomMargin=0.5 * inch,
        title="AFB Operations Report",
    )
    doc.build(list(story), onFirstPage=_footer_on_page, onLaterPages=_footer_on_page)
    return buf.getvalue()


# --------------------------------------------------------------------------- reports

def _daily_production_pdf(db: Session, on_date: date) -> tuple[bytes, str]:
    start = datetime.combine(on_date, datetime.min.time())
    end = datetime.combine(on_date, datetime.max.time())
    logs = (
        db.query(models.PackerProductionLog)
        .filter(models.PackerProductionLog.logged_at >= start)
        .filter(models.PackerProductionLog.logged_at <= end)
        .order_by(models.PackerProductionLog.logged_at.asc())
        .all()
    )

    # Per-packer totals
    totals: dict[str, dict] = {}
    for log in logs:
        t = totals.setdefault(log.packer_name, {"packer": log.packer_name, "units": 0, "entries": 0})
        t["units"] += log.qty_completed
        t["entries"] += 1
    packer_rows = sorted(totals.values(), key=lambda r: r["units"], reverse=True)

    story = _header("Daily Production Report", f"For {on_date.strftime('%A, %B %d, %Y')}")

    # Summary
    story.append(Paragraph("Summary by packer", _H2))
    if packer_rows:
        data = [["Packer", "Units Packed", "Log Entries"]]
        for r in packer_rows:
            data.append([r["packer"], f"{r['units']:,}", str(r["entries"])])
        data.append(["TOTAL", f"{sum(r['units'] for r in packer_rows):,}", str(sum(r['entries'] for r in packer_rows))])
        t = Table(data, colWidths=[3.5 * inch, 1.5 * inch, 1.5 * inch])
        t.setStyle(_table_style())
        # bold the total row
        t.setStyle(TableStyle([
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("LINEABOVE", (0, -1), (-1, -1), 0.75, BRAND_INK),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No production logged for this day.", _BODY))

    # Detail
    story.append(Spacer(1, 14))
    story.append(Paragraph("Detail — every log entry", _H2))
    if logs:
        data = [["Time", "Packer", "SKU", "Product", "Qty", "Notes"]]
        for log in logs:
            data.append([
                log.logged_at.strftime("%I:%M %p"),
                log.packer_name,
                log.product.sku,
                log.product.name,
                str(log.qty_completed),
                (log.notes or "")[:60],
            ])
        t = Table(data, colWidths=[0.9 * inch, 1.3 * inch, 0.9 * inch, 2.2 * inch, 0.6 * inch, 2.2 * inch])
        t.setStyle(_table_style())
        story.append(t)
    else:
        story.append(Paragraph("No log entries.", _BODY))

    pdf = _build_pdf(story, landscape_mode=True)
    filename = f"afb-daily-production-{on_date.isoformat()}.pdf"
    return pdf, filename


def _receipts_pdf(db: Session, days: int) -> tuple[bytes, str]:
    days = max(1, min(days, 90))
    cutoff = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days - 1)
    rows = (
        db.query(models.Receipt)
        .filter(models.Receipt.created_at >= cutoff)
        .order_by(models.Receipt.created_at.desc())
        .all()
    )

    story = _header(
        "Product Receiving Report",
        f"Last {days} day{'s' if days != 1 else ''} — from {cutoff.strftime('%b %d, %Y')} to today",
    )

    # Summary
    total_lines = len(rows)
    total_units = sum(r.qty_received for r in rows if r.condition != models.ReceiptCondition.rejected)
    rejected = sum(1 for r in rows if r.condition == models.ReceiptCondition.rejected)
    damaged = sum(1 for r in rows if r.condition in (models.ReceiptCondition.damaged, models.ReceiptCondition.partial_damage))
    summary_data = [
        ["Total receipt lines", str(total_lines)],
        ["Units accepted into stock", f"{total_units:,}"],
        ["Damaged / partial damage", str(damaged)],
        ["Rejected (not added to stock)", str(rejected)],
    ]
    st = Table(summary_data, colWidths=[3 * inch, 1.5 * inch])
    st.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, BRAND_LINE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(st)
    story.append(Spacer(1, 12))

    # Detail
    story.append(Paragraph("Detail — every receipt line", _H2))
    if rows:
        data = [["When", "Vendor / PO", "SKU / Product", "Qty (exp)", "Lot / Sell-by", "Cond.", "Location", "By"]]
        for r in rows:
            when = r.created_at.strftime("%b %d %I:%M %p")
            vendor_po = " / ".join([p for p in [r.vendor or "", ("#" + r.po_number) if r.po_number else ""] if p]) or "—"
            product = f"{r.product.sku}\n{r.product.name}"
            if r.qty_expected is not None and r.qty_expected != r.qty_received:
                qty = f"{r.qty_received} (exp {r.qty_expected})"
            else:
                qty = str(r.qty_received)
            lot_sb = " / ".join([p for p in [
                ("Lot " + r.lot_code) if r.lot_code else "",
                ("Best-by " + r.sell_by_date.isoformat()) if r.sell_by_date else "",
            ] if p]) or "—"
            location = " / ".join([p for p in [r.put_away_warehouse or "", r.put_away_aisle or "", r.put_away_bin_column or ""] if p]) or "—"
            data.append([when, vendor_po, product, qty, lot_sb, r.condition.value, location, r.received_by])
        t = Table(data, colWidths=[1.1 * inch, 1.3 * inch, 1.7 * inch, 0.9 * inch, 1.5 * inch, 0.7 * inch, 1.1 * inch, 1.0 * inch])
        t.setStyle(_table_style())
        story.append(t)
    else:
        story.append(Paragraph("No receipts in this window.", _BODY))

    pdf = _build_pdf(story, landscape_mode=True)
    filename = f"afb-receipts-last-{days}d.pdf"
    return pdf, filename


def _inventory_pdf(db: Session, item_type: str | None) -> tuple[bytes, str]:
    q = db.query(models.Product).filter(models.Product.active == True)  # noqa: E712
    if item_type:
        try:
            q = q.filter(models.Product.item_type == models.ProductType(item_type))
        except ValueError:
            raise HTTPException(422, f"Unknown item_type '{item_type}'.")
    products = q.order_by(models.Product.sku.asc()).all()

    inv_by_pid = {
        i.product_id: i for i in db.query(models.Inventory).all()
    }

    title = "Inventory Status Report"
    subtitle = "All active products"
    if item_type == "sellable":
        subtitle = "Sellable finished-goods catalog"
    elif item_type == "indirect_material":
        subtitle = "Packaging & supplies (containers, lids, boxes, PPE)"

    story = _header(title, subtitle)

    # Summary — low-stock count
    low_stock = 0
    total_units = 0
    for p in products:
        inv = inv_by_pid.get(p.id)
        if inv:
            total_units += int(inv.qty_on_hand or 0)
            if (inv.qty_on_hand or 0) - (inv.qty_reserved or 0) <= (inv.reorder_threshold or 0):
                low_stock += 1
    summary_data = [
        ["Products in report", str(len(products))],
        ["Total on-hand units", f"{total_units:,}"],
        ["Below reorder threshold", str(low_stock)],
    ]
    st = Table(summary_data, colWidths=[3 * inch, 1.5 * inch])
    st.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, BRAND_LINE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(st)
    story.append(Spacer(1, 12))

    # Detail
    story.append(Paragraph("Detail — every active product", _H2))
    data = [["SKU", "Product", "Location", "On hand", "Reserved", "Avail.", "Min", "Status"]]
    row_flags: list[bool] = []   # True marks a low-stock row for later highlight
    for p in products:
        inv = inv_by_pid.get(p.id)
        on_hand = int(inv.qty_on_hand or 0) if inv else 0
        reserved = int(inv.qty_reserved or 0) if inv else 0
        avail = on_hand - reserved
        min_q = int(inv.reorder_threshold or 0) if inv else 0
        is_low = inv is not None and avail <= min_q
        location = " / ".join([p2 for p2 in [
            (inv.warehouse or "") if inv else "",
            (inv.aisle or "") if inv else "",
            (inv.bin_column or "") if inv else "",
        ] if p2]) or ((inv.location or "—") if inv else "—")
        data.append([
            p.sku, p.name, location,
            str(on_hand), str(reserved), str(avail), str(min_q),
            "REORDER" if is_low else "OK",
        ])
        row_flags.append(is_low)

    t = Table(data, colWidths=[0.9 * inch, 2.3 * inch, 1.6 * inch, 0.7 * inch, 0.75 * inch, 0.65 * inch, 0.55 * inch, 0.85 * inch])
    style = _table_style()
    # Paint low-stock rows in a soft warning tint (1-indexed relative to data)
    for idx, low in enumerate(row_flags, start=1):
        if low:
            style.add("TEXTCOLOR", (7, idx), (7, idx), BRAND_RUST)
            style.add("FONTNAME", (7, idx), (7, idx), "Helvetica-Bold")
    t.setStyle(style)
    story.append(t)

    pdf = _build_pdf(story, landscape_mode=True)
    filename = f"afb-inventory-{item_type or 'all'}.pdf"
    return pdf, filename


# --------------------------------------------------------------------------- helpers

def _generate(report: str, params: dict, db: Session) -> tuple[bytes, str]:
    if report == "daily-production":
        on_date_str = params.get("date")
        on_date = date.fromisoformat(on_date_str) if on_date_str else date.today()
        return _daily_production_pdf(db, on_date)
    if report == "receipts":
        days = int(params.get("days") or 7)
        return _receipts_pdf(db, days)
    if report == "inventory":
        return _inventory_pdf(db, params.get("item_type"))
    raise HTTPException(404, f"Unknown report '{report}'.")


def _stream(pdf_bytes: bytes, filename: str, download: bool) -> StreamingResponse:
    disposition = "attachment" if download else "inline"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'{disposition}; filename="{filename}"'},
    )


# --------------------------------------------------------------------------- routes

@router.get("/daily-production")
def daily_production(
    date_str: str | None = Query(None, alias="date", description="YYYY-MM-DD; defaults to today"),
    download: bool = False,
    db: Session = Depends(get_db),
):
    on_date = date.fromisoformat(date_str) if date_str else date.today()
    pdf, filename = _daily_production_pdf(db, on_date)
    return _stream(pdf, filename, download)


@router.get("/receipts")
def receipts_pdf(
    days: int = 7,
    download: bool = False,
    db: Session = Depends(get_db),
):
    pdf, filename = _receipts_pdf(db, days)
    return _stream(pdf, filename, download)


@router.get("/inventory")
def inventory_pdf(
    item_type: str | None = None,
    download: bool = False,
    db: Session = Depends(get_db),
):
    pdf, filename = _inventory_pdf(db, item_type)
    return _stream(pdf, filename, download)


@router.post("/email")
def email_report(
    report: str = Query(..., description="daily-production | receipts | inventory"),
    to: str = Query(..., description="recipient email address"),
    date_str: str | None = Query(None, alias="date"),
    days: int | None = Query(None),
    item_type: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Generate the requested PDF and email it as an attachment."""
    to_addr = (to or "").strip()
    if "@" not in to_addr:
        raise HTTPException(422, "A valid recipient email address is required.")

    params = {}
    if date_str: params["date"] = date_str
    if days is not None: params["days"] = days
    if item_type: params["item_type"] = item_type
    pdf_bytes, filename = _generate(report, params, db)

    subject_map = {
        "daily-production": "Daily Production Report",
        "receipts": "Product Receiving Report",
        "inventory": "Inventory Status Report",
    }
    subject = f"[AFB] {subject_map.get(report, report.title())} — {datetime.now().strftime('%b %d, %Y')}"
    body_lines = [
        f"Attached: {filename}",
        "",
        "Generated from the American Food & Beverage operations dashboard.",
        f"Report type: {report}",
        f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    ]
    msg = mail.build_message(subject=subject, to=to_addr, body="\n".join(body_lines))
    mail.attach_pdf(msg, filename=filename, data=pdf_bytes)
    mail.send(msg)

    cfg = mail.smtp_config()
    if not cfg["enabled"]:
        return {"ok": True, "sent": False, "detail": f"Mail sending is disabled — the PDF would have gone to {to_addr}. Set MAIL_ENABLED=1 to actually send."}
    return {"ok": True, "sent": True, "detail": f"Sent {filename} to {to_addr}."}
