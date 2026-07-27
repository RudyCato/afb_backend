"""
Builds `AFB-Barcode-Train-the-Trainer.pdf` — a printable trainer guide for the
new barcode / GS1-128 / SSCC workflow across Receiving, Inventory, and
Shipping.

Run:
    python docs/build_trainer_pdf.py

Emits `docs/AFB-Barcode-Train-the-Trainer.pdf`.

Kept as a standalone script (rather than a route) so it can be regenerated
offline whenever the SOPs change, without touching the running server.
"""
from __future__ import annotations

import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, ListFlowable, ListItem,
)

# ---------------------------------------------------------------------------
INK = colors.HexColor("#241A10")
CREAM = colors.HexColor("#FBF6E9")
RUST = colors.HexColor("#a3402a")
OLIVE = colors.HexColor("#4f5c3a")
LINE = colors.HexColor("#d8c79a")

_styles = getSampleStyleSheet()

TITLE = ParagraphStyle("title", parent=_styles["Heading1"], textColor=INK,
                       fontName="Helvetica-Bold", fontSize=22, leading=26, spaceAfter=6)
SUBTITLE = ParagraphStyle("subtitle", parent=_styles["Heading2"], textColor=OLIVE,
                          fontName="Helvetica", fontSize=12, leading=16, spaceAfter=14)
H1 = ParagraphStyle("h1", parent=_styles["Heading1"], textColor=INK,
                    fontName="Helvetica-Bold", fontSize=15, leading=19, spaceBefore=16, spaceAfter=6)
H2 = ParagraphStyle("h2", parent=_styles["Heading2"], textColor=INK,
                    fontName="Helvetica-Bold", fontSize=11, leading=14, spaceBefore=10, spaceAfter=4)
BODY = ParagraphStyle("body", parent=_styles["BodyText"], textColor=INK,
                      fontName="Helvetica", fontSize=10, leading=13.5, spaceAfter=4)
CALLOUT = ParagraphStyle("callout", parent=BODY, textColor=RUST,
                         fontName="Helvetica-Bold", fontSize=10, leading=13, spaceAfter=6)
CODE = ParagraphStyle("code", parent=BODY, fontName="Courier", fontSize=9, leading=12, textColor=INK)
META = ParagraphStyle("meta", parent=_styles["BodyText"], textColor=OLIVE,
                      fontName="Helvetica-Oblique", fontSize=8, leading=11)


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
        bulletType="bullet", start="▪", leftIndent=14,
    )


def _footer(canvas_, doc):
    canvas_.saveState()
    canvas_.setFont("Helvetica-Oblique", 7)
    canvas_.setFillColor(OLIVE)
    canvas_.drawString(0.5 * inch, 0.35 * inch, "American Food & Beverage — Barcode Train-the-Trainer")
    canvas_.drawRightString(doc.pagesize[0] - 0.5 * inch, 0.35 * inch, f"Page {doc.page}")
    canvas_.restoreState()


