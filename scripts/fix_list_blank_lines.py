#!/usr/bin/env python3
"""Insert missing blank lines before lists in Quarto .qmd files.

Fixes rendering issues on GitHub Pages where lists glued to the
previous paragraph don't render as proper list blocks.
"""

import re
from pathlib import Path

PAGES_DIR = Path(__file__).resolve().parent.parent / "pages"
LIST_RE = re.compile(r"^\s*([-*+]|\d+\.)\s")


def fix_file(filepath: Path) -> int:
    """Return number of blank lines inserted."""
    lines = filepath.read_text().splitlines(keepends=True)
    in_code_block = False
    result = []
    inserted = 0

    for i, line in enumerate(lines):
        stripped = line.strip()

        # Track fenced code blocks
        if stripped.startswith("```"):
            in_code_block = not in_code_block

        result.append(line)

        # Insert blank line before list if missing
        if (
            not in_code_block
            and i + 1 < len(lines)
            and stripped  # current line is not empty
            and not stripped.startswith(("#", ">", "---", ":::", "```", "|"))
            and not LIST_RE.match(stripped)  # not a list item itself
            and LIST_RE.match(lines[i + 1].lstrip())  # next line IS a list
        ):
            result.append("\n")
            inserted += 1

    if inserted:
        filepath.write_text("".join(result))

    return inserted


def main():
    total = 0
    for f in sorted(PAGES_DIR.rglob("*.qmd")):
        n = fix_file(f)
        if n:
            print(f"  {f.relative_to(PAGES_DIR.parent)}: {n} fix(es)")
            total += n
    print(f"\nTotal: {total} blank line(s) inserted")


if __name__ == "__main__":
    main()
