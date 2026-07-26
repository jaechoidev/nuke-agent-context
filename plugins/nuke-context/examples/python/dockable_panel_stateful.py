# dockable_panel_stateful — nuke-context example (original code).
# category: PyQt panel | teaches: panel state persisted onto node knobs, surviving save/reload
# verified: API-checked against python_index (nuke-17.0)
"""A dockable panel whose state lives on the nodes, not in the widget.

The trap this example exists for: a PySide widget is *transient* — Nuke can
destroy and recreate panels at will (pane docking, workspace switches, script
reload), so any state held only in the widget silently disappears. The robust
pattern is to treat knobs as the storage layer: each note typed in the panel
is written to a hidden String_Knob on the node itself, so it saves with the
.nk script, survives panel teardown, and even travels when the node is
copy-pasted. The widget is a *view* of the graph, never the model.
Difficulty: difficult.
"""
from PySide6 import QtWidgets

import nuke
import nukescripts

NOTE_KNOB = "nc_artist_note"


def _note_knob(node):
    """Return the node's note knob, creating it (hidden) on first use."""
    knob = node.knob(NOTE_KNOB)
    if knob is None:
        knob = nuke.String_Knob(NOTE_KNOB, "artist note")
        knob.setVisible(False)
        node.addKnob(knob)
    return knob


class NodeNotesPanel(QtWidgets.QWidget):
    """List selected nodes; keep a per-node note that persists in the script."""

    def __init__(self):
        super().__init__()
        layout = QtWidgets.QVBoxLayout(self)

        self._nodes = QtWidgets.QListWidget()
        self._nodes.currentTextChanged.connect(self._load_note)
        layout.addWidget(self._nodes)

        self._note = QtWidgets.QPlainTextEdit()
        self._note.setPlaceholderText("Note for the selected node…")
        layout.addWidget(self._note)

        row = QtWidgets.QHBoxLayout()
        refresh = QtWidgets.QPushButton("Refresh selection")
        refresh.clicked.connect(self.refresh)
        save = QtWidgets.QPushButton("Save note to node")
        save.clicked.connect(self._save_note)
        row.addWidget(refresh)
        row.addWidget(save)
        layout.addLayout(row)

        self.refresh()

    def refresh(self):
        self._nodes.clear()
        for node in nuke.selectedNodes():
            self._nodes.addItem(node.name())

    def _load_note(self, name):
        node = nuke.toNode(name) if name else None
        if node is None:
            self._note.setPlainText("")
            return
        knob = node.knob(NOTE_KNOB)
        self._note.setPlainText(knob.value() if knob else "")

    def _save_note(self):
        item = self._nodes.currentItem()
        if item is None:
            return
        node = nuke.toNode(item.text())
        if node is None:
            return
        # The knob is the model: after this line the note is part of the
        # script — saved with the .nk, restored on load, panel or no panel.
        _note_knob(node).setValue(self._note.toPlainText())


# Registration: Nuke owns panel lifecycle. The id must be unique; the menu
# path puts it in Pane -> Custom alongside the built-ins.
nukescripts.panels.registerWidgetAsPanel(
    "dockable_panel_stateful.NodeNotesPanel", "Node Notes",
    "com.nukecontext.NodeNotesPanel")
