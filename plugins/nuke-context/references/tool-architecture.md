# Tool & pipeline architecture — exemplar repos

*Community field guide. Unofficial and unversioned — orientation, not authority.
These are real open-source tools to read for *structure*, not to copy wholesale.
Repo details (activity, versions) drift; check the live repos.*

There's no official "how to structure a Nuke tool" doc, so the best teacher is
real code. These exemplars sort by scale — and that order is also the recommended
reading order, because the big platforms are just the small patterns composed.

## Start small — the irreducible shape of a tool

Two render-submitter panels show the minimum viable structure:
- [gillesvink/NukeDeadlineSubmission](https://github.com/gillesvink/NukeDeadlineSubmission)
  (archived, but the tidiest) — a `deadline_submission/` core module, a
  `sanity_check.py` **pluggable pre-submit validation framework**, `resources/`
  for UI assets, and a `menu.py` install hook. Its key lesson: a **programmatic
  entry point** (`DeadlineSubmission().submit(node)`) kept separate from the UI
  trigger — a headless-callable core with a thin UI on top.
- [mellowpictures/render_submission](https://github.com/mellowpictures/render_submission)
  — how a small studio actually ships one panel: `python/` (logic),
  `resources/` (assets), `menu.py` (entry), introspecting the comp for frame
  ranges and pulling ShotGrid context to configure the job.

The shared shape: **`menu.py` hook → logic package → separate resources →
headless-callable core with a thin UI, plus a pluggable validation slot.**

## The framework archetypes

- [pyblish/pyblish-nuke](https://github.com/pyblish/pyblish-nuke) — the Nuke host
  adapter for Pyblish, the canonical **collect → validate → extract → integrate**
  publishing model. Study the **`setup()` / `teardown()` lifecycle**: `setup()`
  registers the host + plugins and injects the menu at startup, `teardown()`
  removes it cleanly; supports GUI and silent/headless publishing. (Caps at Nuke
  15 — study the pattern, verify against current Nuke.)
- [aws-deadline/deadline-cloud-for-nuke](https://github.com/aws-deadline/deadline-cloud-for-nuke)
  — the gold-standard **scene-introspection → declarative job template → farm
  runtime** split. The submitter analyses the comp for input files and render
  settings and emits an OpenJD job template; a separate adaptor implements the
  runtime with cross-platform **path mapping** and **task chunking** (frames
  grouped per task). Officially engineered (AWS), Nuke 15/16/17.

## Gizmo & node-graph craft

- [adrianpueyo/Stamps](https://github.com/adrianpueyo/Stamps) — a **proxy-node
  connection system** (Anchors ↔ Wired Stamps) for de-spaghetti-ing graphs,
  built on PostageStamp nodes + callbacks. Notable structure: a self-contained
  package, `init.py` registration, and a separate user-editable `stamps_config.py`
  (**config-as-code**), with menu injection and a hotkey.
- [openNuke/toolset](https://github.com/openNuke/toolset) — a gizmo/script library
  that installs via a **`_load.py` loader driven by JSON metadata** rather than a
  hand-written `menu.py` — the pattern for *distributing a gizmo library
  dynamically*. Designed for farm-safety and zero external deps.
- [Advanced Gizmo Building](https://www.keheka.com/advanced-gizmo-building-in-nuke/)
  (Kenn Hedin Kalvik; body paywalled, preview only) — the UI *theory*: **dynamic
  menus via Python, expression-driven controls, and progressive disclosure** (show
  only the knobs relevant to the current selection). Useful framing for *when* to
  build a gizmo and how to keep its UI honest.

## The full platforms — how the patterns compose

- [ynput/ayon-nuke](https://github.com/ynput/ayon-nuke) — a **client/server addon
  split** (`client/ayon_nuke/` in-DCC logic, `server/` settings) generated from a
  standardised addon template, so every DCC integration shares an identical
  skeleton. Production-grade, actively maintained.
- [masqu3rad3/tik_manager4](https://github.com/masqu3rad3/tik_manager4) — modular
  **core-vs-DCC separation** with a genuine `tests/` suite and cross-platform CI
  (including in-DCC testing) — a good exemplar of *how to test* a pipeline tool.
- [PrismPipeline/Prism](https://github.com/PrismPipeline/Prism) — a **core app +
  per-DCC plugins** architecture that ships a **bundled Python runtime** and
  vendored libs for a self-contained install. Read it for the core spine (the
  DCC-specific plugins are partly commercial/elsewhere).

## The net lesson

Across all of them: **separate core logic from host adapters from UI, express jobs
and config declaratively, keep the core headless-callable, and standardise a
per-DCC skeleton** so integrations stay uniform as the tool grows. Read a small
submitter first, then a framework archetype, then a platform.
