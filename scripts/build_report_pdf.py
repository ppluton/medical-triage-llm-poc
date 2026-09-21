#!/usr/bin/env python3
"""Render the technical report to an A4 PDF with Mermaid diagrams.

Usage: uv run --with markdown python scripts/build_report_pdf.py \
  --source reports/RAPPORT_TECHNIQUE_POC.md --output output/report.pdf
"""

import argparse
import re
import subprocess
import tempfile
from html import escape
from pathlib import Path

import markdown

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
MERMAID = "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"

CSS = """
@page { size: A4; margin: 16mm 15mm 16mm 15mm; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; font-size: 9.6pt;
       line-height: 1.42; color: #1c2430; }
h1 { font-size: 19pt; color: #0f3d4f; margin: 0 0 4pt; }
h2 { font-size: 13.5pt; color: #154c62; border-bottom: 1px solid #c9d6dd; padding-bottom: 2pt;
     margin: 14pt 0 5pt; break-after: avoid; }
h3 { font-size: 11pt; color: #154c62; margin: 10pt 0 3pt; break-after: avoid; }
h4 { font-size: 10pt; margin: 7pt 0 2pt; break-after: avoid; }
p, li { margin: 0 0 4pt; }
ul, ol { margin: 0 0 5pt; padding-left: 16pt; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 8pt; font-size: 8.4pt;
        break-inside: avoid; }
th, td { border: 1px solid #c9d6dd; padding: 2.5pt 4pt; vertical-align: top; }
th { background: #eaf1f4; text-align: left; }
code { font-family: Menlo, monospace; font-size: 8.2pt; background: #f2f4f6; padding: 0 2px;
       overflow-wrap: anywhere; }
blockquote { border-left: 3px solid #154c62; margin: 6pt 0; padding: 2pt 8pt;
             background: #f4f8fa; }
hr { display: none; }
pre.mermaid { text-align: center; margin: 6pt 0 10pt; break-inside: avoid; }
pre.mermaid svg { max-width: 100%; max-height: 340pt; }
a { color: #154c62; text-decoration: none; }
"""


def to_html(source: str) -> str:
    blocks: list[str] = []

    def stash(match: re.Match) -> str:
        blocks.append(match.group(1))
        return f"\n\nMERMAIDBLOCK{len(blocks) - 1}\n\n"

    source = re.sub(r"```mermaid\n(.*?)```", stash, source, flags=re.S)
    body = markdown.markdown(source, extensions=["tables", "fenced_code", "sane_lists"])
    for index, block in enumerate(blocks):
        body = body.replace(
            f"<p>MERMAIDBLOCK{index}</p>", f'<pre class="mermaid">{escape(block)}</pre>'
        )
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8">
<style>{CSS}</style>
<script src="{MERMAID}"></script>
<script>mermaid.initialize({{startOnLoad: true, theme: "neutral",
  themeVariables: {{fontSize: "15px"}}, flowchart: {{useMaxWidth: true}}}});</script>
</head><body>{body}</body></html>"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        html = Path(tmp) / "report.html"
        html.write_text(to_html(args.source.read_text()), encoding="utf-8")
        subprocess.run(
            [
                CHROME,
                "--headless",
                "--disable-gpu",
                "--no-pdf-header-footer",
                "--virtual-time-budget=15000",
                f"--print-to-pdf={args.output.resolve()}",
                html.as_uri(),
            ],
            check=True,
            capture_output=True,
        )
    print(args.output)


if __name__ == "__main__":
    main()
