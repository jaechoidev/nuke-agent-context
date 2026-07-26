#!/usr/bin/env python3
"""Parse DDImage headers into a compact symbol index.

Emits routing data (symbol -> header + line) plus a one-line description where
the header documents one. Routing coverage is 100% by construction; description
coverage is ~70% on Nuke 15.2-17.0, concentrated in the classes that matter.

Symbols are recorded under their *qualified* name. `Description` is declared in
13 different DDImage headers as a nested class, and every NDK plugin registers
itself with `static const Op::Description description;` -- so a flat name would
have to pick one of the 13 and send the agent to the wrong idiom. Qualifying
gives `Op::Description`, `Reader::Description`, `DeepReader::Description` as the
distinct types they actually are.

Knows C++ header syntax only. Takes a directory; knows nothing about Nuke installs.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import pathlib
import re
import sys

# A class/struct *definition*: optional EXPORT macro, then `{` or a base-class list.
# Trailing `;` means forward declaration -> skipped.
CLASS_RE = re.compile(
    r"^[ \t]*(?:class|struct)\s+(?:[A-Z]\w*_API\s+)?([A-Z]\w+)\s*(?::[^;]*)?(?:\{|$)")
BLOCK_RE = re.compile(r"/\*[!*](.*?)\*/", re.S)      # /*! ... */ and /** ... */
LINE_RE = re.compile(r"^[ \t]*(?://!|///)(.*)$")     # //! ... and /// ...
DOXY_TAGS = re.compile(
    r"\\(?:brief|param|return|returns|see|sa|note|deprecated|since|a|e|b|p|c)\b")

# A description must read as prose. Section dividers ("////////...") and other
# punctuation runs otherwise get adopted as a class's documentation.
MIN_PROSE_RATIO = 0.6
MIN_PROSE_CHARS = 12


@dataclasses.dataclass(frozen=True)
class Symbol:
    name: str          # qualified, e.g. "Op::Description" or "Row"
    header: str
    line: int
    desc: str
    variants: int = 1  # >1 when the same name is defined more than once (e.g. #ifdef)

    @property
    def base(self) -> str:
        """Unqualified name, for callers that want to search by short name."""
        return self.name.rsplit("::", 1)[-1]


def strip_comments(src: str) -> str:
    """Blank out comments, preserving every newline so line numbers still line up.

    Without this, C++ examples inside doxygen `\\code` blocks parse as real
    declarations -- DDImage ships `class MyOp : public Op {` inside a comment in
    Op.h, and an unguarded parser indexes a class that does not exist.
    """
    out: list[str] = []
    i, n, st = 0, len(src), 0        # st: 0 code, 1 block comment, 2 line comment,
    while i < n:                     #     3 double-quoted, 4 single-quoted
        c = src[i]
        nxt = src[i + 1] if i + 1 < n else ""
        if st == 0:
            if c == "/" and nxt == "*":
                st, i = 1, i + 2
                out.append("  ")
                continue
            if c == "/" and nxt == "/":
                st, i = 2, i + 2
                out.append("  ")
                continue
            if c == '"':
                st = 3
            elif c == "'":
                st = 4
            out.append(c)
            i += 1
        elif st == 1:
            if c == "*" and nxt == "/":
                st, i = 0, i + 2
                out.append("  ")
                continue
            out.append("\n" if c == "\n" else " ")
            i += 1
        elif st == 2:
            if c == "\n":
                st = 0
                out.append("\n")
                i += 1
                continue
            out.append(" ")
            i += 1
        else:
            if c == "\\" and i + 1 < n:      # escape: copy both chars verbatim
                out.append(c)
                out.append(src[i + 1])
                i += 2
                continue
            if (st == 3 and c == '"') or (st == 4 and c == "'"):
                st = 0
            out.append(c)
            i += 1
    return "".join(out)


def _definitions(code: str) -> list[tuple[str, int]]:
    """Return (qualified_name, line) for each class/struct definition in `code`.

    `code` must already have comments stripped. Tracks brace depth so a nested
    class is reported as Outer::Inner rather than colliding with every other
    class of the same short name.
    """
    found: list[tuple[str, int]] = []
    stack: list[tuple[str, int]] = []     # (name, depth at which it opened)
    depth = 0
    pending: tuple[str, int] | None = None

    for idx, ln in enumerate(code.splitlines()):
        m = CLASS_RE.match(ln)
        if m and not ln.rstrip().endswith(";"):
            pending = (m.group(1), idx + 1)
        for ch in ln:
            if ch == "{":
                if pending:
                    qual = "::".join([s[0] for s in stack] + [pending[0]])
                    found.append((qual, pending[1]))
                    stack.append((pending[0], depth))
                    pending = None
                depth += 1
            elif ch == "}":
                depth -= 1
                while stack and stack[-1][1] >= depth:
                    stack.pop()
    return found


def _is_prose(text: str) -> bool:
    """Reject section dividers and punctuation runs masquerading as documentation."""
    if len(text) < MIN_PROSE_CHARS:
        return False
    alnum = sum(1 for c in text if c.isalnum() or c.isspace())
    return alnum / len(text) >= MIN_PROSE_RATIO


def _prose(raw: str) -> tuple[str | None, str]:
    """Reduce a doc comment to (explicitly-named class or None, first sentence)."""
    m = re.search(r"\\class\s+([\w:]+)", raw)
    named = m.group(1).split("::")[-1] if m else None
    txt = re.sub(r"\\class\s+[\w:]+", " ", raw)
    txt = DOXY_TAGS.sub(" ", txt)
    txt = re.sub(r"^\s*\*+", " ", txt, flags=re.M)   # strip leading * on each line
    txt = re.sub(r"\s+", " ", txt).strip()
    if not txt:
        return named, ""
    m = re.match(r"(.{0,200}?[.!?])(?:\s|$)", txt)
    out = (m.group(1) if m else txt[:200]).strip()
    return named, (out if _is_prose(out) else "")


def _comment_ends(src: str, lines: list[str]) -> dict[int, tuple[str | None, str]]:
    """Map the line a doc comment ends on -> its parsed prose."""
    ends: dict[int, tuple[str | None, str]] = {}
    for m in BLOCK_RE.finditer(src):
        ends[src[: m.end()].count("\n") + 1] = _prose(m.group(1))
    i = 0
    while i < len(lines):
        if LINE_RE.match(lines[i]):
            j, buf = i, []
            while j < len(lines) and LINE_RE.match(lines[j]):
                buf.append(LINE_RE.match(lines[j]).group(1))
                j += 1
            ends[j] = _prose(" ".join(buf))
            i = j
        else:
            i += 1
    return ends


def parse_header(path: pathlib.Path) -> dict[str, Symbol]:
    src = path.read_text(errors="replace")
    code = strip_comments(src)
    code_lines = code.splitlines()
    ends = _comment_ends(src, src.splitlines())
    found: dict[str, Symbol] = {}

    for qual, lineno in _definitions(code):
        desc = ""
        for back in range(1, 4):                 # comment may end 1-3 lines above
            hit = ends.get(lineno - back)
            if not hit:
                continue
            # Everything between the comment and the declaration must be blank.
            # Without this a comment documenting a preceding member or the
            # enclosing class gets adopted -- DDImage has SubFace picking up
            # PolyMesh's description this way.
            gap = code_lines[lineno - back:lineno - 1]
            if any(g.strip() for g in gap):
                continue
            named, text = hit
            if named and named != qual.rsplit("::", 1)[-1]:
                continue                          # \class names some other class
            desc = text
            break

        if qual in found:                         # same name twice (e.g. #ifdef)
            prev = found[qual]
            found[qual] = dataclasses.replace(prev, variants=prev.variants + 1)
            continue
        found[qual] = Symbol(qual, path.name, lineno, desc)

    # A \class block may sit far from its declaration; backfill empties.
    for named, text in ends.values():
        if not (named and text):
            continue
        for key, sym in list(found.items()):
            if key.rsplit("::", 1)[-1] == named and not sym.desc:
                found[key] = dataclasses.replace(sym, desc=text)
    return found


def build_index(headers_dir: pathlib.Path) -> dict[str, Symbol]:
    index: dict[str, Symbol] = {}
    for header in sorted(pathlib.Path(headers_dir).glob("*.h")):
        for name, sym in parse_header(header).items():
            if name in index:
                prev = index[name]
                index[name] = dataclasses.replace(
                    prev, variants=prev.variants + sym.variants)
                continue
            index[name] = sym
    return index


def doc_url(name: str, doc_base: str,
            doxygen_dir: pathlib.Path | None = None) -> str:
    """Public Foundry doxygen URL for a DD::Image class, or "" if none applies.

    Doxygen names a class page `classDD_1_1Image_1_1<Name>.html`, with `::` in a
    nested name mangled to `_1_1` (so `Op::Description` ->
    `...Op_1_1Description.html`). Not every indexed symbol is a DD::Image class
    (`Tile` is not), so when a local doxygen directory is given the URL is only
    emitted for a page that actually exists there -- a real link or none, never
    a guess that 404s.
    """
    page = "classDD_1_1Image_1_1" + name.replace("::", "_1_1") + ".html"
    if doxygen_dir is not None and not (pathlib.Path(doxygen_dir) / page).is_file():
        return ""
    return f"{doc_base.rstrip('/')}/{page}"


def render_symbol_map(index: dict[str, Symbol], doc_base: str | None = None,
                      doxygen_dir: pathlib.Path | None = None) -> str:
    """TSV routing map. With `doc_base`, append a public doc URL column."""
    if doc_base is None:
        rows = ["symbol\theader\tline"]
        rows += [f"{s.name}\t{s.header}\t{s.line}"
                 for s in sorted(index.values(), key=lambda s: s.name)]
        return "\n".join(rows) + "\n"
    rows = ["symbol\theader\tline\turl"]
    rows += [f"{s.name}\t{s.header}\t{s.line}\t{doc_url(s.name, doc_base, doxygen_dir)}"
             for s in sorted(index.values(), key=lambda s: s.name)]
    return "\n".join(rows) + "\n"


def render_index_md(index: dict[str, Symbol], doc_base: str | None = None,
                    doxygen_dir: pathlib.Path | None = None) -> str:
    """Markdown index.

    Default: the local Purpose prose column, for an on-machine reference.
    With `doc_base`: a redistributable index that carries no Foundry prose --
    the Purpose column is replaced by a public learn.foundry.com link, so the
    committed file is derived facts (name, header, line, URL) only.
    """
    header = ("| Symbol | Header | Line | Docs |" if doc_base
              else "| Symbol | Header | Line | Purpose |")
    out = [
        "# DDImage symbol index",
        "",
        f"{len(index)} classes. Look up a symbol here, then read the real header "
        "for exact signatures.",
        "",
        "Nested classes are qualified (`Op::Description`). Search by the short "
        "name to see every variant.",
        "",
        header,
        "| --- | --- | --- | --- |",
    ]
    for s in sorted(index.values(), key=lambda s: s.name):
        note = f" _({s.variants} variants)_" if s.variants > 1 else ""
        if doc_base:
            url = doc_url(s.name, doc_base, doxygen_dir)
            out.append(f"| `{s.name}` | {s.header} | {s.line} | {url}{note} |")
        else:
            out.append(f"| `{s.name}` | {s.header} | {s.line} | {s.desc}{note} |")
    return "\n".join(out) + "\n"


def index_hash(index: dict[str, Symbol]) -> str:
    canon = "\n".join(
        f"{s.name}|{s.header}|{s.line}"
        for s in sorted(index.values(), key=lambda s: s.name))
    return hashlib.sha256(canon.encode()).hexdigest()[:12]


def main() -> int:
    ap = argparse.ArgumentParser(description="Index DDImage headers.")
    ap.add_argument("headers", type=pathlib.Path)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--doc-base",
                    help="Public Foundry doxygen base URL (e.g. "
                         ".../17.0/ndkreference/Plugins). Given, the index is "
                         "rendered for redistribution: the Purpose prose is "
                         "replaced by a per-symbol link, carrying no Foundry text.")
    ap.add_argument("--doxygen", type=pathlib.Path,
                    help="Local doxygen dir (NDKExamples/Plugins) to verify a "
                         "page exists before linking it.")
    args = ap.parse_args()

    if not args.headers.is_dir():
        print(f"not a directory: {args.headers}", file=sys.stderr)
        return 1

    index = build_index(args.headers)
    if not index:
        print(f"no classes found in {args.headers}", file=sys.stderr)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "ndk_index.md").write_text(
        render_index_md(index, args.doc_base, args.doxygen))
    (args.out / "symbol_map.tsv").write_text(
        render_symbol_map(index, args.doc_base, args.doxygen))

    described = sum(1 for s in index.values() if s.desc)
    print(f"{len(index)} symbols, {described} described "
          f"({100 * described // len(index)}%), hash {index_hash(index)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
