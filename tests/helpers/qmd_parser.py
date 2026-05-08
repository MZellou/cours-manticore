"""Extract SQL/Cypher code blocks from .qmd corrigé files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

CORRIGES_DIR = Path(__file__).resolve().parent.parent.parent / "corriges"


@dataclass
class Query:
    id: str
    lang: str  # "sql" | "cypher" | "python"
    code: str
    source_file: str
    section_header: str = ""


def extract_queries(
    qmd_path: Path | str, lang_filter: list[str] | None = None
) -> list[Query]:
    """Parse a .qmd file and extract all code blocks.

    Args:
        qmd_path: Path to .qmd file
        lang_filter: Only return blocks of these languages (e.g. ["sql", "cypher"])
    """
    qmd_path = Path(qmd_path)
    content = qmd_path.read_text(encoding="utf-8")
    stem = qmd_path.stem
    queries: list[Query] = []

    # Find section headers (## Title) to label queries contextually
    lines = content.split("\n")
    current_section = ""
    idx = 0

    # Regex: ```sql ... ``` or ```sql ... ```
    pattern = re.compile(r"```(sql|cypher|python)\s*\n(.*?)```", re.DOTALL)

    for match in pattern.finditer(content):
        lang = match.group(1)
        if lang_filter and lang not in lang_filter:
            continue

        code = match.group(2).strip()
        if not code:
            continue

        # Find which section this block belongs to
        block_start = match.start()
        current_section = _find_section_before(content, block_start)

        queries.append(
            Query(
                id=f"{stem}_{idx:03d}",
                lang=lang,
                code=code,
                source_file=stem,
                section_header=current_section,
            )
        )
        idx += 1

    return queries


def _find_section_before(content: str, pos: int) -> str:
    """Find the last ## header before position `pos`."""
    lines_before = content[:pos].split("\n")
    for line in reversed(lines_before):
        line = line.strip()
        if line.startswith("## "):
            return line[3:].strip()
    return ""


def load_all_corriges(lang_filter: list[str] | None = None) -> dict[str, list[Query]]:
    """Load queries from all corrigé .qmd files.

    Returns:
        {filename_stem: [Query, ...]}
    """
    result = {}
    for qmd in sorted(CORRIGES_DIR.glob("*.qmd")):
        queries = extract_queries(qmd, lang_filter=lang_filter)
        if queries:
            result[qmd.stem] = queries
    return result


# --- Template detection & fixup ---

# Patterns that indicate a template query (non-executable as-is)
TEMPLATE_PATTERNS = [
    r"source_vertex",
    r"target_vertex",
    r"<edge\d*>",
    r"votre_table",
    r"vos_filtres",
    r"votre_role",
    r"src,\s*tgt",
    r"<attaquées>",
    r"<protégées>",
    r"<edge1>",
    r"<edge2>",
    r"<edge3>",
]

_TEMPLATE_RE = re.compile(
    "|".join(TEMPLATE_PATTERNS),
    re.IGNORECASE,
)


def is_template(code: str) -> bool:
    """Check if a query contains unresolved placeholders."""
    return bool(_TEMPLATE_RE.search(code))