def build(out_path: str):
    doc = SimpleDocTemplate(
        out_path, pagesize=LETTER,
        leftMargin=0.6 * inch, rightMargin=0.6 * inch,
        topMargin=0.6 * inch, bottomMargin=0.7 * inch,
        title="AFB Barcode Train-the-Trainer",
    )

    story = []

    # ---------- Cover
    story.append(Paragraph("American Food &amp; Beverage", META))
    story.append(Paragraph("Barcode &amp; Scanning — Train-the-Trainer Guide", TITLE))
    story.append(Paragraph("For Warehouse Managers training Receivers, Packers, and Shipping Clerks on the new GS1-128 / SSCC-based workflow.", SUBTITLE))
    story.append(Paragraph(f"Version 1.0 · Prepared {datetime.now().strftime('%B %Y')}", META))
    story.append(Spacer(1, 20))

    story.append(Paragraph("This guide", H2))
    story.append(Paragraph(
        "Walks a trainer through the material, the hands-on drills, and the sign-off criteria for "
        "certifying a new team member on AFB's barcode-based Receiving, Inventory, and Shipping "
        "workflow. The full procedures live in SOP-WHS-001 (Receiving), SOP-WHS-002 (Shipping), "
        "and SOP-WHS-003 (Inventory) — this document is how you teach them.", BODY))
    story.append(Spacer(1, 10))

    # ---------- Session plan
    story.append(Paragraph("Recommended session plan (½ day)", H1))
    session_data = [
        ["#", "Segment", "Time", "Goal"],
        ["1", "Why barcodes — FSMA 204, recalls, customer expectations", "20 min", "Trainee can explain what a lot recall requires."],
        ["2", "GS1-128, GTIN, lot, sell-by, SSCC — decoded on paper", "30 min", "Trainee reads a printed label and identifies each AI."],
        ["3", "The hardware — scanner, printer, phone/tablet", "30 min", "Trainee pairs a scanner, prints a label, scans it back."],
        ["4", "Receiving — live drill with 3 mock loads", "60 min", "Trainee logs 3 receipts (good / short / rejected) without help."],
        ["5", "Inventory — put-away, cycle count, adjust", "45 min", "Trainee runs a 10-SKU cycle count and reconciles 1 variance."],
        ["6", "Shipping — build pallet, generate SSCC, load", "60 min", "Trainee closes a pallet with SSCC and scans it onto a truck."],
        ["7", "Sign-off, Q&amp;A, refresher-cadence agreement", "15 min", "Trainer signs the certification page."],
    ]
    t = Table(session_data, colWidths=[0.35 * inch, 2.8 * inch, 0.75 * inch, 3.2 * inch])
    t.setStyle(_table_style())
    story.append(t)
    story.append(Spacer(1, 6))
    story.append(Paragraph("Total: ~4 hours plus a 15-min break. Do not compress — the drills are the point.", META))

    # ---------- Module 1
    story.append(PageBreak())
    story.append(Paragraph("Module 1 — Why barcodes", H1))
    story.append(Paragraph("Talk track", H2))
    story.append(_bullets([
        "Every case of covered food we handle must, under FDA FSMA 204, be traceable one-up (who we got it from, on what date, with what lot) and one-down (who we shipped it to, on what date, in which pallet).",
        "The compliance deadline is <b>July 20, 2028</b>. We are building the habit and the data now so we are already correct on that date, not scrambling.",
        "A recall is when everything is on fire. Nobody is reading procedure documents at that moment. The data has to be right <i>before</i> it is needed.",
        "If a receipt is missing a lot code, or a pallet leaves without an SSCC, or a case is scanned onto the wrong order — the trace breaks. A broken trace is a public health risk.",
    ]))
    story.append(Paragraph("Check for understanding", H2))
    story.append(_bullets([
        "Ask: \"If I get a call in 6 hours saying lot LMR-2038 of granola is recalled, what do I need to answer, and how fast?\" — good answers name every customer that got that lot and how many cases, in under an hour.",
        "Ask: \"If I skip the lot field on a receipt, what actually breaks?\" — the answer should include \"we can't trace forward or backward on that case.\"",
    ]))

    # ---------- Module 2
    story.append(Paragraph("Module 2 — Reading a GS1-128 label", H1))
    story.append(Paragraph("Print two of the sample labels on the next page. Give one to each trainee. Have them find and read out each AI.", BODY))
    ai_data = [
        ["AI", "Meaning", "Length", "Example encoded", "Example decoded"],
        ["(01)", "GTIN — the SKU", "14 digits", "01 10614141999996", "GTIN 10614141999996"],
        ["(10)", "Batch / Lot", "up to 20 chars", "10 LMR2038", "Lot LMR2038"],
        ["(17)", "Expiration (best-by)", "6 digits YYMMDD", "17 260930", "Best by 2026-09-30"],
        ["(00)", "SSCC — pallet ID", "18 digits", "00 006141410000012345", "SSCC 006141410000012345"],
    ]
    t = Table(ai_data, colWidths=[0.5 * inch, 1.6 * inch, 1.0 * inch, 1.9 * inch, 2.1 * inch])
    t.setStyle(_table_style())
    story.append(t)
    story.append(Spacer(1, 8))
    story.append(Paragraph("Notes to reinforce", H2))
    story.append(_bullets([
        "The parentheses are printed on the label for humans. They are <b>not</b> in the barcode itself — the scanner emits <i>01</i>, not <i>(01)</i>.",
        "A variable-length AI like (10) is terminated by an invisible <i>Group Separator</i> character or by the end of the label. Our decoder handles both.",
        "Dates are always <b>YYMMDD</b>. \"261230\" is 30 Dec 2026, not 12 Dec 2030.",
        "If a vendor label has no (01) and no (17), that's OK for internal use — but flag it: FSMA-covered inbound should have both.",
    ]))

    # ---------- Module 3
    story.append(PageBreak())
    story.append(Paragraph("Module 3 — The hardware", H1))

    hw_data = [
        ["Item", "Model (per Option 2)", "Notes for trainer"],
        ["Handheld scanner", "Socket Mobile S720 2D (or Zebra CS60-HC)", "Pairs to phone/tablet as a Bluetooth keyboard. Battery lasts a shift; charge on the cradle nightly."],
        ["Phone / tablet", "BYOD Android/iOS, or shared 8\" Android tablet", "Runs `/dashboard`. Keep on Wi-Fi in the warehouse."],
        ["Label printer", "Zebra ZD621 4\" thermal transfer", "Prints both case labels (4x2) and pallet labels (4x6). Keep two ribbons on hand."],
        ["Label media", "Freezer-grade direct thermal for case; thermal-transfer for pallet", "Freezer-grade adhesive matters — regular adhesive falls off cold cases."],
    ]
    t = Table(hw_data, colWidths=[1.2 * inch, 2.4 * inch, 3.5 * inch])
    t.setStyle(_table_style())
    story.append(t)

    story.append(Paragraph("Pairing drill", H2))
    story.append(Paragraph("Do this together on Day 1 — do not skip. Every trainee pairs a scanner to their assigned device with the trainer watching:", BODY))
    story.append(_bullets([
        "Power on the scanner. It beeps and the pairing LED flashes.",
        "On the device, open Bluetooth settings, find the scanner (\"Socket S720\" or \"CS60\"), tap Pair.",
        "Open `/dashboard` → Receiving → click the barcode field.",
        "Pull the scanner trigger on the test label. If the digits appear in the field, pairing is complete.",
        "If the scan appears somewhere else (chat, notes, home screen): the scanner is paired to the wrong device — unpair and redo.",
    ]))

    # ---------- Module 4
    story.append(Paragraph("Module 4 — Receiving drill (3 mock loads)", H1))
    story.append(Paragraph("Set up three mock deliveries at the receiving dock. The trainee logs each without trainer help; the trainer observes and marks the certification checklist.", BODY))

    drill_data = [
        ["Mock load", "What's on it", "What the trainee must do", "What they must NOT do"],
        ["Clean load", "10 cases, all GS1-128, quantities match PO, no damage", "Scan each case, save with correct put-away, receipt in portal in ≤ 5 min", "Skip lot or sell-by; save without location"],
        ["Short load", "Case ordered 20 but only 18 arrived, one is damaged", "Log qty received = 18, condition = partial damage, note damage; flag to Manager <b>before driver leaves</b>", "Sign off before flagging; over-report qty to \"match PO\""],
        ["Rejected load", "Off-temperature cold case, seal broken", "Log a receipt with condition = rejected (no inventory added), photograph, wait for Manager", "Accept it \"because the driver is in a hurry\"; put in stock"],
    ]
    t = Table(drill_data, colWidths=[0.9 * inch, 1.9 * inch, 2.5 * inch, 1.8 * inch])
    t.setStyle(_table_style())
    story.append(t)

    story.append(Paragraph("Pass criteria", H2))
    story.append(_bullets([
        "All three loads logged with 100% of required fields — no blank Received-by, no blank Location, no missing lot on the clean load.",
        "Rejected load did <b>not</b> increment inventory.",
        "Short-load discrepancy raised to trainer <i>before</i> the mock driver \"leaves\".",
    ]))

    # ---------- Module 5
    story.append(PageBreak())
    story.append(Paragraph("Module 5 — Inventory drill (cycle count + adjust)", H1))
    story.append(Paragraph("Choose one aisle with ~10 SKUs. Print the Inventory Status PDF for it in advance. Introduce a deliberate variance the trainee doesn't know about (e.g. hide 2 units of one SKU).", BODY))
    story.append(_bullets([
        "Trainee counts each row, marks physical count next to system count.",
        "Trainee finds the variance and recounts (should recount before assuming the system is wrong).",
        "Trainee returns to portal, opens the affected SKU, presses Adjust, reason = Manual adjustment, notes \"cycle count variance, physical was N\".",
        "Trainer confirms the adjustment reads correctly in the SKU's History.",
    ]))
    story.append(Paragraph("Pass criteria: trainee recounts before adjusting, uses the correct reason, and writes a note that another human could understand in 6 months.", BODY))

    # ---------- Module 6
    story.append(Paragraph("Module 6 — Shipping drill (SSCC pallet close)", H1))
    story.append(Paragraph("Use a real order in packed status. Trainee is the Shipping Clerk; trainer plays Forklift Operator and mock driver.", BODY))
    story.append(_bullets([
        "Trainee creates a Pallet, assigns the order.",
        "Trainee scans every case onto the pallet — trainer sneaks in one wrong case that must be caught.",
        "Trainee wraps and corner-protects, then presses Generate SSCC.",
        "Trainee prints the pallet label, applies two copies (front + side), at 16-32\" from the bottom.",
        "Trainee stages the pallet, then on \"truck arrival\" scans the SSCC onto the truck manifest, prints the BOL, hands it to the mock driver.",
    ]))
    story.append(Paragraph("Pass criteria: wrong case was caught during scan (not after wrap); SSCC printed with two labels placed correctly; pallet status ends as <b>shipped</b>; truck manifest matches what was scanned.", BODY))

    # ---------- Common mistakes
    story.append(Paragraph("Common trainee mistakes — call them out fast", H1))
    mistakes = [
        ["Mistake", "Why it happens", "Fix in the moment"],
        ["Skipping lot code on receipt", "\"It's optional, right?\" — no, not for FSMA-covered inbound", "Reject the save, re-open, enter it."],
        ["Typing sell-by with wrong century (2126 instead of 2026)", "Copy-paste from label got garbled", "Have them re-read the AI: YYMMDD, two-digit year."],
        ["Loading a case that failed to scan", "\"It's basically the right SKU\"", "Never. Set it aside, resolve the mismatch, log an adjustment if needed."],
        ["Signing the BOL with an unresolved shortage", "Driver pressure", "Not acceptable. If the driver refuses to wait, they leave without signature and the office resolves it."],
        ["Batch-entering a shift's worth of receipts at 5 pm", "\"I was too busy\"", "The offline paper sheet exists for exactly this. Enter within 4 hours, not end of shift."],
    ]
    t = Table(mistakes, colWidths=[2.3 * inch, 2.2 * inch, 2.7 * inch])
    t.setStyle(_table_style())
    story.append(t)

    # ---------- Refresh cadence
    story.append(PageBreak())
    story.append(Paragraph("Refresh cadence", H1))
    story.append(_bullets([
        "<b>30-day check</b> — trainer reviews 5 randomly-selected receipts and 5 pallets logged by the trainee. Any recurring gap → 30 min of retraining on the specific step.",
        "<b>Quarterly</b> — 10-minute team huddle on any changes to hardware, media, or the SOPs. Log attendance.",
        "<b>Annually</b> — full re-certification against the three SOPs. Re-sign the certification page below.",
        "<b>On any change to scanning hardware or label printers</b> — a fresh pairing drill for the affected staff.",
    ]))

    # ---------- Cert
    story.append(Paragraph("Trainee certification", H1))
    story.append(Paragraph("The trainer signs below only when the trainee has passed all six drills with no assist required for pass criteria.", BODY))

    cert_data = [
        ["Field", "Value"],
        ["Trainee name", ""],
        ["Trainee signature", ""],
        ["Role certified for", "☐ Receiver   ☐ Packer   ☐ Shipping Clerk"],
        ["Trainer name", ""],
        ["Trainer signature", ""],
        ["Date completed", ""],
        ["Next re-cert due", ""],
        ["Notes", ""],
    ]
    t = Table(cert_data, colWidths=[1.8 * inch, 5.4 * inch], rowHeights=[0.35 * inch] * 8 + [0.9 * inch])
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
    story.append(Paragraph("Filed in: Warehouse Manager's training folder (physical + scanned to shared drive).", META))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "AFB-Barcode-Train-the-Trainer.pdf")
    build(out)
    print(f"Wrote {out}")
