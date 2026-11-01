#!/usr/bin/env python3
"""kb.py — manage a project literature knowledge base.

Usage:
    python kb.py [--root reference/literature] add --key K --title T --authors A --year Y \
        [--journal J] [--doi D] [--pmid P] [--tags t1,t2]
    python kb.py [--root reference/literature] bib
    python kb.py [--root reference/literature] index
    python kb.py [--root reference/literature] find TERM
    python kb.py [--root reference/literature] check
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

CITEKEY_RE = re.compile(r"^[a-z]+\d{4}[a-z0-9]*$")
DEFAULT_ROOT = "reference/literature"

FIELD_ORDER = (
    "citekey",
    "title",
    "authors",
    "year",
    "journal",
    "doi",
    "pmid",
    "status",
    "added",
    "tags",
    "used_in",
)

STATUSES = ("to-read", "summarized", "verified")

TEMPLATE_BODY = """## Summary

TODO

## Key findings

- TODO (p. TODO)

## What we use from it

- TODO (TODO)

## Quotes (verified)

- "TODO" (p.TODO)

## Notes

TODO
"""


def read_paper(path: Path) -> tuple[dict[str, str], str] | None:
    """Parse a paper markdown file with simple YAML frontmatter; return (metadata, body) or None."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None

    meta: dict[str, str] = {}
    i = 1
    while i < len(lines) and lines[i].strip() != "---":
        line = lines[i]
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
        i += 1

    if i >= len(lines):
        return None

    body = "\n".join(lines[i + 1 :])
    return meta, body


def load_papers(root: Path) -> list[tuple[Path, dict[str, str], str]]:
    """Load all valid paper files under root/papers; return list of (path, metadata, body)."""
    papers_dir = root / "papers"
    if not papers_dir.is_dir():
        return []

    papers: list[tuple[Path, dict[str, str], str]] = []
    for path in sorted(papers_dir.glob("*.md")):
        parsed = read_paper(path)
        if parsed is None:
            continue
        meta, body = parsed
        papers.append((path, meta, body))
    return papers


def render_paper(meta: dict[str, str]) -> str:
    """Render a complete paper markdown file from frontmatter fields and the body template."""
    lines = ["---"]
    for key in FIELD_ORDER:
        lines.append(f"{key}: {meta.get(key, '')}")
    lines.append("---")
    return "\n".join(lines) + "\n\n" + TEMPLATE_BODY


def _cell(value: str) -> str:
    """Make a string safe for a markdown table cell."""
    return value.replace("|", "\\|").replace("\n", " ").strip()


def _first_author_surname(meta: dict[str, str]) -> str:
    """Return the surname of the first author from a semicolon-separated author list."""
    first = meta.get("authors", "").split(";")[0].strip()
    if not first:
        return ""
    if "," in first:
        return first.split(",", 1)[0].strip()
    return first


def _year_int(value: str) -> int:
    """Parse a year string as an integer, returning 0 when invalid."""
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return 0


def build_bib(papers: list[tuple[Path, dict[str, str], str]]) -> str:
    """Build library.bib content from paper metadata as @article entries."""
    entries: list[str] = []

    for _, meta, _ in sorted(papers, key=lambda item: item[1].get("citekey", "")):
        citekey = meta.get("citekey", "").strip()
        if not citekey:
            continue

        authors = " and ".join(
            author.strip() for author in meta.get("authors", "").split(";") if author.strip()
        )

        fields: list[str] = []
        for name in ("author", "title", "journal", "year", "doi", "pmid"):
            value = authors if name == "author" else meta.get(name, "").strip()
            if value:
                fields.append(f"  {name} = {{{value}}},")

        field_text = "\n".join(fields)
        if field_text.endswith(","):
            field_text = field_text[:-1]

        if field_text:
            entries.append(f"@article{{{citekey},\n{field_text}\n}}")
        else:
            entries.append(f"@article{{{citekey},\n}}")

    return "\n\n".join(entries) + ("\n" if entries else "")


