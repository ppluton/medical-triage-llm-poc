#!/usr/bin/env python3
"""Render the versioned final-candidate report without changing its evidence claims."""

import argparse
import re
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Fresh output path required")
    styles = getSampleStyleSheet()
    styles["BodyText"].fontSize = 10
    styles["BodyText"].leading = 14
    styles["BodyText"].spaceAfter = 8
    styles["BodyText"].alignment = TA_LEFT
    styles["BodyText"].splitLongWords = True
    styles["Heading1"].fontSize = 19
    styles["Heading1"].leading = 23
    styles["Heading2"].keepWithNext = True
    styles["Heading2"].fontSize = 13
    styles["Heading2"].textColor = colors.HexColor("#154c62")
    styles["Heading3"].keepWithNext = True
    styles["Heading3"].fontSize = 11
    styles["Heading3"].leading = 14
    styles["Heading3"].textColor = colors.HexColor("#154c62")

    def inline(text):
        text = re.sub(
            r"\[([^]]+)\]\(([^)]+)\)",
            lambda m: m[1] + (" (" + m[2] + ")" if "://" in m[2] else ""),
            text,
        )
        text = escape(text.replace("—", "-").replace("–", "-").replace("≤", "<="))
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        return text.replace("`", "")

    story = []
    lines = args.source.read_text().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = lines[i].strip().strip("|").split("|")
                if not all(re.fullmatch(r"[ :\-]+", c) for c in cells):
                    rows.append([Paragraph(inline(c.strip()), styles["BodyText"]) for c in cells])
                i += 1
            table = Table(rows, colWidths=[483 / len(rows[0])] * len(rows[0]), repeatRows=1)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6eff3")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#b7c8d0")),
                        ("LEFTPADDING", (0, 0), (-1, -1), 7),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ]
                )
            )
            story.extend([table, Spacer(1, 12)])
            continue
        style = styles["BodyText"]
        if line.startswith("# "):
            style, line = styles["Heading1"], line[2:]
        elif line.startswith("## "):
            style, line = styles["Heading2"], line[3:]
        elif line.startswith("### "):
            style, line = styles["Heading3"], line[4:]
        story.append(Paragraph(inline(line), style))
        i += 1

    def footer(canvas, doc):
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#526575"))
        canvas.drawString(
            56,
            28,
            "CHSA | Candidat final - POC pédagogique, sans validation clinique",
        )
        canvas.drawRightString(539, 28, str(doc.page))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(
        str(args.output),
        pagesize=(595, 842),
        leftMargin=56,
        rightMargin=56,
        topMargin=45,
        bottomMargin=48,
        title="POC CHSA - rapport technique final",
    ).build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    main()
