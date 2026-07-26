# knob_linker — nuke-agent example (original code).
# category: callbacks | teaches: knobChanged callbacks and deferred, event-driven UI
# verified: live in Nuke 17.0v3 (nuke-mcp)
"""Reflect a Blur's size onto its node label whenever the user changes it.

Teaches the event-driven half of the Python paradigm: you do not poll: you
register a callback that Nuke fires when a knob changes. nuke.thisNode() and
nuke.thisKnob() identify what fired. Difficulty: mid.
"""
import nuke


def _on_knob_changed():
    node = nuke.thisNode()
    knob = nuke.thisKnob()
    if knob is not None and knob.name() == "size":
        node["label"].setValue("size %.1f" % knob.value())


def install():
    """Register for all Blur nodes. Call once from menu.py."""
    nuke.addKnobChanged(_on_knob_changed, nodeClass="Blur")


def uninstall():
    nuke.removeKnobChanged(_on_knob_changed, nodeClass="Blur")
