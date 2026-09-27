#!/usr/bin/env python3
"""Build a kid-friendly (14-year-old level) explainer PDF of the RFP benchmark
pipeline, including a real drawn diagram of the two different reading paths."""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable,
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon

# ---------------------------------------------------------------- palette --
TEXT_BLUE = colors.HexColor("#2E5FA3")     # boxes on the "typed text" path
PIC_ORANGE = colors.HexColor("#D97B29")    # boxes on the "picture" path
NEUTRAL = colors.HexColor("#555555")       # shared/neutral steps
ANSWERKEY = colors.HexColor("#2E9E5B")     # the ground-truth / answer-key box
LINE_GRAY = colors.HexColor("#888888")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("KidTitle", parent=styles["Title"], fontSize=26, spaceAfter=6))
styles.add(ParagraphStyle("KidSub", parent=styles["Normal"], fontSize=13,
                           textColor=colors.HexColor("#555555"), spaceAfter=16))
styles.add(ParagraphStyle("H1", parent=styles["Heading1"], fontSize=17,
                           textColor=colors.HexColor("#1A1A1A"), spaceBefore=18, spaceAfter=8))
styles.add(ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13,
                           textColor=TEXT_BLUE, spaceBefore=12, spaceAfter=6))
styles.add(ParagraphStyle("Body", parent=styles["Normal"], fontSize=11, leading=15.5, spaceAfter=8))
styles.add(ParagraphStyle("BodyBold", parent=styles["Body"], fontName="Helvetica-Bold"))
styles.add(ParagraphStyle("Caption", parent=styles["Normal"], fontSize=9,
                           textColor=colors.HexColor("#666666"), alignment=TA_CENTER, spaceAfter=14))
styles.add(ParagraphStyle("Callout", parent=styles["Body"], fontSize=11,
                           backColor=colors.HexColor("#FFF6DA"), borderColor=colors.HexColor("#E8C468"),
                           borderWidth=1, borderPadding=10, spaceAfter=10, spaceBefore=6))


# ---------------------------------------------------------- diagram parts --
def rrect(x, y, w, h, fill, label, sub=None, text_color=colors.white, fs=10):
    """A rounded-ish box (plain rect, reportlab has no easy round-rect+text combo
    that stays crisp at small sizes) with 1-2 lines of centered text."""
    elems = [Rect(x, y, w, h, fillColor=fill, strokeColor=colors.white, strokeWidth=1.2, rx=6, ry=6)]
    if sub:
        elems.append(String(x + w / 2, y + h / 2 + 6, label, fontSize=fs, fontName="Helvetica-Bold",
                             fillColor=text_color, textAnchor="middle"))
        elems.append(String(x + w / 2, y + h / 2 - 8, sub, fontSize=fs - 1.5, fontName="Helvetica",
                             fillColor=text_color, textAnchor="middle"))
    else:
        elems.append(String(x + w / 2, y + h / 2 - 4, label, fontSize=fs, fontName="Helvetica-Bold",
                             fillColor=text_color, textAnchor="middle"))
    return elems


def arrow(d, x1, y1, x2, y2, color=LINE_GRAY, width=1.6):
    d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=width))
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    size = 6
    p1 = (x2, y2)
    p2 = (x2 - size * math.cos(ang - 0.4), y2 - size * math.sin(ang - 0.4))
    p3 = (x2 - size * math.cos(ang + 0.4), y2 - size * math.sin(ang + 0.4))
    d.add(Polygon([p1[0], p1[1], p2[0], p2[1], p3[0], p3[1]], fillColor=color, strokeColor=color))


