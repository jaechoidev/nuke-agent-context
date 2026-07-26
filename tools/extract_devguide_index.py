#!/usr/bin/env python3
"""Index the NDK Developer Guide as a concept -> page map.

The fifth extractor. The API extractors answer "does this symbol exist"; the
examples extractor answers "which file shows this pattern"; this one answers
"which guide page explains this part of the paradigm" -- routing a task or
concept to Foundry's own prose.

Source is each section's Sphinx `index.html` toctree, which lists every page and
its sub-headings as short navigation captions with hrefs. The index carries only
those captions and a version-pinned link to Foundry's page -- never the guide's
paragraph prose (that stays on learn.foundry.com, reached by the link). Section
framing lines are original.

Knows the Sphinx toctree shape only. Takes a directory; knows nothing about Nuke
install detection.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import html
import pathlib
import re
import sys

# A toctree entry: <a class="reference internal" href="page.html#anchor">Caption</a>.
LINK_RE = re.compile(
    r'<a class="reference internal" href="([^"]+)">([^<]+)</a>')
# Same-dir page link only: "page.html" or "page.html#anchor". No slashes
# (cross-section / _autosummary), no bare "#..." (self link). Page names may be
# mixed case (the Python guide ships 3D.html, the Blink guide QuickStart.html).
HREF_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9_-]*\.html)(?:#(.+))?$")
H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.S)
# Sphinx navigation pages that are not guide content.
SKIP_PAGES = {"index.html", "genindex.html", "search.html", "py-modindex.html",
              "modindex.html"}

# Original one-line framing for the flat single-index guides (Python, Blink).
FLAT_INTRO = {
    "pyguide": "The Python guide — scripting the node graph: knobs, animation, "
               "callbacks, custom panels, channels, threading, performance.",
    "blinkguide": "The BlinkScript guide — kernels end to end: quick start, "
                  "worked examples, library files, and the kernel reference.",
}

# Reading order + an original one-line framing per section (our words, not the
# guide's). A section found on disk but not listed here is still indexed, at the
# end, with no framing line.
SECTIONS: list[tuple[str, str]] = [
    ("intro", "Orientation: terminology, the Op architecture, building and installing plug-ins."),
    ("2d", "The 2D image pipeline — PixelIop, DrawIop, Iop, PlanarIop, channels, readers/writers."),
    ("3d-usd", "The current USD-based 3D API for geometry plug-ins."),
    ("3d", "The classic 3D system — GeoOp, attributes, geometry readers/writers."),
    ("deep", "Deep image data — DeepOp, DeepPixelOp, deep readers/writers, deep-to-2D."),
    ("particles", "Custom particle-behaviour Ops and their performance."),
    ("split-and-execute", "Shared Op machinery — input handling, time/stereo splitting, executable Ops."),
    ("knobs-and-handles", "Knobs, control panels and in-viewer handles; dynamic and custom knobs."),
    ("advanced", "The traps — hashing/caching, threading, memory, errors: correct-looking code that misbehaves."),
    ("appendixa", "Setting up projects and compilers per platform."),
    ("appendixb", "Reference appendix."),
    ("appendixc", "Plug-in compatibility across Nuke versions."),
]
SECTION_ORDER = {name: i for i, (name, _) in enumerate(SECTIONS)}
SECTION_BLURB = dict(SECTIONS)


@dataclasses.dataclass(frozen=True)
class Topic:
    section: str                 # dir name, e.g. "2d"
    page: str                    # "architecture.html"
    title: str                   # the page's toctree caption
    concepts: tuple[str, ...]    # sub-heading captions on that page
    anchors: tuple[str, ...]     # matching #anchor slugs, aligned with concepts


def _text(raw: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", raw)).replace("¶", "").strip()


def _pages_from_toctree(text: str) -> tuple[list[str], dict[str, dict]]:
    """Group a toctree's same-dir links into ordered pages with their anchors."""
    order: list[str] = []
    pages: dict[str, dict] = {}
    for href, caption in LINK_RE.findall(text):
        m = HREF_RE.match(href)
        if not m or m.group(1) in SKIP_PAGES:
            continue                       # cross-dir, self, or a nav page
        page, anchor = m.group(1), m.group(2)
        cap = _text(caption)
        if page not in pages:
            order.append(page)
            pages[page] = {"title": None, "concepts": [], "anchors": []}
        if anchor:
            pages[page]["concepts"].append(cap)
            pages[page]["anchors"].append(anchor)
        elif pages[page]["title"] is None:
            pages[page]["title"] = cap
    return order, pages


def _topics(order, pages, section: str) -> list[Topic]:
    return [Topic(section, page, pages[page]["title"] or page,
                  tuple(pages[page]["concepts"]), tuple(pages[page]["anchors"]))
            for page in order]


def parse_section(index_html: pathlib.Path, section: str) -> list[Topic]:
    """Turn one section's index.html toctree into per-page Topics (sectioned guide)."""
    order, pages = _pages_from_toctree(index_html.read_text(errors="replace"))
    return _topics(order, pages, section)


def build_flat(guide_dir: pathlib.Path) -> list[Topic]:
    """A flat guide (Python, Blink): one top-level index.html over sibling pages.

    Section is empty -- the public URL has no section segment -- and the
    _autosummary API pages the toctree also lists are excluded (they are covered
    by the API index, and their hrefs carry a slash)."""
    idx = pathlib.Path(guide_dir) / "index.html"
    order, pages = _pages_from_toctree(idx.read_text(errors="replace"))
    return _topics(order, pages, "")