def build_index(papers: list[tuple[Path, dict[str, str], str]]) -> str:
    """Build INDEX.md content as a markdown table sorted by year descending."""
    counts = {status: 0 for status in STATUSES}
    for _, meta, _ in papers:
        status = meta.get("status", "").strip()
        if status in counts:
            counts[status] += 1

    lines: list[str] = [
        "# Literature Index",
        "",
        "Counts: " + ", ".join(f"{status}={counts[status]}" for status in STATUSES),
        "",
        "| citekey | year | first author | title | status | tags | used_in |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    def sort_key(item: tuple[Path, dict[str, str], str]) -> tuple[int, str]:
        meta = item[1]
        return (-_year_int(meta.get("year", "0")), meta.get("citekey", ""))

    for _, meta, _ in sorted(papers, key=sort_key):
        citekey = meta.get("citekey", "").strip()
        year = _cell(meta.get("year", ""))
        first_author = _cell(_first_author_surname(meta))
        title = _cell(meta.get("title", ""))
        status = _cell(meta.get("status", ""))
        tags = _cell(meta.get("tags", ""))
        used_in = _cell(meta.get("used_in", ""))
        lines.append(
            f"| [{citekey}](papers/{citekey}.md) | {year} | {first_author} | "
            f"{title} | {status} | {tags} | {used_in} |"
        )

    return "\n".join(lines) + "\n"


def rebuild_bib(root: Path) -> None:
    """Regenerate root/library.bib from all papers."""
    root.mkdir(parents=True, exist_ok=True)
    content = build_bib(load_papers(root))
    (root / "library.bib").write_text(content, encoding="utf-8")


def rebuild_index(root: Path) -> None:
    """Regenerate root/INDEX.md from all papers."""
    root.mkdir(parents=True, exist_ok=True)
    content = build_index(load_papers(root))
    (root / "INDEX.md").write_text(content, encoding="utf-8")


def parse_sections(body: str) -> dict[str, str]:
    """Split a markdown body into `## Heading` sections; return heading -> content."""
    sections: dict[str, str] = {}
    current: str | None = None
    buffer: list[str] = []

    for line in body.splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(buffer).strip()
            current = line[3:].strip()
            buffer = []
        elif current is not None:
            buffer.append(line)

    if current is not None:
        sections[current] = "\n".join(buffer).strip()

    return sections


def cmd_add(root: Path, args: argparse.Namespace) -> int:
    """Create a new paper file from the template, refusing duplicates, then rebuild bib/index."""
    if not CITEKEY_RE.match(args.key):
        print(f"error: invalid citekey {args.key!r}", file=sys.stderr)
        return 2

    papers_dir = root / "papers"
    path = papers_dir / f"{args.key}.md"

    if path.exists():
        print("exists")
        return 0

    if args.doi.strip():
        wanted = args.doi.strip().lower()
        for _, meta, _ in load_papers(root):
            if meta.get("doi", "").strip().lower() == wanted:
                print(
                    f"error: duplicate DOI {args.doi!r} (used by {meta.get('citekey', '?')})",
                    file=sys.stderr,
                )
                return 2

    papers_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "citekey": args.key,
        "title": args.title,
        "authors": args.authors,
        "year": str(args.year),
        "journal": args.journal,
        "doi": args.doi,
        "pmid": args.pmid,
        "status": "to-read",
        "added": dt.date.today().isoformat(),
        "tags": args.tags,
        "used_in": "",
    }

    path.write_text(render_paper(meta), encoding="utf-8")
    rebuild_bib(root)
    rebuild_index(root)
    print(f"added {args.key}")
    return 0


def cmd_bib(root: Path) -> int:
    """Regenerate library.bib."""
    rebuild_bib(root)
    return 0


def cmd_index(root: Path) -> int:
    """Regenerate INDEX.md."""
    rebuild_index(root)
    return 0


def cmd_find(root: Path, term: str) -> int:
    """Case-insensitive search across papers; print `citekey: matching line` for each hit."""
    needle = term.lower()
    papers_dir = root / "papers"

    if papers_dir.is_dir():
        for path in sorted(papers_dir.glob("*.md")):
            citekey = path.stem
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue
            for line in lines:
                if needle in line.lower():
                    print(f"{citekey}: {line.rstrip()}")

    return 0


def cmd_check(root: Path) -> int:
    """Report papers needing work; return 1 when any problem is found."""
    problems: list[tuple[str, list[str]]] = []

    for _, meta, body in load_papers(root):
        citekey = meta.get("citekey", "").strip() or "?"
        reasons: list[str] = []

        if meta.get("status", "").strip() == "to-read":
            reasons.append("status is to-read")

        sections = parse_sections(body)
        for section in ("Summary", "What we use from it"):
            content = sections.get(section, "")
            if not content:
                reasons.append(f"{section} is empty")
            elif "TODO" in content:
                reasons.append(f"{section} contains TODO")

        if reasons:
            problems.append((citekey, reasons))

    for citekey, reasons in problems:
        print(f"{citekey}: {'; '.join(reasons)}")

    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point; return process exit code."""
    parser = argparse.ArgumentParser(prog="kb.py", description="Project literature knowledge base")
    parser.add_argument(
        "--root",
        default=DEFAULT_ROOT,
        help=f"root directory of the knowledge base (default: {DEFAULT_ROOT})",
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="add a paper from the template")
    p_add.add_argument("--key", required=True, help="citekey, e.g. smith2024")
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--authors", required=True, help='semicolon-separated "Last, First"')
    p_add.add_argument("--year", required=True)
    p_add.add_argument("--journal", default="")
    p_add.add_argument("--doi", default="")
    p_add.add_argument("--pmid", default="")
    p_add.add_argument("--tags", default="")

    sub.add_parser("bib", help="regenerate library.bib")
    sub.add_parser("index", help="regenerate INDEX.md")

    p_find = sub.add_parser("find", help="search papers")
    p_find.add_argument("term")

    sub.add_parser("check", help="report papers needing work")

    args = parser.parse_args(argv)
    root = Path(args.root)

    if args.cmd == "add":
        return cmd_add(root, args)
    if args.cmd == "bib":
        return cmd_bib(root)
    if args.cmd == "index":
        return cmd_index(root)
    if args.cmd == "find":
        return cmd_find(root, args.term)
    if args.cmd == "check":
        return cmd_check(root)

    parser.error(f"unknown command {args.cmd!r}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
