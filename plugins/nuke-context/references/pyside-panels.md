# PySide / panel UI — the practitioner landscape

*Community field guide. Unofficial and unversioned — orientation, not authority.
Nuke's Qt binding is PySide (PySide6 on Nuke 16/17). Our
`examples/python/pyqt_panel.py` is a working PySide6 panel. Verify APIs against
`refs/nuke-<VER>/python_index.md` and the custom-panels page in `pyguide_index.md`.*

Building a panel in Nuke trips up a strong Qt developer in three specific places —
registration, lifecycle, and the binding version. Every resource here lives in one
of those three layers.

## 1. Registration & docking — Nuke owns it, not Qt

The canonical pattern is Foundry's
[Custom Panels reference](https://learn.foundry.com/nuke/developers/140/pythonreference/custom_panels.html)
(documented against Nuke 14 / PySide2): subclass a `QWidget`, then

```
nukescripts.panels.registerWidgetAsPanel('module.Class', label, 'reverse.url.id', create).addToPane(nuke.getPaneFor(...))
```

Three non-obvious points a general Qt dev gets wrong:
- **You pass the widget as a string path** (`"module.Class"`), not a live instance
  — Nuke re-instantiates it. Instantiating and `show()`-ing your widget is the
  wrong model.
- **Docking is Nuke's, not Qt's.** You don't use `QDockWidget`; registration +
  `addToPane()` gives you docking, and the registered panel appears under
  **Windows → Custom**.
- **The reverse-URL `id`** (`com.you.tool`) is what lets Nuke save the panel into
  a workspace layout and restore it on relaunch — change or omit it and
  persistence breaks.

[jedypod's gist](https://gist.github.com/jedypod/0c2b89cf047b0bc5cebed109d707fa69)
shows the full register-and-dock idiom end to end (`registerWidgetAsPanel(...).addToPane(nuke.getPaneFor(...))`),
but it's **PySide 1** (`QtGui`, not `QtWidgets`) and has a `closeEvent` bug — read
it for the mechanics, modernise the imports before running.

## 2. Lifecycle — the panel widget is transient

The trap that catches everyone: **Nuke destroys and re-instantiates the panel
widget on close and on layout-restore**, so any in-memory Qt state you hold on
`self` evaporates. The fix is to push values into **hidden native Nuke knobs** on
a node, so the value survives destruction and travels with the script —
[stefanmuller/nuke_PySide_helper](https://github.com/stefanmuller/nuke_PySide_helper)
is a proof-of-concept built entirely around this idiom (QWidgets that auto-persist
onto knobs). It's narrow and dated, but the concept is the important part.

## 3. Binding version — the PySide6 migration

The version map, now well-established:

| Nuke | Python | Qt binding |
| --- | --- | --- |
| ≤ 10 | 2 | PySide (1) |
| 11–15 | 2/3 | PySide2 |
| 16–17 | 3.11 | **PySide6** |

The durable pattern is a **binding-detection shim** that prioritises PySide6 and
falls back, so one tool runs across versions.
[georgeantonopoulos/W_Hotbox_Nuke16](https://github.com/georgeantonopoulos/W_Hotbox_Nuke16)
is the cleanest artifact for the *migration mechanics* — a tri-version import
ladder (PySide6 for 16+, PySide2 for 11–15, PySide for ≤10) plus error handling
around the imports, ported from Wouter Gilsing's original
[W_hotbox](https://github.com/melMass/W_hotbox) (which is itself a good contrast
case: a *transient hotkey-triggered floating popup*, not a registered dockable
pane). [shiningdesign/universal_tool_template](https://github.com/shiningdesign/universal_tool_template.py)
generalises the idea to a cross-DCC binding shim (the manual precursor to `Qt.py`),
though it predates PySide6.

The best *living* example of the whole stack is
[adrianpueyo/KnobScripter](https://github.com/adrianpueyo/KnobScripter): a
full-featured registered panel whose v3.2 added Nuke 16 / PySide6 support while
staying compatible with older versions — the multi-version bar to match.

## Where to start

Foundry's reference for the registration API, our `examples/python/pyqt_panel.py`
for a modern PySide6 panel, `nuke_PySide_helper` for the knob-persistence idiom,
and `W_Hotbox_Nuke16` for the exact PySide2→PySide6 import ladder. Treat any
pre-PySide2 gist as a mechanics reference whose `QtGui`→`QtWidgets` imports must be
modernised first.