def build_index(guide_dir: pathlib.Path) -> list[Topic]:
    guide = pathlib.Path(guide_dir)
    found = [d.name for d in guide.iterdir()
             if d.is_dir() and (d / "index.html").is_file()
             and not d.name.startswith("_")]
    ordered = sorted(found, key=lambda s: (SECTION_ORDER.get(s, len(SECTIONS)), s))
    topics: list[Topic] = []
    for section in ordered:
        topics.extend(parse_section(guide / section / "index.html", section))
    return topics


def doc_url(section: str, page: str, doc_base: str, anchor: str | None = None) -> str:
    base = doc_base.rstrip("/")
    url = f"{base}/{section}/{page}" if section else f"{base}/{page}"
    return f"{url}#{anchor}" if anchor else url


def section_title(topics: list[Topic]) -> str:
    """Human label for a section: its blurb key wins, else the dir name."""
    return topics[0].section if topics else ""


def render_index_md(topics: list[Topic], doc_base: str) -> str:
    by_section: dict[str, list[Topic]] = {}
    for t in topics:
        by_section.setdefault(t.section, []).append(t)
    pages = len(topics)
    out = [
        "# NDK dev guide — concept → page map",
        "",
        f"{pages} pages across {len(by_section)} sections of the NDK Developer "
        "Guide. Routing only: to understand a part of the paradigm, open the "
        "linked Foundry page and read it there.",
        "",
    ]
    for section in sorted(by_section, key=lambda s: (SECTION_ORDER.get(s, len(SECTIONS)), s)):
        out.append(f"## {section}")
        blurb = SECTION_BLURB.get(section)
        if blurb:
            out.append("")
            out.append(blurb)
        out.append("")
        for t in by_section[section]:
            out.append(f"- **{t.title}** — {doc_url(t.section, t.page, doc_base)}")
            if t.concepts:
                out.append("  " + " · ".join(t.concepts))
        out.append("")
    return "\n".join(out) + "\n"


def render_map(topics: list[Topic], doc_base: str) -> str:
    """Flat, greppable: one row per concept (plus one per page). concept -> URL."""
    rows = ["section\tpage_title\tconcept\turl"]
    for t in topics:
        rows.append(f"{t.section}\t{t.title}\t\t{doc_url(t.section, t.page, doc_base)}")
        for concept, anchor in zip(t.concepts, t.anchors):
            rows.append(f"{t.section}\t{t.title}\t{concept}\t"
                        f"{doc_url(t.section, t.page, doc_base, anchor)}")
    return "\n".join(rows) + "\n"


def render_flat_md(topics: list[Topic], doc_base: str, title: str,
                   blurb: str = "") -> str:
    """A flat guide's page map: one list, no sections, URLs without a subdir."""
    out = [
        f"# {title} — page map",
        "",
        f"{len(topics)} pages. Routing only: to understand a topic, open the "
        "linked Foundry page and read it there.",
        "",
    ]
    if blurb:
        out += [blurb, ""]
    for t in topics:
        out.append(f"- **{t.title}** — {doc_url('', t.page, doc_base)}")
        if t.concepts:
            out.append("  " + " · ".join(t.concepts))
    out.append("")
    return "\n".join(out) + "\n"


def render_flat_map(topics: list[Topic], doc_base: str) -> str:
    rows = ["page_title\tconcept\turl"]
    for t in topics:
        rows.append(f"{t.title}\t\t{doc_url('', t.page, doc_base)}")
        for concept, anchor in zip(t.concepts, t.anchors):
            rows.append(f"{t.title}\t{concept}\t"
                        f"{doc_url('', t.page, doc_base, anchor)}")
    return "\n".join(rows) + "\n"


def index_hash(topics: list[Topic]) -> str:
    canon = "\n".join(f"{t.section}|{t.page}|{t.title}|{','.join(t.anchors)}"
                      for t in topics)
    return hashlib.sha256(canon.encode()).hexdigest()[:12]


def main() -> int:
    ap = argparse.ArgumentParser(description="Index the NDK Developer Guide.")
    ap.add_argument("guide", help="a guide directory (NDKDevGuide, "
                                   "PythonDevGuide/Nuke, or BlinkUserGuide)")
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--doc-base", required=True,
                    help="Public base URL, e.g. "
                         ".../nuke/developers/17.0/ndkdevguide")
    ap.add_argument("--name", default="devguide",
                    help="output file prefix (<name>_index.md / <name>_map.tsv)")
    ap.add_argument("--flat", action="store_true",
                    help="flat guide (Python/Blink): one index.html over sibling "
                         "pages; URLs carry no section segment")
    ap.add_argument("--title", help="heading title for a flat guide")
    args = ap.parse_args()

    guide = pathlib.Path(args.guide)
    if not guide.is_dir():
        print(f"not a directory: {guide}", file=sys.stderr)
        return 1

    if args.flat:
        topics = build_flat(guide)
    else:
        topics = build_index(guide)
    if not topics:
        print(f"no guide pages found in {guide}", file=sys.stderr)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    if args.flat:
        title = args.title or args.name
        md = render_flat_md(topics, args.doc_base, title, FLAT_INTRO.get(args.name, ""))
        tsv = render_flat_map(topics, args.doc_base)
        scope = "pages"
    else:
        md = render_index_md(topics, args.doc_base)
        tsv = render_map(topics, args.doc_base)
        scope = f"pages across {len({t.section for t in topics})} sections"
    (args.out / f"{args.name}_index.md").write_text(md)
    (args.out / f"{args.name}_map.tsv").write_text(tsv)

    print(f"{len(topics)} {scope}, hash {index_hash(topics)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