def build_diagram():
    W, H = 460, 600
    d = Drawing(W, H)

    def put(x, y, w, h, fill, label, sub=None, fs=9):
        for e in rrect(x, y, w, h, fill, label, sub, fs=fs):
            d.add(e)

    # Row A: the PDF itself
    put(140, 552, 180, 34, NEUTRAL, "The RFP", "(a 30-40 page rulebook)")

    # branch down to two reading methods
    arrow(d, 190, 552, 90, 502)
    arrow(d, 270, 552, 370, 502)

    # Row B: two reading methods
    put(15, 466, 150, 36, TEXT_BLUE, "Typed-out TEXT", "(copied out of the PDF)")
    put(295, 466, 150, 36, PIC_ORANGE, "a PICTURE", "(a photo of the page)")

    # Row C: who uses which
    arrow(d, 55, 466, 55, 424)
    arrow(d, 125, 466, 125, 424)
    arrow(d, 335, 466, 335, 424)
    arrow(d, 405, 466, 405, 424)

    put(10, 388, 90, 36, TEXT_BLUE, "GPT-4o", "reads TEXT")
    put(110, 388, 90, 36, TEXT_BLUE, "Llama", "reads TEXT")
    put(280, 388, 90, 36, PIC_ORANGE, "Qwen", "reads PICTURE")
    put(380, 388, 90, 36, ANSWERKEY, "ME", "reads PICTURE")

    # converge down to the questions box
    for cx in (55, 155, 325, 425):
        arrow(d, cx, 388, 230, 348)

    put(65, 314, 330, 34, NEUTRAL, "Everyone gets asked the SAME 17 questions")

    arrow(d, 230, 314, 230, 272)
    put(55, 226, 350, 40, NEUTRAL, "Check: did you make that up, or is it really",
        "on the page? (only for the 3 AI readers)", fs=8.5)

    arrow(d, 230, 226, 230, 184)
    put(70, 140, 320, 36, ANSWERKEY, "Compare every answer to MY answer key")

    arrow(d, 230, 140, 230, 98)
    put(120, 56, 220, 40, colors.HexColor("#333333"), "SCOREBOARD", "who got the most right?")

    # legend
    ly = 40
    for i, (c, t) in enumerate([(TEXT_BLUE, "reads typed-out text"),
                                 (PIC_ORANGE, "reads a picture of the page"),
                                 (ANSWERKEY, "answer key (also a picture-reader)")]):
        d.add(Rect(15, ly - i * 14, 10, 10, fillColor=c, strokeColor=None))
        d.add(String(30, ly - i * 14 + 1, t, fontSize=7.5, fillColor=colors.HexColor("#333333")))

    return d


# --------------------------------------------------------------- content --
story = []

story.append(Spacer(1, 30))
story.append(Paragraph("Which AI Reads a Rulebook Best?", styles["KidTitle"]))
story.append(Paragraph("A kid-level explanation of how we tested 3 AIs on the same 17 questions "
                        "— and the sneaky problem we found along the way.", styles["KidSub"]))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CCCCCC"), spaceAfter=14))

story.append(Paragraph("The Big Idea", styles["H1"]))
story.append(Paragraph(
    "Imagine a company writes a giant rulebook — 30 to 40 pages — that says things like "
    "“your application is due March 10th” and “you need $5,000,000 of insurance.” "
    "That rulebook is called an <b>RFP</b>. We wanted to know: if you hand this rulebook to three "
    "different AIs and ask each one the same 17 questions about it, which one gets the most right?",
    styles["Body"]))

story.append(Paragraph("Meet the 3 Readers", styles["H1"]))
tbl = Table([
    ["Reader", "Personality", "Costs money?"],
    ["GPT-4o", "The smart kid you hire over the internet", "Yes, a few cents per question"],
    ["Llama-3.3-70B", "A smart roommate who lives on our own computer, a bit slow", "No, it's ours"],
    ["Qwen3-VL-32B", "Another smart roommate, medium speed", "No, it's ours"],
], colWidths=[110, 260, 150])
tbl.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E5FA3")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 9.5),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
    ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
]))
story.append(tbl)
story.append(Spacer(1, 6))

story.append(PageBreak())
story.append(Paragraph("The Whole Pipeline, Drawn Out", styles["H1"]))
story.append(Paragraph(
    "Here's every step, top to bottom. The colors matter — blue means "
    "“this one only reads typed-out text,” orange means “this one only looks at a "
    "picture of the page.”", styles["Body"]))
story.append(build_diagram())
story.append(Paragraph("Follow the arrows: the same rulebook splits into two completely different "
                        "things — typed text, or a photo — before it even reaches anyone.",
                        styles["Caption"]))

story.append(PageBreak())
story.append(Paragraph("Step by Step, in Plain Words", styles["H1"]))

