#!/usr/bin/env python3
"""Locate Nuke installs and derive the paths the toolkit needs.

Knows filesystem layout only. Contains no C++ or index logic.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import pathlib
import re
import sys

# Nuke install directories look like: Nuke15.2v9, Nuke17.0v3, Nuke17.0v1-Beta.4
VERSION_RE = re.compile(r"\d+\.\d+v\d+")
DIR_RE = re.compile(r"Nuke(?P<version>\d+\.\d+v\d+)$")
# Bundled interpreters are named python3.10, python3.11 -- but the glob used to
# find them also matches python3.11-config, python3.11m and python3.1a, which
# are not interpreters. Match the exact shape instead.
_PY_RE = re.compile(r"python3\.(\d+)")


@dataclasses.dataclass(frozen=True)
class Install:
    """A usable Nuke install. Every path on it exists on disk."""

    version: str          # "17.0v3"
    root: pathlib.Path    # /Applications/Nuke17.0v3
    app: pathlib.Path
    binary: pathlib.Path
    python: pathlib.Path
    cmake_dir: pathlib.Path
    headers: pathlib.Path
    examples: pathlib.Path

    @property
    def major_minor(self) -> str:
        return self.version.split("v")[0]

    def to_dict(self) -> dict:
        d = {f.name: getattr(self, f.name) for f in dataclasses.fields(self)}
        return {k: (str(v) if isinstance(v, pathlib.Path) else v) for k, v in d.items()}


def _build(root: pathlib.Path, version: str) -> Install | None:
    app = root / f"Nuke{version}.app"
    macos = app / "Contents" / "MacOS"
    headers = root / "Documentation" / "NDKExamples" / "include" / "DDImage"
    if not headers.is_dir() or not any(headers.glob("*.h")):
        return None                      # docs-only or partial install
    major_minor = version.split("v")[0]
    binary = macos / f"Nuke{major_minor}"
    cmake_dir = macos / "cmake"
    examples = root / "Documentation" / "NDKExamples" / "examples"
    # Real interpreters only: python3.11-config has the same numeric key as
    # python3.11, so an unfiltered [-1] could pick it on arbitrary glob order.
    # Sort numerically, not lexically: "python3.9" must not outrank "python3.10".
    pys = sorted((p for p in macos.glob("python3.[0-9]*")
                  if _PY_RE.fullmatch(p.name) and p.is_file()),
                 key=lambda p: int(_PY_RE.fullmatch(p.name).group(1)))
    if not app.is_dir() or not binary.is_file() or not pys:
        return None
    if not cmake_dir.is_dir() or not examples.is_dir():
        return None                      # every path we hand out must exist
    return Install(
        version=version,
        root=root,
        app=app,
        binary=binary,
        python=pys[-1],
        cmake_dir=cmake_dir,
        headers=headers,
        examples=examples,
    )


def _version_key(name: str) -> list[int]:
    """Numeric sort key. Lexically, "Nuke9" sorts after "Nuke17" -- and Task 7
    takes find_installs()[-1] as the newest install, so a lexical sort would
    silently build against a legacy SDK on any machine with Nuke 9-14."""
    return [int(n) for n in re.findall(r"\d+", name)]


def find_installs(search_root: str | pathlib.Path = "/Applications") -> list[Install]:
    """Return every usable Nuke install, oldest first (numeric version order)."""
    out = []
    for child in sorted(pathlib.Path(search_root).glob("Nuke*"),
                        key=lambda c: _version_key(c.name)):
        m = DIR_RE.match(child.name)
        if not m or not child.is_dir():
            continue
        inst = _build(child, m.group("version"))
        if inst:
            out.append(inst)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Locate Nuke installs.")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--search-root", default="/Applications")
    args = ap.parse_args()

    installs = find_installs(args.search_root)
    if args.json:
        json.dump([i.to_dict() for i in installs], sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if not installs:
        print("No usable Nuke install found.", file=sys.stderr)
        return 1
    for i in installs:
        print(f"{i.version:<12} {i.root}  (python {i.python.name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
