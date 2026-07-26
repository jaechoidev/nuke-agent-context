# Nuke Python — the practitioner landscape

*Community field guide. Unofficial and unversioned — orientation, not authority.
For the API use `refs/nuke-<VER>/python_index.md` and the Python guide map
(`pyguide_index.md`); for how-to prose the Nuke Python Developer's Guide is on
Context7. Verify anything here against those.*

The one idea every community source circles back to — and the thing a strong
general Python developer gets wrong first — is that **in Nuke, code and tools are
not files-first.** Tools are nodes; state lives on knobs; scripts live *on* nodes.
Once that clicks, the rest is ordinary Python.

## The mental-model gaps worth internalising

**A gizmo is a serialized node, not a class.** You author it by selecting nodes
in the DAG and grouping them (Ctrl/Cmd+G), then saving the Group to a `.gizmo`
text file — not by writing a Python class. Even the node's icon is just a line
inside that text file. Nukepedia's
[gizmo tutorials](https://www.nukepedia.com/knowledge/code-tutorials/gizmos/)
(SwitchMatte, "Adding a Gizmo Icon", custom menus) teach this directly; it's
legacy and undated but the group→gizmo model is still exactly how it works.

**`init.py` vs `menu.py` is a load-context split, not a style choice.**
`init.py` runs in *every* session including headless render nodes, so plugin
*paths* (`nuke.pluginAddPath()`) go there; `menu.py` runs only when the GUI
launches, so *menu and command* registration goes there. Put UI code in `init.py`
and you break batch renders. Nuke auto-scans `~/.nuke` at startup — the whole
plugin system is filesystem convention, not an install step. Nukepedia's
[getting started with plugins](https://www.nukepedia.com/knowledge/general-tutorials/getting-started-with-nuke-plugins/)
is the clearest write-up (gizmo-focused, overlaps the official startup-scripts
docs).

**Knobs are objects, accessed dict-style.** `node['size']` returns a *Knob*, not a
value — you call `.setValue()` / `.getValue()`; `node['size'] = 10` does not do
what a Python dev expects. And `nuke.toNode('Blur1')` looks a node up by its live
DAG name (a mutable global namespace), not by a variable reference. Alexander
Richter's
[Mastering Python to Enhance Nuke Workflows](https://www.alexanderrichtertd.com/post/mastering-python-to-enhance-nuke-workflows)
(current, Sep 2025) is a solid motivation-and-basics read that makes these idioms
concrete, though it stays near the official getting-started material and doesn't
reach the harder traps (animation curves, deferred/expression evaluation,
callbacks — those are in our `nuke-python-model` skill and the Foundry guide).

**Code lives on knobs.** This is the deepest Nuke-specific fact: a node can carry
Python *button* knobs and *callback* knobs (`knobChanged`, `onCreate`, …) whose
bodies are strings stored inside the knob, plus inline BlinkScript. Adrian Pueyo's
[KnobScripter](https://adrianpueyo.com/knobscripter/) (v3, current, GPL-v3) exists
precisely to give that per-knob code an IDE — File Mode for `.py` files, Node
Editing Mode for on-knob Python and Blink, a snippets system and code gallery.
It's the de-facto community-standard editor and a good example to study; the file
scripts vs. per-node knob scripts duality is the concept it's built around.

## Currency and caveats

- **Current:** Richter (2025), KnobScripter (v3). Trust these first.
- **Legacy but still correct on fundamentals:** the Nukepedia pieces (undated,
  gizmo-centric; specific menu snippets may duplicate the official guide).
- **Ben McEwan's** [Nuke/Python blog](https://benmcewan.com/blog/category/nuke/python/)
  is a well-regarded practical-scripts source, but the post listing is
  JS-rendered and didn't load for review — treat individual posts as unverified
  until read directly. His public tools repo is `github.com/BenMcEwan/nuke_public`;
  his "Python for Nuke 101" course is self-marked end-of-life.

## Where to start

Read our `nuke-python-model` skill for the paradigm, then Richter for gentle
motivation. When you're authoring per-node code or gizmos, KnobScripter is both a
tool and a worked reference. Confirm every `nuke.*` call against `python_index.md`
before writing it — community snippets predate current versions.
