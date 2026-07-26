#!/usr/bin/env python3
"""Verify the example corpus against a running, licensed Nuke via nuke_bridge.

Requires Nuke open with the nuke-mcp addon started (see evals/nuke_bridge.py).
Blink kernels are compiled in a real BlinkScript node; Python tools are run
against a real node graph and their effect checked. This is the live tier above
the static API-check that CI runs -- it catches real-name-wrong-object bugs a
static index cannot (e.g. node.dependentNodes, which is a module function).

  python3 evals/verify_live.py
"""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import nuke_bridge as nb  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parent.parent
EX = REPO / "plugins" / "nuke-agent" / "examples"
PYDIR = EX / "python"

# Each Python check: setup graph, run the tool, assert. Kept as source sent to
# the live Nuke. `result` must be set to a bool. Plain loops only -- list
# comprehensions do not see enclosing locals under the addon's exec().
PY_CHECKS = {
    "select_downstream": f'''
import sys, importlib, nuke
sys.path.insert(0, {str(PYDIR)!r})
for n in list(nuke.allNodes()): nuke.delete(n)
a = nuke.nodes.NoOp(name="A"); b = nuke.nodes.NoOp(name="B"); b.setInput(0,a)
c = nuke.nodes.NoOp(name="C"); c.setInput(0,b)
for n in nuke.allNodes(): n.setSelected(False)
a.setSelected(True)
m = importlib.import_module("select_downstream"); importlib.reload(m)
m.select_downstream()
sel = sorted(n.name() for n in nuke.selectedNodes())
for n in list(nuke.allNodes()): nuke.delete(n)
result = sel == ["A","B","C"]
''',
    "backdrop_selected": f'''
import sys, importlib, nuke
sys.path.insert(0, {str(PYDIR)!r})
for n in list(nuke.allNodes()): nuke.delete(n)
nuke.nodes.Blur().setSelected(True); nuke.nodes.Grade().setSelected(True)
m = importlib.import_module("backdrop_selected"); importlib.reload(m)
bd = m.backdrop_selected("t")
ok = bd is not None and bd.Class() == "BackdropNode" and bd.knob("label").value() == "t"
for n in list(nuke.allNodes()): nuke.delete(n)
result = ok
''',
    "bake_expression": f'''
import sys, importlib, nuke
sys.path.insert(0, {str(PYDIR)!r})
for n in list(nuke.allNodes()): nuke.delete(n)
nuke.root()["first_frame"].setValue(1); nuke.root()["last_frame"].setValue(5)
b = nuke.nodes.Blur(name="B"); b.setSelected(True)
b["size"].setExpression("frame*2")
m = importlib.import_module("bake_expression"); importlib.reload(m)
m.bake_selected("size")
k = b["size"]; vals = []
for f in range(1, 6):
    vals.append(k.getValueAt(f))
ok = bool(k.isAnimated()) and vals == [2.0,4.0,6.0,8.0,10.0]
for n in list(nuke.allNodes()): nuke.delete(n)
result = ok
''',
    "gizmo_builder": f'''
import sys, importlib, nuke
sys.path.insert(0, {str(PYDIR)!r})
for n in list(nuke.allNodes()): nuke.delete(n)
m = importlib.import_module("gizmo_builder"); importlib.reload(m)
g = m.build_blur_glow("G")
knobs = []
for k in ["size", "gain"]:
    if g.knob(k) is not None: knobs.append(k)
ok = g.Class() == "Group" and knobs == ["size", "gain"]
for n in list(nuke.allNodes()): nuke.delete(n)
result = ok
''',
    "pyqt_panel": f'''
import sys, importlib
sys.path.insert(0, {str(PYDIR)!r})
m = importlib.import_module("pyqt_panel"); importlib.reload(m)
w = m.NodeNudgePanel()
result = w is not None and w._label.text() == "(no selection)"
''',
    "knob_linker": f'''
import sys, importlib
sys.path.insert(0, {str(PYDIR)!r})
m = importlib.import_module("knob_linker"); importlib.reload(m)
m.install(); m.uninstall()
result = True
''',
}


def main() -> int:
    try:
        if nb.call("ping").get("result") != "pong":
            print("Nuke addon did not pong", file=sys.stderr)
            return 1
    except Exception as e:
        print(f"cannot reach Nuke ({e}); open Nuke + nuke_mcp_addon.start()", file=sys.stderr)
        return 1

    ident = nb.execute("import nuke; result = nuke.NUKE_VERSION_STRING")["result"]
    print(f"live Nuke {ident}\n")
    failures = 0

    print("BlinkScript (loaded into a real BlinkScript node; kernelName must match):")
    for k in sorted((EX / "blink").rglob("*.blink")):
        r = nb.blink_compile(str(k))
        ok = r.get("status") == "ok" and r.get("result") == "ok"
        print(f"  {'PASS' if ok else 'FAIL'}  {k.name}  {'' if ok else r.get('result', r)}")
        failures += not ok

    print("\nPython (run against a real node graph):")
    for name, code in PY_CHECKS.items():
        r = nb.execute(code)
        ok = r.get("status") == "ok" and r.get("result") is True
        print(f"  {'PASS' if ok else 'FAIL'}  {name}  {'' if ok else r.get('error', r.get('result'))}")
        failures += not ok

    print(f"\n{'all live checks passed' if not failures else f'{failures} FAILED'}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
