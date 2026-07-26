# select_downstream — nuke-agent example (original code).
# category: node graph | teaches: the graph as a data structure you traverse
# verified: live in Nuke 17.0v3 (nuke-mcp); CI runs the static api-check
"""Select every node downstream of the current selection.

Teaches the core Python paradigm: the node graph is a live data structure. You
walk it via each node's dependents, not by iterating a flat list.
"""
import nuke


def downstream(nodes):
    """Breadth-first walk over dependentNodes; returns the reachable set."""
    seen = set()
    frontier = list(nodes)
    while frontier:
        node = frontier.pop()
        for dep in node.dependent(nuke.INPUTS):
            if dep not in seen:
                seen.add(dep)
                frontier.append(dep)
    return seen


def select_downstream():
    start = nuke.selectedNodes()
    for node in downstream(start):
        node.setSelected(True)
