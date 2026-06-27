#!/usr/bin/env python3
"""Build a single self-contained HTML study pack from ordered Markdown files."""

from __future__ import annotations

import argparse
import base64
import mimetypes
import re
import sys
from pathlib import Path

try:
    import markdown
except ImportError:
    print(
        "Missing dependency: python-markdown. Install it with "
        "`python3 -m pip install markdown` and rerun this script.",
        file=sys.stderr,
    )
    raise SystemExit(1)


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return slug or "section"


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def rewrite_images(markdown_text: str, source: Path) -> str:
    def repl(match: re.Match[str]) -> str:
        alt = match.group(1)
        target = match.group(2)
        if "://" in target or target.startswith("data:"):
            return match.group(0)
        img = (source.parent / target).resolve()
        if not img.exists():
            return match.group(0)
        return f"![{alt}]({data_uri(img)})"

    return re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", repl, markdown_text)


def rewrite_links(markdown_text: str, source: Path, root: Path) -> str:
    def repl(match: re.Match[str]) -> str:
        label = match.group(1)
        target = match.group(2)
        if target.startswith("#") or "://" in target or target.startswith("mailto:"):
            return match.group(0)
        clean = target.split("#", 1)[0]
        if clean.endswith(".md"):
            linked = (source.parent / clean).resolve()
            try:
                rel = linked.relative_to(root).as_posix()
            except ValueError:
                return match.group(0)
            return f"[{label}](#{slugify(rel)})"
        return match.group(0)

    return re.sub(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)", repl, markdown_text)


def escape_angle_brackets(markdown_text: str) -> str:
    escaped_lines: list[str] = []
    for line in markdown_text.splitlines():
        if line.startswith(">"):
            escaped_lines.append(">" + line[1:].replace("<", "&lt;").replace(">", "&gt;"))
        else:
            escaped_lines.append(line.replace("<", "&lt;").replace(">", "&gt;"))
    return "\n".join(escaped_lines)


def protect_display_math(markdown_text: str) -> tuple[str, list[str]]:
    blocks: list[str] = []

    def repl(match: re.Match[str]) -> str:
        blocks.append(match.group(0))
        return f"\n\n@@MATH_BLOCK_{len(blocks) - 1}@@\n\n"

    return re.sub(r"\$\$.*?\$\$", repl, markdown_text, flags=re.S), blocks


def restore_display_math(rendered: str, blocks: list[str]) -> str:
    for i, block in enumerate(blocks):
        placeholder = f"@@MATH_BLOCK_{i}@@"
        rendered = rendered.replace(f"<p>{placeholder}</p>", block)
        rendered = rendered.replace(placeholder, block)
    return rendered


def load_combined_markdown(root: Path, docs: list[Path]) -> str:
    parts: list[str] = []
    for doc in docs:
        source = doc if doc.is_absolute() else root / doc
        source = source.resolve()
        text = source.read_text(encoding="utf-8")
        text = rewrite_images(text, source)
        text = rewrite_links(text, source, root)
        text = escape_angle_brackets(text)
        rel = source.relative_to(root).as_posix()
        parts.append(f'<a id="{slugify(rel)}"></a>\n\n')
        parts.append(f"# {rel}\n\n")
        parts.append(text)
        parts.append('\n\n<div class="page-break"></div>\n\n')
    return "".join(parts)


def convert_markdown(markdown_text: str) -> str:
    protected_text, math_blocks = protect_display_math(markdown_text)
    rendered = markdown.markdown(
        protected_text,
        extensions=["extra", "tables", "fenced_code", "toc", "sane_lists"],
        output_format="html5",
    )
    return restore_display_math(rendered, math_blocks)


def html_page(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <script>
    window.MathJax = {{
      tex: {{
        inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
        displayMath: [['$$', '$$']],
        processEscapes: true
      }},
      svg: {{ fontCache: 'global' }}
    }};
  </script>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
  <style>
    :root {{
      color-scheme: light;
      --ink: #151515;
      --muted: #5b6470;
      --line: #d9dee7;
      --soft: #f6f8fb;
    }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
      line-height: 1.55;
      background: white;
    }}
    main {{
      max-width: 980px;
      margin: 0 auto;
      padding: 32px 28px 80px;
    }}
    h1, h2, h3, h4 {{
      line-height: 1.2;
      margin: 1.5em 0 0.55em;
    }}
    h1 {{
      border-bottom: 2px solid var(--line);
      padding-bottom: 0.25em;
    }}
    a {{ color: #174ea6; }}
    code {{
      background: var(--soft);
      padding: 0.1em 0.25em;
      border-radius: 4px;
    }}
    pre {{
      background: var(--soft);
      border: 1px solid var(--line);
      padding: 12px;
      overflow-x: auto;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      margin: 1em 0;
    }}
    th, td {{
      border: 1px solid var(--line);
      padding: 6px 8px;
      vertical-align: top;
    }}
    img {{
      display: block;
      max-width: 100%;
      height: auto;
      margin: 16px auto 28px;
      page-break-inside: avoid;
      break-inside: avoid;
    }}
    mjx-container {{
      overflow-x: auto;
      overflow-y: hidden;
      max-width: 100%;
      padding: 2px 0;
    }}
    .page-break {{
      border-top: 1px dashed var(--line);
      margin: 42px 0;
    }}
    @media print {{
      @page {{ size: A4; margin: 12mm; }}
      main {{ max-width: none; padding: 0; }}
      a {{ color: inherit; text-decoration: none; }}
      .page-break {{ page-break-after: always; border: 0; margin: 0; }}
      h1, h2, h3, h4 {{ page-break-after: avoid; break-after: avoid; }}
      p, li, table, pre {{ orphans: 3; widows: 3; }}
      p:has(img), table, pre, mjx-container {{
        page-break-inside: avoid;
        break-inside: avoid;
      }}
      h3 + p:has(img), h4 + p:has(img) {{
        page-break-before: avoid;
        break-before: avoid;
      }}
      img {{
        max-height: 245mm;
        object-fit: contain;
      }}
    }}
  </style>
</head>
<body>
<main>
{body}
</main>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("docs", nargs="+", help="Markdown files, in output order")
    parser.add_argument("--root", required=True, help="Study pack root directory")
    parser.add_argument("--title", required=True, help="HTML document title")
    parser.add_argument("--output", required=True, help="Output HTML path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    docs = [Path(doc) for doc in args.docs]
    markdown_text = load_combined_markdown(root, docs)
    body = convert_markdown(markdown_text)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html_page(args.title, body), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