steps = [
    ("1. Get the rulebook", "We start with a real RFP — an actual PDF a real company sent out."),
    ("2. Split it two ways", "One copy gets typed out as plain text (like copy-pasting it). "
     "Another copy gets turned into pictures, one photo per page — nothing is typed out, "
     "it's literally just an image, like a screenshot."),
    ("3. Hand it to the readers", "GPT-4o and Llama only ever see the typed-out text version. "
     "Qwen only ever sees the picture version. Neither one gets both."),
    ("4. Ask the same 17 questions", "Things like “when is this due?” and “how much "
     "insurance is needed?” Every reader is asked to also point to <i>which page</i> and "
     "<i>copy the exact sentence</i> that proves their answer."),
    ("5. Catch anyone making stuff up", "For every answer, we check: does that exact sentence they "
     "copied really exist on that page? If a reader invents an answer that isn't actually in the "
     "document, this step catches it — like checking someone's homework citations."),
    ("6. Make an answer key", "Since nobody knows the *true* answers yet, someone has to actually "
     "read the whole rulebook and write down what's really true. That job fell to me (the AI writing "
     "this explanation) — and I read it the SAME way Qwen does: by looking at pictures of the "
     "pages, not the typed-out text."),
    ("7. Grade everyone", "Compare each reader's 17 answers against the answer key. Score it."),
]
for title, body in steps:
    story.append(Paragraph(title, styles["H2"]))
    story.append(Paragraph(body, styles["Body"]))

story.append(PageBreak())
story.append(Paragraph("The Sneaky Problem", styles["H1"]))
story.append(Paragraph(
    "Here's the catch, and it's a real one. Sometimes when you copy text out of a PDF automatically, "
    "tables get scrambled. Imagine a table that says:", styles["Body"]))
story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;Cost — 30 points", styles["BodyBold"]))
story.append(Paragraph(
    "and the auto-copy accidentally spits out “30 Cost points” instead — same words, "
    "wrong order. Someone looking at a picture of the table would never make that mistake. Someone "
    "reading the scrambled copy-paste version might get confused through absolutely no fault of "
    "their own.", styles["Body"]))
story.append(Paragraph(
    "Since I made the answer key by looking at PICTURES — the same way Qwen reads — "
    "grading Qwen against my answer key is a fair fight. But grading GPT-4o or Llama against my "
    "answer key isn't quite fair: they never even saw what I saw. If their typed-out copy of a page "
    "got scrambled somewhere, that's not their mistake, and I only spot-checked ONE page out of 33 "
    "to see if the copy-paste matched the picture.", styles["Callout"]))

story.append(Paragraph("The Scoreboard (so far)", styles["H1"]))
tbl2 = Table([
    ["Reader", "Reads", "Score so far", "Fair comparison to my answer key?"],
    ["GPT-4o", "typed text", "70.6%*", "Not fully — different reading method"],
    ["Qwen3-VL-32B", "pictures", "64.7%", "Yes — same reading method as me"],
    ["Llama-3.3-70B", "typed text", "52.9%", "Not fully — different reading method"],
], colWidths=[110, 90, 100, 220])
tbl2.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#333333")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 9.5),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#E2EFDA")),
    ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
]))
story.append(tbl2)
story.append(Paragraph("*GPT-4o's score also has an asterisk for an unrelated reason: our OpenAI "
                        "account hit a spending limit partway through, so 2 of its 17 answers are "
                        "from an older, slightly buggy run.", styles["Caption"]))

story.append(Paragraph("What We Still Don't Know", styles["H1"]))
story.append(Paragraph(
    "Whether the typed-out text version of the rulebook actually matches the picture version, "
    "page by page. We checked exactly one page out of 33 and it matched perfectly — but one "
    "page isn't proof for the whole document. Until every page is checked, GPT-4o's and Llama's "
    "scores come with an honest asterisk.", styles["Body"]))

doc = SimpleDocTemplate(
    "/home/ubuntu/aidc/project-qwen-rfp/Kid-Friendly-Pipeline-Explainer.pdf",
    pagesize=letter, topMargin=50, bottomMargin=50, leftMargin=56, rightMargin=56,
    title="Which AI Reads a Rulebook Best?",
)
doc.build(story)
print("wrote Kid-Friendly-Pipeline-Explainer.pdf")
