#!/usr/bin/env python3
"""Parse the Blink kernel reference into a built-in API index.

Parallel to extract_ndk_index.py and extract_python_api.py, for BlinkScript.
Source is the BlinkKernelAPIReference shipped with Nuke -- no license needed.

Blink is a small fixed language, so this indexes three things:
  builtin   maths + kernel functions parsed from the reference (sin, dot, median)
  type      vector/image types (float3, Image, ...)
  keyword   fixed language constructs (kernel, process, eRead, eAccessPoint)

The keyword set is intrinsic to the grammar and stable across versions, so it
is enumerated here rather than scraped from prose. Functions and types are
extracted from the reference so the index tracks the installed version.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import html
import pathlib
import re
import sys

# Fixed Blink language constructs -- the grammar, not the library. Stable.
KEYWORDS = {
    "kernel", "ImageComputationKernel", "ImageReductionKernel", "ImageRollingKernel",
    "eRead", "eWrite", "eReadWrite", "eEdit",
    "eAccessPoint", "eAccessRanged", "eAccessRandom",
    "eComponentWise", "ePixelWise",
    "param", "local", "define", "process", "init",
    "Image", "void", "bool", "int", "float", "kernel",
    "bounds", "at", "setRange", "setAxis", "median", "print",
}

# Vector / matrix / image types.
TYPES = {
    "float", "float2", "float3", "float4", "float3x3", "float4x4",
    "int", "int2", "int3", "int4", "bool", "bool2", "bool3", "bool4",
    "Image", "ImageInfo", "recursive",
}


@dataclasses.dataclass(frozen=True)
class Symbol:
    name: str
    kind: str          # builtin | type | keyword
    sig: str = ""      # dot(floatn x, floatn y)
    desc: str = ""     # Returns the dot product of x and y


def _signatures_from(ref_dir: pathlib.Path) -> dict[str, tuple[str, str]]:
    """Map builtin -> (args, one-line description) parsed from the reference."""
    out: dict[str, tuple[str, str]] = {}
    for page in ("MathsFunctions.html", "Kernels.html"):
        p = ref_dir / page
        if not p.is_file():
            continue
        text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", p.read_text(errors="replace"))))
        for m in re.finditer(r"\b([a-z][a-zA-Z0-9_]{1,20})\s*\(([^)]{0,120})\)\s*;?\s*([A-Z][^.;]{0,90})?", text):
            name, args, doc = m.group(1), m.group(2).strip(), (m.group(3) or "").strip()
            if name not in out or (doc and not out[name][1]):
                out[name] = (args, doc)
    return out


# The Blink maths library. Like the keywords and types, this is the small fixed
# grammar of the language, so it is enumerated intrinsically rather than scraped
# -- scraping the SET is version-fragile (Nuke 15.2's HTML formats some
# signatures differently and drops lerp, a real builtin). Verified against
# BlinkKernelAPIReference/MathsFunctions.html.
#
# Do NOT add plausible GLSL/HLSL names Blink lacks: smoothstep, step, mix, fract,
# saturate, distance, reflect, refract are NOT Blink built-ins. Listing one would
# send the agent to write code that fails to compile -- the exact failure this
# index exists to prevent.
MATHS = {
    "sin", "cos", "tan", "asin", "acos", "atan", "atan2",
    "pow", "exp", "log", "log2", "log10", "sqrt", "rsqrt",
    "fabs", "floor", "ceil", "round", "fmod",
    "min", "max", "clamp", "lerp",
    "dot", "cross", "length", "normalize", "sign", "median",
}


def build_index(ref_dir: pathlib.Path) -> dict[str, Symbol]:
    ref_dir = pathlib.Path(ref_dir)
    index: dict[str, Symbol] = {}
    for kw in KEYWORDS:
        index.setdefault(kw, Symbol(kw, "keyword"))
    for t in TYPES:
        index[t] = Symbol(t, "type")            # type wins over keyword overlap
    sigs = _signatures_from(ref_dir)             # enrich with args where the doc has them
    for fn in MATHS:
        args, doc = sigs.get(fn, ("", ""))
        index.setdefault(fn, Symbol(fn, "builtin", f"{fn}({args})" if args else "", doc))
    return index


def doc_url(name: str, doc_base: str) -> str:
    """Public Foundry URL for a Blink symbol.

    Blink is a small fixed language whose maths library, types, and keywords are
    all documented on one page, so every symbol links to the same reference.
    """
    return f"{doc_base.rstrip('/')}/BlinkKernelAPIReference.html"


def render_symbol_map(index: dict[str, Symbol], doc_base: str | None = None) -> str:
    if doc_base is None:
        rows = ["symbol\tkind"]
        rows += [f"{s.name}\t{s.kind}"
                 for s in sorted(index.values(), key=lambda s: s.name)]
        return "\n".join(rows) + "\n"
    rows = ["symbol\tkind\turl"]
    rows += [f"{s.name}\t{s.kind}\t{doc_url(s.name, doc_base)}"
             for s in sorted(index.values(), key=lambda s: s.name)]
    return "\n".join(rows) + "\n"


def render_index_md(index: dict[str, Symbol], doc_base: str | None = None) -> str:
    """Markdown index. With `doc_base`, the Purpose column becomes a public
    learn.foundry.com link (no Foundry prose); signatures are kept."""
    last = "Docs" if doc_base else "Purpose"
    out = [
        "# BlinkScript built-in API index",
        "",
        f"{len(index)} built-ins. A kernel that calls anything not listed here "
        "(and not a param/local you declared) will fail to compile in Nuke.",
        "",
        f"| Symbol | Kind | Signature | {last} |",
        "| --- | --- | --- | --- |",
    ]
    for s in sorted(index.values(), key=lambda s: (s.kind, s.name)):
        sig = f"`{s.sig}`" if s.sig else ""
        tail = doc_url(s.name, doc_base) if doc_base else s.desc
        out.append(f"| `{s.name}` | {s.kind} | {sig} | {tail} |")
    return "\n".join(out) + "\n"


def index_hash(index: dict[str, Symbol]) -> str:
    canon = "\n".join(f"{s.name}|{s.kind}"
                      for s in sorted(index.values(), key=lambda s: s.name))
    return hashlib.sha256(canon.encode()).hexdigest()[:12]


def main() -> int:
    ap = argparse.ArgumentParser(description="Index the BlinkScript built-in API.")
    ap.add_argument("reference", help="BlinkKernelAPIReference directory")
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--doc-base",
                    help="Public Foundry base URL (e.g. .../17.0/BlinkUserGuide). "
                         "Given, the index links to the reference page instead of "
                         "carrying scraped prose.")
    args = ap.parse_args()

    ref = pathlib.Path(args.reference)
    if not ref.is_dir():
        print(f"not a directory: {ref}", file=sys.stderr)
        return 1

    index = build_index(ref)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "blink_index.md").write_text(render_index_md(index, args.doc_base))
    (args.out / "blink_symbols.tsv").write_text(
        render_symbol_map(index, args.doc_base))

    kinds = {k: sum(1 for s in index.values() if s.kind == k)
             for k in ("builtin", "type", "keyword")}
    print(f"{len(index)} symbols "
          f"({kinds['builtin']} builtins, {kinds['type']} types, "
          f"{kinds['keyword']} keywords), hash {index_hash(index)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
