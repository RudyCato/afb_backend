"""
Builds `AFB-Review-Portal-Guide.pdf` — a plain-language "for dummies" guide
to the Project Review portal, for reviewers (management + employees) who
have never used it before. Answers What / Why / Where / When, then walks
through leaving a comment step by step.

Run:
    python docs/build_review_guide_pdf.py

Emits `docs/AFB-Review-Portal-Guide.pdf`.
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
    ListFlowable, ListItem, HRFlowable, Image,
)
from reportlab.lib.utils import ImageReader

INK = colors.HexColor("#241A10")
CREAM = colors.HexColor("#FBF6E9")
RUST = colors.HexColor("#a3402a")
RUST_DEEP = colors.HexColor("#7f3121")
OLIVE = colors.HexColor("#4f5c3a")
OLIVE_DEEP = colors.HexColor("#3a4429")
LINE = colors.HexColor("#d8c79a")
GOLD = colors.HexColor("#c2932f")
PANEL = colors.HexColor("#F7F1DE")

_styles = getSampleStyleSheet()

TITLE = ParagraphStyle("title", parent=_styles["Heading1"], textColor=INK,
                       fontName="Helvetica-Bold", fontSize=24, leading=28, spaceAfter=4)
SUBTITLE = ParagraphStyle("subtitle", parent=_styles["Heading2"], textColor=OLIVE,
                          fontName="Helvetica", fontSize=12, leading=16, spaceAfter=16)
SECTION = ParagraphStyle("section", parent=_styles["Heading1"], textColor=RUST_DEEP,
                         fontName="Helvetica-Bold", fontSize=17, leading=21,
                         spaceBefore=16, spaceAfter=8, keepWithNext=True)
QWORD = ParagraphStyle("qword", parent=_styles["Heading1"], textColor=GOLD,
                       fontName="Helvetica-Bold", fontSize=11, leading=13, spaceAfter=2)
H2 = ParagraphStyle("h2", parent=_styles["Heading2"], textColor=INK,
                    fontName="Helvetica-Bold", fontSize=12, leading=15,
                    spaceBefore=8, spaceAfter=4, keepWithNext=True)
BODY = ParagraphStyle("body", parent=_styles["BodyText"], textColor=INK,
                      fontName="Helvetica", fontSize=10.5, leading=15, spaceAfter=6)
BIG = ParagraphStyle("big", parent=BODY, fontSize=12, leading=17, spaceAfter=8)
CODE = ParagraphStyle("code", parent=BODY, fontName="Courier", fontSize=9.5,
                      leading=13, textColor=INK, leftIndent=8, spaceAfter=6,
                      backColor=PANEL)
CALLOUT = ParagraphStyle("callout", parent=BODY, textColor=RUST_DEEP,
                         fontName="Helvetica-Bold", fontSize=10.5, leading=14,
                         spaceAfter=6)
META = ParagraphStyle("meta", parent=_styles["BodyText"], textColor=OLIVE,
                      fontName="Helvetica-Oblique", fontSize=8, leading=11)


def _bullets(items, style=BODY):
    return ListFlowable(
        [ListItem(Paragraph(t, style), leftIndent=10, bulletColor=RUST) for t in items],
        bulletType="bullet", start="•", leftIndent=14,
    )


def _footer(canvas_, doc):
    canvas_.saveState()
    canvas_.setFont("Helvetica-Oblique", 7)
    canvas_.setFillColor(OLIVE)
    canvas_.drawString(0.5 * inch, 0.35 * inch, "American Food & Beverage — Project Review Guide")
    canvas_.drawRightString(doc.pagesize[0] - 0.5 * inch, 0.35 * inch, f"Page {doc.page}")
    canvas_.restoreState()


def _qbox(story, question, answer_paragraphs):
    """Boxed Q/A block: gold question label, ink answer, thin rust rule under it."""
    story.append(Paragraph(question, QWORD))
    for p in answer_paragraphs:
        story.append(Paragraph(p, BIG))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=LINE, spaceAfter=14))


def build():
    out_path = os.path.join(os.path.dirname(__file__), "AFB-Review-Portal-Guide.pdf")
    doc = SimpleDocTemplate(
        out_path, pagesize=LETTER,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
        topMargin=0.7 * inch, bottomMargin=0.6 * inch,
        title="AFB Project Review Guide",
    )
    story = []

    # ---- Cover / intro -----------------------------------------------
    story.append(Paragraph("The Project Review Portal", TITLE))
    story.append(Paragraph("A simple guide — for everyone, no experience needed", SUBTITLE))
    story.append(HRFlowable(width="100%", thickness=2, color=RUST, spaceAfter=16))

    story.append(Paragraph(
        "If someone at American Food &amp; Beverage sent you a link and asked you to "
        "“review a workflow” or “leave feedback,” this page is for you. "
        "It explains everything in plain language: what this is, why it exists, where to "
        "find it, and when to use it. No technical background required.",
        BIG,
    ))
    story.append(Spacer(1, 10))

    _screenshot_path = os.path.join(os.path.dirname(__file__), "images", "review-portal-screenshot.jpg")
    if os.path.exists(_screenshot_path):
        img_reader = ImageReader(_screenshot_path)
        iw, ih = img_reader.getSize()
        max_w = 6.5 * inch
        display_h = max_w * (ih / iw)
        story.append(Image(_screenshot_path, width=max_w, height=display_h))
        story.append(Paragraph("This is what a review page looks like — pick a screen on the left, read the four boxes, leave a comment at the bottom.", META))
        story.append(Spacer(1, 12))

    # ---- WHAT -----------------------------------------------------------
    _qbox(story, "WHAT IS IT?", [
        "The Review Portal is a webpage that shows you how a part of the AFB app works — "
        "what the screen looks like, what information it collects, and what happens after "
        "someone fills it out. Underneath each one is a simple comment box.",
        "You read, you comment. That's the whole idea. You're not editing anything, you're "
        "not logging into the real app, and you can't break anything by clicking around.",
    ])

    # ---- WHY -----------------------------------------------------------
    _qbox(story, "WHY ARE WE DOING THIS?", [
        "Because the people who actually do the work — receiving, packing, shipping, "
        "answering the phone — notice problems that get missed when the app is built. "
        "A field that's confusing, a step that's missing, a button in the wrong place. "
        "This is the easiest way to catch that <b>before</b> it costs real time on the floor.",
        "It also means suggestions don't get lost in a hallway conversation or a text "
        "message nobody can find again. Every comment is saved, dated, and tracked until "
        "someone actually resolves it.",
    ])

    # ---- WHERE -----------------------------------------------------------
    _qbox(story, "WHERE DO I GO?", [
        "You'll be sent a link that looks like this:",
    ])
    story.append(Paragraph("https://afb-backend-58ys.onrender.com/review/&lt;a long code&gt;", CODE))
    story.append(Paragraph(
        "Click it, or paste it into any browser — phone, tablet, or computer all work. "
        "<b>You do not need a username or password.</b> The long code in the link is your "
        "access, so keep the link private and don't forward it anywhere public — it's "
        "the same as leaving a door unlocked.",
        BIG,
    ))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=LINE, spaceAfter=14))

    # ---- WHEN -----------------------------------------------------------
    _qbox(story, "WHEN SHOULD I USE IT?", [
        "Any time you're sent a review link — there's no set schedule. A few guidelines:",
    ])
    story.append(_bullets([
        "Try to look it over within a few days of getting the link, while the screen is fresh in your head.",
        "You can comment more than once, and come back to the same link later — nothing expires or locks after one visit.",
        "If you spot something mid-shift and don't have time to write it up, jot a quick note and come back to it — better a rough comment than none.",
    ]))
    story.append(Spacer(1, 10))

    story.append(PageBreak())

    # ---- HOW TO USE IT -----------------------------------------------------------
    story.append(Paragraph("How to Leave a Comment — Step by Step", SECTION))
    steps = [
        "<b>Open the link.</b> You'll see a page with a list of screens down the left side "
        "(things like “Receiving,” “Log a Return,” “Reports”).",
        "<b>Click a screen name</b> to open it. You'll see four boxes: what the screen "
        "looks like, how the process flows step by step, what information it collects, "
        "and what else it affects downstream.",
        "<b>Read through the four boxes.</b> You don't need to understand every technical "
        "detail — just react to whether it matches how the work actually happens.",
        "<b>Scroll down to the comment box.</b> Type your name and email if you want a "
        "follow-up (both optional), pick a category, and write your comment in plain "
        "language — a sentence or two is plenty.",
        "<b>Click Submit comment.</b> That's it — it's saved immediately and the person "
        "running the review gets notified.",
    ]
    story.append(ListFlowable(
        [ListItem(Paragraph(s, BODY), leftIndent=12, bulletColor=RUST, value=i + 1) for i, s in enumerate(steps)],
        bulletType="1", leftIndent=16,
    ))
    story.append(Spacer(1, 12))

    # ---- Categories -----------------------------------------------------------
    story.append(Paragraph("What Category Do I Pick?", SECTION))
    cat_data = [
        ["Category", "Use it when…"],
        ["Bug", "Something looks broken, wrong, or doesn't match how the real process works."],
        ["Suggestion", "You have an idea that would make the screen or process better — not broken, just improvable."],
        ["Question", "You're not sure why something works the way it does, or need more explanation."],
        ["Approval", "This screen looks right to you as-is — no changes needed, just a thumbs-up on record."],
    ]
    cat_table = Table(cat_data, colWidths=[1.3 * inch, 5.2 * inch])
    cat_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), INK),
        ("TEXTCOLOR", (0, 0), (-1, 0), CREAM),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9.5),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 1), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 1), (0, -1), RUST_DEEP),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PANEL]),
        ("GRID", (0, 0), (-1, -1), 0.25, LINE),
    ]))
    story.append(cat_table)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Not sure which one fits? Pick your best guess — nothing is locked in, and the "
        "person triaging comments can always recategorize it.",
        META,
    ))

    story.append(PageBreak())

    # ---- FAQ -----------------------------------------------------------
    story.append(Paragraph("Common Questions", SECTION))
    faqs = [
        ("Do I need to create an account?",
         "No. The link itself is your access — no username, no password, no sign-up."),
        ("Will people see my name?",
         "Only if you type it in. The name and email fields are optional. If you leave "
         "them blank, your comment shows up as “Anonymous.”"),
        ("Can I comment on more than one screen?",
         "Yes — click through as many of the listed screens as you want and leave a "
         "comment on each, or just the ones you have something to say about."),
        ("What happens after I submit a comment?",
         "It's saved right away and the person running the review gets an email. They'll "
         "mark it Accepted, Deferred, Rejected, or Resolved once they've looked at it — "
         "you don't need to do anything else."),
        ("I made a mistake in my comment — can I edit it?",
         "Not directly, but you can just submit a new comment clarifying or correcting it. "
         "All comments stay visible, so context isn't lost."),
        ("Does this affect the real app or real data?",
         "No. This page only shows a description of how a screen works — it's not "
         "connected to real orders, real inventory, or real customer data. You can't "
         "accidentally change anything by using it."),
    ]
    for q, a in faqs:
        story.append(Paragraph(q, H2))
        story.append(Paragraph(a, BODY))
    story.append(Spacer(1, 10))

    # ---- Quick reference card -----------------------------------------------------------
    story.append(HRFlowable(width="100%", thickness=2, color=RUST, spaceAfter=10))
    story.append(Paragraph("Quick Reference", SECTION))
    ref_data = [
        ["What", "A webpage showing how an app screen works, with a comment box under it."],
        ["Why", "So the people doing the real work can catch problems and suggest fixes early."],
        ["Where", "The link you were sent — no login needed. Keep it private."],
        ["When", "Any time — review within a few days if you can, come back anytime after."],
        ["How", "Open link → pick a screen → read the four boxes → write a comment → submit."],
    ]
    ref_table = Table(ref_data, colWidths=[0.9 * inch, 5.6 * inch])
    ref_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), GOLD),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), INK),
        ("TEXTCOLOR", (1, 0), (1, -1), CREAM),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#4a3c2c")),
    ]))
    story.append(ref_table)
    story.append(Spacer(1, 14))
    story.append(Paragraph(
        f"Questions about this guide or the review portal itself? Contact Rudy directly. "
        f"Guide generated {datetime.now().strftime('%B %d, %Y')}.",
        META,
    ))

    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return out_path


if __name__ == "__main__":
    path = build()
    print(f"Wrote {path}")
