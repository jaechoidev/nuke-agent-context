# Curation sources — review tracker

**2026-07-25:** first distillation pass complete — the community field guides
in `plugins/nuke-context/references/` (ported from nuke-agent-toolkit) are the
output of this list. Rows remain for future re-review as sources evolve.

Status: `pending` = awaiting Jae's review · `keep` = approved for distillation ·
`drop` = rejected · `done` = distilled into a skill/reference file.

Rule for distillation: only extract facts the model would otherwise get wrong.
Paraphrase, attribute with a link per claim, never republish prose.

## NDK (C++)

| Status | Source | Why / what to mine |
| --- | --- | --- |
| pending | [Erwan Leroy — NDK series Part 1: Intro & Compiling](https://erwanleroy.com/intro-to-writing-nuke-c-plugins-a-k-a-the-ndk-part-1-intro-compiling/) | Build setup gotchas per platform |
| pending | [Part 2: Architecture, validate, knobs](https://erwanleroy.com/writing-nuke-c-plugins-a-k-a-the-ndk-part-2-architecture-the-validate-and-knobs-functions-and-first-simple-plugins/) | Op lifecycle as practitioners actually explain it |
| pending | [Part 3: engine and pixel_engine](https://erwanleroy.com/writing-nuke-c-plugins-a-k-a-the-ndk-part-3-engine-and-pixel-engine-functions/) | Scanline engine model, threading pitfalls |
| pending | [Part 4: Custom knobs, GL handles, table knob](https://erwanleroy.com/writing-nuke-c-plugins-ndk-part-4-custom-knobs-gl-handles-and-the-table-knob/) | Barely-documented knob/GL surface |
| pending | [Part 5: PointGradient node (full example)](https://erwanleroy.com/writing-nuke-c-plugins-ndk-part-5-the-pointgradient-node/) | Complete real tool walkthrough |
| pending | [Max van Leeuwen — Nuke NDK guide](https://maxvanleeuwen.com/project/nuke-ndk/) | Windows/Linux build friction points |
| pending | [DeepC (charlesangus) — GitHub](https://github.com/charlesangus/DeepC) | Real DeepOp source; mine for deep examples |
| pending | [Vivek Reddy — Getting started with the NDK](https://www.vivekc.com/getting-started-with-the-nuke-ndk/) | Older (VS2010 era); likely superseded by Erwan 1 |
| pending | [Sujay Reddy — Beginner's guide (Medium)](https://medium.com/@sujay_reddy/beginners-guide-to-building-a-nuke-c-plugin-2d787811c364) | Overlaps Erwan Part 1; keep only if it adds VS specifics |

## BlinkScript

| Status | Source | Why / what to mine |
| --- | --- | --- |
| pending | [Mads Hagbarth — blog / RnD](https://hagbarth.net/blog/) | Most prolific Blink performance knowledge |
| pending | [Mads Hagbarth — Point Rendering Engine intro](https://hagbarth.net/nuke-point-rendering-engine-introduction/) | Extreme Blink techniques, perf tricks |
| pending | [Erwan Leroy — 3D lightning in BlinkScript](https://erwanleroy.com/making-3d-lightning-in-nuke-using-blinkscript/) | Advanced worked example |
| pending | [Guillermo Algora — BlinkScript guide](https://guillermoalgora.com/blinkscript-guide.html) | Structured intro; check overlap with official docs |
| pending | [Adrian Pueyo — gizmos (open-source Blink kernels)](https://adrianpueyo.com/gizmos/) | apDespill/aPMatte/ColorSampler kernel sources as examples |
| pending | [lcrs/blinks — GitHub](https://github.com/lcrs/blinks) | Assorted real-world kernels as examples |

## Python

| Status | Source | Why / what to mine |
| --- | --- | --- |
| pending | [Ben McEwan — Python category](https://benmcewan.com/blog/category/nuke/python/) | Practical workflow scripts; pick posts individually |
| pending | [Nukepedia — code tutorials index](https://www.nukepedia.com/knowledge/code-tutorials/gizmos/) | Community knowledge base; mine selectively |
| pending | [Nukepedia — Getting started with Nuke plugins](https://www.nukepedia.com/knowledge/general-tutorials/getting-started-with-nuke-plugins/) | Plugin loading/installation facts |
| pending | [Alexander Richter — Enhance Nuke workflows with Python](https://www.alexanderrichtertd.com/post/mastering-python-to-enhance-nuke-workflows) | General; may be mostly known-to-model |
| pending | [Adrian Pueyo — KnobScripter](https://adrianpueyo.com/knobscripter/) | Exemplar of a polished Nuke Python tool |

## UI / PySide panels

| Status | Source | Why / what to mine |
| --- | --- | --- |
| pending | [Foundry — Custom Panels (Python dev guide)](https://learn.foundry.com/nuke/developers/140/pythonreference/custom_panels.html) | Canonical `registerWidgetAsPanel` reference |
| pending | [jedypod — dockable PySide GUI gist](https://gist.github.com/jedypod/0c2b89cf047b0bc5cebed109d707fa69) | Minimal working dock-into-Nuke pattern |
| pending | [stefanmuller/nuke_PySide_helper](https://github.com/stefanmuller/nuke_PySide_helper) | QWidgets that persist values onto nodes — non-obvious pattern |
| pending | [shiningdesign/universal_tool_template.py](https://github.com/shiningdesign/universal_tool_template.py) | Multi-DCC Qt template; PySide2/6 compat handling |
| pending | [adrianpueyo/KnobScripter](https://github.com/adrianpueyo/KnobScripter) | Heavy-UI exemplar: full script editor panel, Nuke 16/PySide6 migration in history |
| pending | [W_hotbox (melMass mirror)](https://github.com/melMass/W_hotbox) + [Nuke 16 update](https://github.com/georgeantonopoulos/W_Hotbox_Nuke16) | Wouter Gilsing's UI tool; manager UI + PySide2→6 migration diff |

## Complex tools — structure exemplars (mine for patterns, don't distill wholesale)

| Status | Source | Why / what to mine |
| --- | --- | --- |
| pending | [adrianpueyo/Stamps](https://github.com/adrianpueyo) | Smart node-connection system; mid-size, well-liked tool |
| pending | [ynput/ayon-nuke](https://github.com/ynput/ayon-nuke) | Production studio pipeline integration; package layout, hooks into Nuke lifecycle |
| pending | [PrismPipeline/Prism](https://github.com/PrismPipeline/Prism) | Open-source pipeline w/ Nuke plugin; plugin architecture |
| pending | [masqu3rad3/tik_manager4](https://github.com/masqu3rad3/tik_manager4) | Project-management platform w/ heavy Qt UI + Nuke support |
| pending | [aws-deadline/deadline-cloud-for-nuke](https://github.com/aws-deadline/deadline-cloud-for-nuke) | Officially engineered submitter: scene introspection → job template UI |
| pending | [mellowpictures/render_submission](https://github.com/mellowpictures/render_submission) | Deadline + ShotGrid submitter; real studio job-management shape |
| pending | [gillesvink/NukeDeadlineSubmission](https://github.com/gillesvink/NukeDeadlineSubmission) | Small submitter dialog; good minimal contrast to the above |
| pending | [pyblish/pyblish-nuke](https://github.com/pyblish/pyblish-nuke) | Publishing/validation framework integration pattern |
| pending | [openNuke/toolset](https://github.com/openNuke/toolset) | Tool-loader UI pulling from repo/local disk |

## Gizmo structure

| Status | Source | Why / what to mine |
| --- | --- | --- |
| pending | [Keheka — Advanced Gizmo Building in Nuke](https://www.keheka.com/advanced-gizmo-building-in-nuke/) | Dynamic menus via Python, expression-driven controls |

## Dropped (not scrapeable / video-only / paid courses)

- fxphd, Rebelway, Pluralsight, CGCircuit, ActionVFX, gatimedia — video courses, no distillable text
- Ben McEwan Python for Nuke 101 — EOL'd paid course

## Official docs (already primary sources in the design, listed for completeness)

- [NDK dev guide — Op basics](https://learn.foundry.com/nuke/developers/17.0/ndkdevguide/advanced/opscommon.html)
- [NDK dev guide — Memory management](https://learn.foundry.com/nuke/developers/17.0/ndkdevguide/advanced/memorymanagement.html)
- [NDK dev guide — Deep ops](https://learn.foundry.com/nuke/developers/17.0/ndkdevguide/deep/deep.html)
- Blink Kernel API Reference, Blink User Guide, Python dev guide + reference (versioned learn.foundry.com URLs)
