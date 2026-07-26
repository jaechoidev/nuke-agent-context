---
name: nuke-python-model
description: The Nuke Python mental model - the node graph as a live data structure, the knob/animation model, callbacks and deferred evaluation, and gizmo/group authoring. Use when writing or designing a Nuke tool in Python, after nuke-tool-structure sets the overall paradigm.
---

# The Nuke Python model

Read `nuke-tool-structure` first for the paradigm. This is the Python specifics.

Python in Nuke is not application scripting against an API — it is manipulating a **live node
graph**. Most Python tools read or rewrite that graph, or respond to it changing. The
different-from-normal parts:

## 1. The node graph is a mutable data structure

Nodes are objects; you query and rewire them.
- `nuke.allNodes()`, `nuke.selectedNodes()`, `nuke.toNode(name)` to get them.
- `node.input(i)`, `node.setInput(i, other)`, `node.dependencies()`, `node.dependentNodes()`
  to walk and rewire connections.
- Position is data too: `node.xpos()`, `node.ypos()`, `node.screenWidth()` — how tools size
  backdrops and lay out graphs.

Confirm any method against the Python index
(`${CLAUDE_PLUGIN_ROOT}/refs/nuke-<VER>/python_index.md`, grep — never read it whole) —
6000+ signatures. A method that is not there does not exist. For *how it behaves* (argument
semantics, examples), follow the row's Docs URL. See `nuke-api-lookup`.

For the *concepts* — which guide page covers callbacks, custom panels, threading, the node
graph, channels — `refs/nuke-<VER>/pyguide_index.md` maps topic → guide page (grep
`pyguide_map.tsv` by keyword). Read the page for the paradigm, then confirm exact calls in the
symbol index.

## 2. Knobs hold values *and* animation

A knob is not a scalar. `knob.value()` / `knob.setValue()` read/write the current value;
`knob.getValueAt(frame)` / `knob.setValueAt(v, frame)` handle animation; `knob.setExpression()`
links it. Baking an expression to keys means iterating the frame range and calling
`setValueAt` — the animation model is explicit, not implicit.

## 3. Evaluation is deferred, and callbacks fire on graph events

Nuke does not recompute when you set a knob — it defers until a pull. Tools hook lifecycle
events instead of polling: `nuke.addOnCreate`, `nuke.addOnScriptLoad`,
`knob.setFlag`/`knobChanged` callbacks. Do the minimum in a callback; it runs inside Nuke's
event loop.

## 4. Gizmos and groups are authored graphs

A gizmo is a saved `Group` with promoted knobs. Building one is graph construction
(`nuke.nodes.<Class>(...)`, `group.begin()/end()`), not subclassing.

## Structure still applies

The thin-shell/pure-core split holds here too: put logic that does not need `nuke` in a
plain module you can test with pytest, and keep the `import nuke` layer thin. If it needs a
running Nuke, it is verified with `nuke -t`, not a unit test (see `nuke-tool-structure`).

## Examples to read

Original nuke-context tools: `${CLAUDE_PLUGIN_ROOT}/examples/python/` (labelled — Python
examples are API-checked against the index, not executed, because that needs a licensed
Nuke). Confirm methods against the Python index.

## Practitioner field guide

`${CLAUDE_PLUGIN_ROOT}/references/python.md` (code-on-knobs, gizmo-as-serialized-node, the
`init.py`/`menu.py` split) and, for panel UI, `references/pyside-panels.md`
(registerWidgetAsPanel, the transient-widget/persist-to-knobs trap, the PySide2→PySide6
migration). Community sources: the guide tells you *where to look*, the official tier tells
you *what is true*. Verify any claim from it against the index, the guide pages, or
`nuke -t` before it shapes code; surface what you cannot verify as unverified.
