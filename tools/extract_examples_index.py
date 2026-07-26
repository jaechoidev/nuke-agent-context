#!/usr/bin/env python3
"""Index the shipped Foundry examples by what each one *teaches*.

The fourth extractor. The other three answer "does this symbol exist"; this one
answers "which real, compiling example should I read to learn this pattern" --
the paradigm-transfer half of the toolkit. It points the agent at Foundry's own
canonical code (82 NDK .cpp + the Blink kernels) rather than at community tools.

Classification is derived from each example's base class and which contract
methods it overrides -- factual structure, parsed from the file. The category
lesson text is original. Foundry's HELP one-liner is included in the generated
output (the user's own local docs), never committed to this repo.

Knows C++/kernel file shape only. Takes a directory; knows nothing about Nuke
install detection.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import pathlib
import re
import sys

BASE_RE = re.compile(r"\bpublic\s+(?:DD::Image::)?([A-Z][A-Za-z0-9_]+)")
HELP_RE = re.compile(r'(?:HELP|help)\s*=\s*"([^"]{4,200})"')
INCLUDE_RE = re.compile(r'#include\s+"DDImage/([A-Za-z0-9_]+)\.h"')
CONTRACT = ["_validate", "_request", "engine", "pixel_engine", "in_channels",
            "knobs", "knob_changed", "append", "build_handles",
            "geometry_engine", "create_geometry", "engine_gpu"]

# Base class -> (paradigm category, what reading an example of it teaches).
# Original text; the mapping is the teaching taxonomy.
CATEGORY = {
    "PixelIop":    ("2D per-pixel", "output pixel depends only on the input pixel; in_channels + pixel_engine"),
    "Iop":         ("2D general", "full Op contract; may need caching (Interest) for neighbouring pixels"),
    "MultiTileIop":("2D multi-input", "reading several inputs/tiles per output scanline"),
    "NoIop":       ("2D pass-through", "metadata/no-pixel ops that only change info, not pixels"),
    "DrawIop":     ("2D generator", "source nodes that draw rather than filter an input"),
    "Transform":   ("2D transform", "moving pixels; concatenating transforms via pass_transform"),
    "DeepFilterOp":("deep", "iterating deep samples in a DeepFilterOp"),
    "DeepReaderFormat": ("deep IO", "reading deep image formats"),
    "DeepWriter":  ("deep IO", "writing deep image formats"),
    "GeoOp":       ("3D geometry", "producing/modifying GeoInfo in the 3D system"),
    "SourceGeomOp":("3D geometry source", "generating geometry from scratch (create_geometry)"),
    "ModifyGeomOp":("3D geometry modifier", "transforming incoming geometry"),
    "Material":    ("3D shading", "surface shaders in the 3D system"),
    "IllumShader": ("3D shading", "illumination/lighting shaders"),
    "Reader":      ("file IO", "decoding an image file into Nuke"),
    "FileReader":  ("file IO", "decoding an image file into Nuke"),
    "ReaderFormat":("file IO", "reader options/format handling"),
    "Writer":      ("file IO", "encoding Nuke output to a file"),
    "FileWriter":  ("file IO", "encoding Nuke output to a file"),
    "GeoReaderFormat": ("3D IO", "reading geometry file formats"),
    "GeoWriter":   ("3D IO", "writing geometry file formats"),
    "ParticleBehaviour": ("particles", "custom particle behaviours"),
    "Knob":        ("custom knob", "authoring a custom knob / UI control"),
    "Op":          ("core op", "the base Op contract directly"),
}


@dataclasses.dataclass(frozen=True)
class Example:
    file: str
    base: str
    category: str
    lesson: str
    overrides: tuple[str, ...]
    help: str            # Foundry HELP one-liner (local output only)


def _clean_help(raw: str) -> str:
    """Foundry HELP is a plain one-liner, but a few files embed doxygen HTML.
    Keep it only when it survives as a short clean sentence; else drop it and
    let the paradigm lesson stand."""
    h = re.sub(r"<[^>]+>", " ", raw)
    h = re.sub(r"\s+", " ", h).strip()
    if "<" in raw or len(h) > 90 or not h:
        return ""
    return h


def parse_example(path: pathlib.Path) -> Example | None:
    src = path.read_text(errors="replace")
    bm = BASE_RE.search(src)
    if not bm:
        return None
    base = bm.group(1)
    cat, lesson = CATEGORY.get(base, ("other", f"derives from {base}"))
    overrides = tuple(m for m in CONTRACT if re.search(rf"\b{m}\s*\(", src))
    hm = HELP_RE.search(src)
    return Example(path.name, base, cat, lesson, overrides,
                   _clean_help(hm.group(1)) if hm else "")


def build_index(examples_dir: pathlib.Path) -> dict[str, Example]:
    index: dict[str, Example] = {}
    for f in sorted(pathlib.Path(examples_dir).glob("*.cpp")):
        ex = parse_example(f)
        if ex:
            index.setdefault(ex.file, ex)
    return index


def render_index_md(index: dict[str, Example], examples_dir: pathlib.Path) -> str:
    by_cat: dict[str, list[Example]] = {}
    for ex in index.values():
        by_cat.setdefault(ex.category, []).append(ex)
    out = [
        "# Foundry example index — read the canonical pattern before writing",
        "",
        f"{len(index)} shipped examples in `{examples_dir}`. To learn a pattern, "
        "read the real file listed here rather than inventing structure.",
        "",
    ]
    for cat in sorted(by_cat):
        out.append(f"## {cat}")
        out.append("")
        out.append("| Example | Base | Teaches | Purpose | Overrides |")
        out.append("| --- | --- | --- | --- | --- |")
        for ex in sorted(by_cat[cat], key=lambda e: e.file):
            ov = ", ".join(ex.overrides) or "-"
            out.append(f"| `{ex.file}` | {ex.base} | {ex.lesson} | {ex.help} | {ov} |")
        out.append("")
    return "\n".join(out) + "\n"


def render_task_map(index: dict[str, Example]) -> str:
    """Flat task -> example lookup: category, file, lesson."""
    rows = ["category\texample\tbase\tlesson"]
    for ex in sorted(index.values(), key=lambda e: (e.category, e.file)):
        rows.append(f"{ex.category}\t{ex.file}\t{ex.base}\t{ex.lesson}")
    return "\n".join(rows) + "\n"


def index_hash(index: dict[str, Example]) -> str:
    canon = "\n".join(f"{e.file}|{e.base}|{e.category}"
                      for e in sorted(index.values(), key=lambda e: e.file))
    return hashlib.sha256(canon.encode()).hexdigest()[:12]


def main() -> int:
    ap = argparse.ArgumentParser(description="Index Foundry examples by lesson.")
    ap.add_argument("examples", help="NDKExamples/examples directory")
    ap.add_argument("--out", type=pathlib.Path, required=True)
    args = ap.parse_args()

    d = pathlib.Path(args.examples)
    if not d.is_dir():
        print(f"not a directory: {d}", file=sys.stderr)
        return 1

    index = build_index(d)
    if not index:
        print(f"no .cpp examples found in {d}", file=sys.stderr)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "examples_index.md").write_text(render_index_md(index, d))
    (args.out / "examples_map.tsv").write_text(render_task_map(index))

    cats = len({e.category for e in index.values()})
    print(f"{len(index)} examples across {cats} categories, hash {index_hash(index)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
