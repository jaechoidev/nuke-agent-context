#!/usr/bin/env python3
"""Parse Nuke's Python documentation into a compact API index.

Parallel to extract_ndk_index.py, for the Python layer. The source is the
PythonDevGuide autosummary shipped with every Nuke install, so this needs no
license and no running Nuke -- unlike `nuke -t` introspection, which the
api-lookup skill falls back to when the docs are absent.

Emits three symbol kinds:
  function   nuke.allNodes, nuke.createNode, ...
  class      nuke.Node, nuke.Knob, ...
  method     nuke.Node.knob, nuke.Knob.setValue, ...

Routing coverage is whatever the docs enumerate; a symbol absent from the
index is one the agent should not write without checking.

Knows the autosummary layout only. Takes a directory; knows nothing about Nuke
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

# Autosummary page names: nuke.X.html (top-level) and nuke.Class.method.html.
PAGE_RE = re.compile(r"^nuke\.([A-Za-z_]\w*)(?:\.([A-Za-z_]\w*))?$")
META_RE = re.compile(r'<meta name="description" content="([^"]*)"')
FIRST_P_RE = re.compile(r"<p[^>]*>(.*?)</p>", re.S)


# The real content lives in a signature <dt> (class "sig", carrying the symbol
# id) immediately followed by a <dd> docstring. The meta tag is generic prose.
SIG_DT_RE = re.compile(
    r'<dt class="sig[^"]*"[^>]*id="(nuke\.[A-Za-z_][\w.]*)"[^>]*>(.*?)</dt>\s*<dd[^>]*>(.*?)</dd>',
    re.S)


@dataclasses.dataclass(frozen=True)
class Symbol:
    name: str          # nuke.Node, nuke.Node.knob, nuke.allNodes
    kind: str          # class | function | method
    sig: str           # createNode(node, knobs, inpanel) -> Node
    desc: str          # first sentence of the docstring


def _flatten(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _first_sentence(text: str, limit: int = 200) -> str:
    text = _flatten(text)
    # cut before the "Parameters ..." tail so the description stays a summary
    text = re.split(r"\bParameters\b|\bReturns\b|\bReturn type\b", text)[0].strip()
    m = re.match(rf"(.{{0,{limit}}}?[.!?])(?:\s|$)", text)
    return (m.group(1) if m else text[:limit]).strip()


def _drop_prose_return(sig: str) -> str:
    """Keep the call form and a type-like return; drop a prose-sentence return.

    Nuke documents many returns as free prose ("-> The knob named p or the pth
    knob."). That sentence is Foundry documentation text and must not ride into
    a committed signature. A type-like return (`Node`, `None`, `AnimationCurve or
    None`) is a functional fact and is kept; anything else is dropped, leaving
    just `name(args)`.
    """
    call, arrow, ret = sig.partition("->")
    if not arrow:
        return sig.strip()
    ret = ret.strip().rstrip(".").strip()
    if re.fullmatch(r"[\w.]+(?: (?:or|\|) [\w.]+)*", ret):
        return f"{call.strip()} -> {ret}"
    return call.strip()


def _signature(dt_html: str, symbol: str) -> str:
    """Normalise a <dt> into `name(args) -> ret`, dropping the module prefix."""
    sig = _flatten(dt_html).replace("\uf0c1", " ")   # strip Sphinx headerlink glyph
    sig = sig.replace("nuke. ", "nuke.").replace(" (", "(").replace("( ", "(")
    sig = sig.replace(" )", ")").replace(" ,", ",").replace("→", "->")
    leaf = symbol.rsplit(".", 1)[-1]
    m = re.search(rf"{re.escape(leaf)}\s*\(.*", sig)
    return _drop_prose_return((m.group(0) if m else sig)[:200].strip())


def _details(page: pathlib.Path) -> dict[str, tuple[str, str]]:
    """Map every documented symbol on a page to (signature, first-sentence)."""
    h = page.read_text(errors="replace")
    out: dict[str, tuple[str, str]] = {}
    for name, dt, dd in SIG_DT_RE.findall(h):
        # the docstring's first <p> is the summary; the rest is Parameters/Returns
        pm = FIRST_P_RE.search(dd)
        desc = _first_sentence(pm.group(1) if pm else dd)
        out[name] = (_signature(dt, name), desc)
    return out


def parse_class_methods(page: pathlib.Path, cls: str) -> set[str]:
    """Methods a class page enumerates, e.g. every nuke.Node.<m> it mentions."""
    h = page.read_text(errors="replace")
    return set(re.findall(rf"nuke\.{re.escape(cls)}\.([a-zA-Z_]\w*)", h))


def build_index(autosummary_dir: pathlib.Path) -> dict[str, Symbol]:
    d = pathlib.Path(autosummary_dir)
    pages = sorted(d.glob("nuke.*.html"))
    index: dict[str, Symbol] = {}

    for page in pages:
        m = PAGE_RE.match(page.stem)
        if not m:
            continue
        head, tail = m.group(1), m.group(2)
        details = _details(page)
        if tail:                                     # nuke.Class.method page
            name = f"nuke.{head}.{tail}"
            sig, desc = details.get(name, ("", ""))
            index.setdefault(name, Symbol(name, "method", sig, desc))
            continue
        # nuke.X page: class if it enumerates methods, else a function/constant.
        kind = "class" if head[:1].isupper() else "function"
        name = f"nuke.{head}"
        sig, desc = details.get(name, ("", ""))
        index.setdefault(name, Symbol(name, kind, sig, desc))
        # Methods are documented in-page on the owning class; capture their detail.
        for mname, (msig, mdesc) in details.items():
            if mname.startswith(f"nuke.{head}.") and mname.count(".") == 2:
                index.setdefault(mname, Symbol(mname, "method", msig, mdesc))
        if kind == "class":
            for meth in parse_class_methods(page, head):
                mn = f"nuke.{head}.{meth}"
                index.setdefault(mn, Symbol(mn, "method", "", ""))
    return index


def doc_url(name: str, kind: str, doc_base: str) -> str:
    """Public Foundry autosummary URL for a symbol.

    Sphinx names a page after the symbol itself, so `nuke.createNode` lives at
    `_autosummary/nuke.createNode.html`. A method has no page of its own -- it is
    documented on its class page under an `id` anchor -- so `nuke.Node.knob`
    resolves to `_autosummary/nuke.Node.html#nuke.Node.knob`.
    """
    base = doc_base.rstrip("/")
    if kind == "method":
        cls = name.rsplit(".", 1)[0]           # nuke.Node.knob -> nuke.Node
        return f"{base}/_autosummary/{cls}.html#{name}"
    return f"{base}/_autosummary/{name}.html"


def render_symbol_map(index: dict[str, Symbol], doc_base: str | None = None) -> str:
    if doc_base is None:
        rows = ["symbol\tkind"]
        rows += [f"{s.name}\t{s.kind}"
                 for s in sorted(index.values(), key=lambda s: s.name)]
        return "\n".join(rows) + "\n"
    rows = ["symbol\tkind\turl"]
    rows += [f"{s.name}\t{s.kind}\t{doc_url(s.name, s.kind, doc_base)}"
             for s in sorted(index.values(), key=lambda s: s.name)]
    return "\n".join(rows) + "\n"


def method_names(index: dict[str, Symbol]) -> set[str]:
    """Flat set of every method leaf-name across all classes.

    Grade method calls against this, not against `Class.method`. Nuke documents
    a method on the concrete subclass that owns it (setValue on Array_Knob), but
    code calls it through the base type (knob.setValue()). A strict Class.method
    check would flag real inherited calls as invented -- the precise false the
    eval must not commit.
    """
    return {s.name.rsplit(".", 1)[-1] for s in index.values() if s.kind == "method"}


def render_method_names(index: dict[str, Symbol]) -> str:
    return "\n".join(sorted(method_names(index))) + "\n"


def render_index_md(index: dict[str, Symbol], doc_base: str | None = None) -> str:
    """Markdown index.

    Default: the local Purpose prose column. With `doc_base`: a redistributable
    index carrying no Foundry prose -- the Purpose column becomes a public
    learn.foundry.com link. Signatures (name(args) -> ret, functional facts) are
    kept in both modes.
    """
    classes = [s for s in index.values() if s.kind == "class"]
    funcs = [s for s in index.values() if s.kind == "function"]
    methods = [s for s in index.values() if s.kind == "method"]
    last = "Docs" if doc_base else "Purpose"
    out = [
        "# Nuke Python API index",
        "",
        f"{len(classes)} classes, {len(funcs)} module functions, "
        f"{len(methods)} methods. Signatures and one-line purposes are from the "
        "shipped docs; a symbol absent here should not be written.",
        "",
        f"| Symbol | Kind | Signature | {last} |",
        "| --- | --- | --- | --- |",
    ]
    for s in sorted(index.values(), key=lambda s: s.name):
        sig = f"`{s.sig}`" if s.sig else ""
        tail = doc_url(s.name, s.kind, doc_base) if doc_base else s.desc
        out.append(f"| `{s.name}` | {s.kind} | {sig} | {tail} |")
    return "\n".join(out) + "\n"


def index_hash(index: dict[str, Symbol]) -> str:
    canon = "\n".join(f"{s.name}|{s.kind}"
                      for s in sorted(index.values(), key=lambda s: s.name))
    return hashlib.sha256(canon.encode()).hexdigest()[:12]


def main() -> int:
    ap = argparse.ArgumentParser(description="Index the Nuke Python API.")
    ap.add_argument("autosummary",
                    help="PythonDevGuide/Nuke/_autosummary directory")
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--doc-base",
                    help="Public Foundry base URL (e.g. "
                         ".../17.0/pythondevguide). Given, the index is rendered "
                         "for redistribution: prose is replaced by per-symbol "
                         "links, carrying no Foundry text.")
    args = ap.parse_args()

    src = pathlib.Path(args.autosummary)
    if not src.is_dir():
        print(f"not a directory: {src}", file=sys.stderr)
        return 1

    index = build_index(src)
    if not index:
        print(f"no nuke.* pages found in {src}", file=sys.stderr)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "python_index.md").write_text(
        render_index_md(index, args.doc_base))
    (args.out / "python_symbols.tsv").write_text(
        render_symbol_map(index, args.doc_base))
    (args.out / "python_methods.txt").write_text(render_method_names(index))

    kinds = {k: sum(1 for s in index.values() if s.kind == k)
             for k in ("class", "function", "method")}
    print(f"{len(index)} symbols "
          f"({kinds['class']} classes, {kinds['function']} functions, "
          f"{kinds['method']} methods), hash {index_hash(index)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
