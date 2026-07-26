"""Blink examples are API-checked, not runtime-compiled (that needs a licensed
Nuke). The check is a lint: every function call must be a known Blink built-in
or something the kernel declares. It catches invented built-ins -- the main
hallucination risk -- not semantic errors, which is why these examples ship
labelled "unverified".
"""
import importlib.util
import pathlib
import re
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
BLINK_EXAMPLES = REPO / "plugins" / "nuke-context" / "examples" / "blink"

CALL_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
DECL_RE = re.compile(r"\b(?:float|int|bool|float2|float3|float4|void)\d?\s+(\w+)")
COMMENT_RE = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)


def _code(src: str) -> str:
    """Strip comments -- lint the kernel, not the prose in its header."""
    return COMMENT_RE.sub(" ", src)
CONTROL = {"for", "if", "while", "return", "else", "switch"}
# Blink methods/built-ins the kernel API exposes beyond the maths library:
# lifecycle, Image access methods, and bounds accessors.
BLINK_API = {"defineParam", "setRange", "setAxis", "define", "init", "process",
             "bounds", "at", "median", "print", "kernel",
             "width", "height", "x", "y", "x1", "y1", "x2", "y2"}


def load_blink_index(tools_root):
    p = tools_root / "extract_blink_api.py"
    spec = importlib.util.spec_from_file_location("extract_blink_api", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["extract_blink_api"] = mod
    spec.loader.exec_module(mod)
    return mod


def blink_builtins(tools_root, nuke_installs):
    for i in nuke_installs:
        ref = i["root"] / "Documentation" / "BlinkUserGuide" / "BlinkKernelAPIReference"
        if ref.is_dir():
            mod = load_blink_index(tools_root)
            return set(mod.build_index(ref))
    return set()


def kernels():
    return sorted(BLINK_EXAMPLES.rglob("*.blink"))


def test_there_is_a_blink_corpus():
    assert kernels(), "no Blink examples"


@pytest.mark.parametrize("kernel", kernels(), ids=lambda p: p.name)
def test_blink_kernel_is_well_formed(kernel):
    src = kernel.read_text()
    assert "kernel" in src and "ImageComputationKernel" in src, f"{kernel.name}: not a kernel"
    assert re.search(r"\bprocess\s*\(", src), f"{kernel.name}: no process()"


@pytest.mark.parametrize("kernel", kernels(), ids=lambda p: p.name)
def test_blink_kernel_calls_only_known_builtins(tools_root, nuke_installs, kernel):
    builtins = blink_builtins(tools_root, nuke_installs)
    if not builtins:
        pytest.skip("no Blink reference found")
    src = _code(kernel.read_text())
    declared = set(DECL_RE.findall(src))
    declared |= set(re.findall(r"\b(\w+)\s*;", src))       # member/param names
    known = builtins | BLINK_API | CONTROL | declared
    unknown = sorted({c for c in CALL_RE.findall(src) if c not in known})
    assert not unknown, f"{kernel.name}: calls not in the Blink API: {unknown}"


@pytest.mark.parametrize("kernel", kernels(), ids=lambda p: p.name)
def test_blink_example_states_its_verification(kernel):
    head = kernel.read_text()[:400].lower()
    assert "original" in head, f"{kernel.name}: does not state it is original"
    assert "verified:" in head, f"{kernel.name}: must state a verification status"


def test_api_check_would_catch_an_invented_builtin(tools_root, nuke_installs, tmp_path):
    """The lint must actually fail on a fabricated built-in, or it proves nothing."""
    builtins = blink_builtins(tools_root, nuke_installs)
    if not builtins:
        pytest.skip("no Blink reference found")
    bad = "kernel K : public ImageComputationKernel<ePixelWise> {\n" \
          "  void process() { dst() = superBlur(src()); }\n};\n"
    declared = set(DECL_RE.findall(bad)) | set(re.findall(r"\b(\w+)\s*;", bad))
    known = builtins | BLINK_API | CONTROL | declared | {"dst", "src"}
    unknown = {c for c in CALL_RE.findall(bad) if c not in known}
    assert "superBlur" in unknown, "the lint failed to catch an invented built-in"
