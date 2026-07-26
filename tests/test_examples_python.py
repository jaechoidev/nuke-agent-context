"""Python examples are API-checked against the generated index, not executed
(that needs a licensed Nuke). Two high-signal checks:

  * every `nuke.<name>` reference is a real top-level symbol or a known constant
  * every method call is a documented Nuke method leaf-name or a Python builtin

Catches invented APIs (`nuke.magicMerge`, `node.growBox()`). This is the CI floor;
`evals/verify_live.py` runs the tools in a real Nuke for the stronger check (and
found node.dependentNodes -- a real name, but a module function, not a method).
"""
import ast
import importlib.util
import pathlib
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent
PY_EXAMPLES = REPO / "plugins" / "nuke-context" / "examples" / "python"

# Module-level constants the autosummary does not index (they are ints, not
# documented callables) but which are real Nuke API.
NUKE_CONSTANTS = {"INPUTS", "EXPRESSIONS", "HIDDEN_INPUTS", "nodes", "math",
                  "GUI", "root", "thisNode", "thisKnob"}

# Python container/stdlib methods that are not Nuke API and must be allowed.
PY_METHODS = {"pop", "append", "add", "items", "keys", "values", "get",
              "update", "remove", "insert", "sort", "join", "split", "strip",
              "format", "startswith", "endswith", "lower", "upper", "extend"}


def load_py_index(tools_root, nuke_installs):
    for i in nuke_installs:
        auto = i["root"] / "Documentation" / "PythonDevGuide" / "Nuke" / "_autosummary"
        if auto.is_dir():
            p = tools_root / "extract_python_api.py"
            spec = importlib.util.spec_from_file_location("extract_python_api", p)
            mod = importlib.util.module_from_spec(spec)
            sys.modules["extract_python_api"] = mod
            spec.loader.exec_module(mod)
            idx = mod.build_index(auto)
            top = {s.name.split("nuke.", 1)[1] for s in idx.values()
                   if s.kind in ("class", "function") and s.name.count(".") == 1}
            methods = mod.method_names(idx)
            return top, methods
    return set(), set()


def examples():
    return sorted(PY_EXAMPLES.glob("*.py"))


def _nuke_refs_and_calls(src):
    """Return (nuke.<name> names, method-call leaf names) via the AST."""
    tree = ast.parse(src)
    nuke_names, methods = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            # nuke.<name>
            if isinstance(node.value, ast.Name) and node.value.id == "nuke":
                nuke_names.add(node.attr)
            # <expr>.<method>(...) captured as a call below
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            methods.add(node.func.attr)
    return nuke_names, methods


def test_there_is_a_python_corpus():
    assert examples(), "no Python examples"


@pytest.mark.parametrize("example", examples(), ids=lambda p: p.name)
def test_python_example_parses(example):
    ast.parse(example.read_text())    # syntactically valid


@pytest.mark.parametrize("example", examples(), ids=lambda p: p.name)
def test_python_example_uses_only_real_nuke_api(tools_root, nuke_installs, example):
    """CI checks the high-signal thing: every `nuke.<X>` module reference is real.

    It deliberately does NOT lint arbitrary method calls -- those include Qt
    (addWidget, connect), node construction (nuke.nodes.Blur), and Nuke methods
    the autosummary omits, so the check false-positives on correct code. Method
    correctness is proven the right way, by running the tool in a real Nuke
    (evals/verify_live.py) -- which caught node.dependentNodes, a real name but
    a module function, that no static leaf-name check could.
    """
    top, _ = load_py_index(tools_root, nuke_installs)
    if not top:
        pytest.skip("no Python docs found")
    nuke_names, _ = _nuke_refs_and_calls(example.read_text())
    bad_refs = sorted(n for n in nuke_names if n not in top and n not in NUKE_CONSTANTS)
    assert not bad_refs, f"{example.name}: nuke.<X> not in the API: {bad_refs}"


@pytest.mark.parametrize("example", examples(), ids=lambda p: p.name)
def test_python_example_states_its_verification(example):
    head = example.read_text()[:400].lower()
    assert "original" in head, f"{example.name}: does not state it is original"
    assert "verified:" in head, f"{example.name}: must state a verification status"


def test_api_check_catches_invented_python_api(tools_root, nuke_installs):
    top, methods = load_py_index(tools_root, nuke_installs)
    if not top:
        pytest.skip("no Python docs found")
    bad = "import nuke\nnuke.magicMerge()\nnuke.selectedNodes()[0].growBox()\n"
    nuke_names, calls = _nuke_refs_and_calls(bad)
    assert "magicMerge" not in top and "magicMerge" not in NUKE_CONSTANTS
    assert "growBox" not in methods and "growBox" not in PY_METHODS
