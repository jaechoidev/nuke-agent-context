# bake_expression — nuke-agent example (original code).
# category: knobs/animation | teaches: the knob animation model over a frame range
# verified: live in Nuke 17.0v3 (nuke-mcp); CI runs the static api-check
"""Bake an expression-driven knob into explicit keyframes.

Teaches that a knob holds animation, not just a value: reading it per frame with
getValueAt and writing keys with setValueAt is how you convert a live expression
into baked animation over the script's frame range.
"""
import nuke


def bake_knob(knob, first=None, last=None):
    root = nuke.root()
    if first is None:
        first = int(root.firstFrame())
    if last is None:
        last = int(root.lastFrame())
    values = {f: knob.getValueAt(f) for f in range(first, last + 1)}
    knob.clearAnimated()
    knob.setAnimated()
    for f, v in values.items():
        knob.setValueAt(v, f)


def bake_selected(knob_name):
    for node in nuke.selectedNodes():
        knob = node.knob(knob_name)
        if knob is not None:
            bake_knob(knob)
