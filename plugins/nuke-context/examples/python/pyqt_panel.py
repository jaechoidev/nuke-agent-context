# pyqt_panel — nuke-agent example (original code).
# category: PyQt panel | teaches: a PySide6 widget registered as a Nuke panel
# verified: live in Nuke 17.0v3 (nuke-mcp)
"""A dockable panel that lists the selected nodes and can nudge them.

Teaches Nuke UI development the modern way: build a PySide6 QWidget, wire its
signals to nuke calls, and register it as a panel with
nukescripts.panels.registerWidgetAsPanel. Nuke 17 ships PySide6. Difficulty:
difficult.
"""
from PySide6 import QtWidgets

import nuke
import nukescripts


class NodeNudgePanel(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)
        self._label = QtWidgets.QLabel("(no selection)")
        layout.addWidget(self._label)

        row = QtWidgets.QHBoxLayout()
        refresh = QtWidgets.QPushButton("Refresh")
        refresh.clicked.connect(self.refresh)
        nudge = QtWidgets.QPushButton("Nudge +50x")
        nudge.clicked.connect(self.nudge)
        row.addWidget(refresh)
        row.addWidget(nudge)
        layout.addLayout(row)

        self.refresh()

    def refresh(self):
        names = [n.name() for n in nuke.selectedNodes()]
        self._label.setText(", ".join(names) if names else "(no selection)")

    def nudge(self):
        for node in nuke.selectedNodes():
            node.setXpos(node.xpos() + 50)
        self.refresh()


def register():
    """Call once (e.g. from menu.py) to add the panel to Nuke's Pane menu."""
    nukescripts.panels.registerWidgetAsPanel(
        "pyqt_panel.NodeNudgePanel", "Node Nudge", "nukeagent.NodeNudgePanel")
