#!/usr/bin/env python3
"""Objective graders for the nuke-agent ablation.

No LLM judge. Nuke's headers say whether a symbol exists and the compiler says
whether the code works, so the two metrics that matter here need no opinion:

  includes  - does every #include "DDImage/X.h" name a real header?
  symbols   - is every DD::Image::X used a class that exists in this version?
  compiles  - does the generated plugin actually build?

`compiles` subsumes the other two, but they are reported separately because
they isolate *hallucination* from ordinary C++ mistakes. A model can invent a
class and also forget a semicolon; only the first is the failure this toolkit
exists to prevent.
"""
from __future__ import annotations

import importlib.util
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
PLUGIN = REPO / "plugins" / "nuke-context"
TOOLS = REPO / "tools"

FENCE_RE = re.compile(r"```(?:cpp|c\+\+|cxx|c)?\n(.*?)```", re.S)
INCLUDE_RE = re.compile(r'#\s*include\s+[<"]DDImage/([A-Za-z0-9_]+)\.h[>"]')
QUALIFIED_RE = re.compile(r"\bDD::Image::([A-Z]\w+)")


def _load(name: str):
    spec = importlib.util.spec_from_file_location(
        name, TOOLS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def extract_code(response: str) -> str:
    """Pull C++ out of the response. Prefer fenced blocks; fall back to raw."""
    blocks = FENCE_RE.findall(response)
    if blocks:
        return max(blocks, key=len)
    return response if "#include" in response else ""


def grade_includes(code: str, headers_dir: pathlib.Path) -> dict:
    """Every #include "DDImage/X.h" must name a header that exists."""
    named = sorted(set(INCLUDE_RE.findall(code)))
    missing = [n for n in named if not (headers_dir / f"{n}.h").is_file()]
    return {"total": len(named), "invalid": missing,
            "ok": len(named) - len(missing)}


def grade_symbols(code: str, index: dict) -> dict:
    """Every DD::Image::X must be a class this Nuke version actually declares.

    Compared against the base (unqualified) names in the index, because source
    code writes DD::Image::Description, not Op::Description.
    """
    bases = {s.rsplit("::", 1)[-1] for s in index}
    used = sorted(set(QUALIFIED_RE.findall(code)))
    invalid = [u for u in used if u not in bases]
    return {"total": len(used), "invalid": invalid, "ok": len(used) - len(invalid)}


def grade_compiles(code: str, cmake_dir: pathlib.Path) -> dict:
    """Build the generated plugin. The compiler is the final authority."""
    if not code.strip():
        return {"compiles": False, "reason": "no code produced"}
    if shutil.which("cmake") is None:
        return {"compiles": None, "reason": "cmake unavailable"}

    with tempfile.TemporaryDirectory() as td:
        proj = pathlib.Path(td)
        (proj / "src" / "ops").mkdir(parents=True)
        (proj / "src" / "ops" / "Generated.cpp").write_text(code)
        tmpl = (PLUGIN / "examples" / "ndk"
                / "CMakeLists.txt.example").read_text()
        (proj / "CMakeLists.txt").write_text(
            tmpl.replace("@PROJECT@", "Generated")
                .replace("@NUKE_CMAKE_DIR@", str(cmake_dir)))

        cfg = subprocess.run(["cmake", "-S", str(proj), "-B", str(proj / "build")],
                             capture_output=True, text=True)
        if cfg.returncode != 0:
            return {"compiles": False, "reason": "configure failed",
                    "log": cfg.stderr[-1500:]}
        b = subprocess.run(["cmake", "--build", str(proj / "build")],
                           capture_output=True, text=True)
        if b.returncode != 0:
            errs = [l for l in (b.stdout + b.stderr).splitlines()
                    if "error:" in l]
            out = {"compiles": False, "reason": "build failed",
                   "errors": errs[:8], "error_count": len(errs)}
            out.update(classify_errors(errs))
            return out
        return {"compiles": True}


# The compiler names precisely what was invented, which is a better oracle than
# any regex over the source. Distinguishes "made up an API" from "wrote bad C++".
HALLUCINATION_PATTERNS = [
    re.compile(r"no member named '([^']+)' in '([^']+)'"),
    re.compile(r"no type named '([^']+)' in '([^']+)'"),
    re.compile(r"unknown type name '([^']+)'"),
    re.compile(r"use of undeclared identifier '([^']+)'"),
    re.compile(r"'([^']+)' file not found"),
    re.compile(r"no matching (?:member )?function for call to '([^']+)'"),
]


def classify_errors(errors: list[str]) -> dict:
    """Split compile errors into invented-API vs ordinary C++ mistakes."""
    invented, other = [], 0
    for line in errors:
        hit = None
        for pat in HALLUCINATION_PATTERNS:
            m = pat.search(line)
            if m:
                hit = "::".join(reversed(m.groups())) if len(m.groups()) == 2 \
                    else m.group(1)
                break
        if hit:
            invented.append(hit)
        else:
            other += 1
    return {"invented_api": sorted(set(invented)),
            "invented_api_count": len(set(invented)),
            "other_cpp_errors": other}


def grade(response: str, install) -> dict:
    index = _load("extract_ndk_index").build_index(install.headers)
    code = extract_code(response)
    return {
        "produced_code": bool(code.strip()),
        "code_bytes": len(code),
        "includes": grade_includes(code, install.headers),
        "symbols": grade_symbols(code, index),
        "build": grade_compiles(code, install.cmake_dir),
    }


def newest_install():
    installs = _load("nuke_detect").find_installs()
    if not installs:
        raise SystemExit("no Nuke install found")
    return installs[-1]


if __name__ == "__main__":
    text = pathlib.Path(sys.argv[1]).read_text()
    import json
    json.dump(grade(text, newest_install()), sys.stdout, indent=2)
    print()
