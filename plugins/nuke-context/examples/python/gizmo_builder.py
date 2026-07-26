# gizmo_builder — nuke-agent example (original code).
# category: gizmo authoring | teaches: a gizmo is an authored Group with promoted knobs
# verified: live in Nuke 17.0v3 (nuke-mcp)
"""Build a reusable "blur glow" gizmo from scratch.

Teaches that a gizmo is not a subclass -- it is a Group you construct
(begin/end), wire an internal graph inside, and expose selected inner knobs on
the outside with Link_Knob. Difficulty: mid.
"""
import nuke


def build_blur_glow(name="BlurGlow"):
    group = nuke.nodes.Group(name=name)
    group.begin()
    try:
        inp = nuke.nodes.Input(name="Input")
        blur = nuke.nodes.Blur()
        blur.setInput(0, inp)
        grade = nuke.nodes.Grade()
        grade.setInput(0, blur)
        out = nuke.nodes.Output()
        out.setInput(0, grade)
    finally:
        group.end()

    # Promote inner knobs to the group's surface.
    size = nuke.Link_Knob("size", "glow size")
    group.addKnob(size)
    size.setLink(blur.name() + ".size")

    gain = nuke.Link_Knob("gain", "glow gain")
    group.addKnob(gain)
    gain.setLink(grade.name() + ".white")

    return group
