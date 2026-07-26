# backdrop_selected — nuke-agent example (original code).
# category: node graph | teaches: node position is data; sizing a BackdropNode
# verified: live in Nuke 17.0v3 (nuke-mcp); CI runs the static api-check
"""Create a BackdropNode sized to enclose the selected nodes.

Teaches that node layout is queryable data: xpos/ypos/screenWidth/screenHeight
give each node's screen-space box, and a backdrop is just a node placed and
sized around them.
"""
import nuke


def bounding_box(nodes, pad=50):
    """Screen-space (x, y, w, h) enclosing nodes, with padding."""
    xs = [n.xpos() for n in nodes]
    ys = [n.ypos() for n in nodes]
    rs = [n.xpos() + n.screenWidth() for n in nodes]
    ts = [n.ypos() + n.screenHeight() for n in nodes]
    x, y = min(xs) - pad, min(ys) - pad
    return x, y, (max(rs) + pad) - x, (max(ts) + pad) - y


def backdrop_selected(label="backdrop"):
    nodes = nuke.selectedNodes()
    if not nodes:
        return None
    x, y, w, h = bounding_box(nodes)
    bd = nuke.nodes.BackdropNode(xpos=x, ypos=y, bdwidth=w, bdheight=h)
    bd.knob("label").setValue(label)
    return bd
