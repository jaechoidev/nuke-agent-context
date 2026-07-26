---
name: nuke-tool-structure
description: The mental model for Nuke tool development and how it differs from normal coding - the pull-based per-scanline evaluation model, the Op contract, thin-shell/pure-core structure, test-first workflow, the verification ladder, and version control. Use when designing, planning, or writing any Nuke tool, Op, kernel, gizmo, panel, or callback - read this before writing code.
---

# How Nuke tool development is different

Writing a Nuke tool is not writing an application. The instinct from normal coding — drive a
loop, hold state, call the library — produces tools that are slow, that corrupt renders under
load, or that never fire. The paradigm is different in four ways, and getting them wrong is
what separates a working Nuke tool from code that merely compiles.

## 1. The framework calls you, not the other way around

Nuke is a **lazy, pull-based, per-scanline, multithreaded DAG over 32-bit float image data.**
Nothing computes until something downstream pulls it. When a viewer or write needs a frame,
Nuke walks *up* the tree asking each Op what it needs, then walks *down* filling pixels — one
scanline at a time, on many threads at once.

You do not write the loop over pixels-and-frames. You implement small methods that Nuke calls,
possibly thousands of times, concurrently, in an order you do not control. Design for that:
- **You will be called per scanline, out of order, on parallel threads.**
- **Each frame is independent.** No "previous frame" state survives unless you explicitly ask
  for another frame's data.
- **Do the least work that answers the pull.** Requesting or touching more of the image than
  you need makes the whole downstream tree slower (see `nuke-performance`).

## 2. The Op contract splits three things normal code would merge

A normal class computes a result in one place. A Nuke Op separates *declaring its output
shape* from *declaring what input it will pull* from *producing pixels* — three distinct
methods Nuke calls at different times. Mixing them is the most common structural error.

| Method | Its one job | Never |
| --- | --- | --- |
| `_validate()` | Declare output metadata: format, bounding box, channels | Touch pixels |
| `_request()` | Declare which input channels and image area you will pull | Touch pixels |
| `engine()` / `pixel_engine()` | Produce pixels for one scanline | Mutate member state |
| `knobs()` | Declare the knob (control) interface | Compute anything |
| `knob_changed()` | React to a user changing a knob | Do pixel work |

## 3. Thread-safety is a rule of the paradigm, not an optimization

`engine()`/`pixel_engine()` run concurrently on many threads, each on a different scanline. It
**must be reentrant**: no mutable member state, no lazy caching into `this`, no shared scratch
buffer. A member written from `engine()` is the classic Nuke bug — it passes single-threaded
testing and corrupts output intermittently under a real render, usually only on long ones.

Anything expensive and shared belongs in `_validate()` (computed once) or a proper cache class
(hold an `Interest`) — read `SimpleBlurCached.cpp` for the pattern.

## 4. Thin shell, pure core

Because the shell (`engine()`, a knob callback, a panel handler) needs a live Nuke to run, it
is not unit-testable. So put almost nothing in it.

```
src/core/    algorithm and maths. No DDImage include, no `import nuke`.
             Testable in milliseconds with plain pytest / ctest.
src/ops/     the Op / kernel / panel shell. Reads knobs, calls core, writes out.
             Verified at the Nuke boundary (ladder below).
```

Keep the core importable/compilable with no Nuke on the machine — then a leak of `nuke` or
DDImage into the core is caught the moment the unit tests run. **If a bug reproduces without
Nuke running, it belongs in the core.**

## Test-first, and tests that can actually fail

1. Write the failing test first; run it and confirm it fails **for the reason you expect** —
   a test that passes immediately is testing nothing.
2. Implement the minimum that passes; run; commit.
3. The cheap defence against decorative tests is mutation: break the thing the test guards
   and watch it go red. Specifically: a test that iterates a collection asserts non-empty
   first; a test reading a subprocess's output asserts the exit code too; never verify an
   implementation against a copy of its own logic.
4. When a test fails, fix the implementation. **Never edit the test to match the output** —
   that converts a caught bug into a documented one. A genuinely wrong test changes in its
   own deliberate commit, visible in review.

Pixel tests: float output is not bit-exact (multithreading + compiler reordering) — compare
within a stated tolerance, and prefer gradients with hard edges over constant colours, which
prove almost nothing.

## The verification ladder

"Done" means *verified to a rung*, and you always **report which rung you reached**:

1. **Static** (always available): every API symbol grepped against
   `${CLAUDE_PLUGIN_ROOT}/refs/nuke-<VER>/` — no invented API (`nuke-api-lookup`).
2. **Headless** (Nuke installed): `nuke -t` — import the module, build the node, compile the
   Blink kernel, run the golden test, catch errors without the GUI. For the NDK: it compiles.
   Note: terminal mode consumes a license seat.
3. **Live session** (optional, best feedback): if the user has a community **Nuke MCP
   server** connected to a running Nuke, use it — create the node, run test snippets, render
   a frame, read the real error. These are third-party servers executing arbitrary Python in
   the user's Nuke: recommend, never install or configure one yourself, and degrade to rungs
   1–2 without it.
4. **Human** (always the final rung when 2–3 are unavailable): hand the user a short manual
   test checklist — the file to load or menu to click, the knobs to touch, the expected
   result, the edge cases to try — instead of claiming the tool works.

## Version control

Tools are software; history is undo. At the start of tool work, check for a repo
(`git rev-parse --git-dir`). If there is none, recommend `git init` once — one line on why —
and respect a decline without asking again. Commit at **verified milestones**: each time a
ladder rung passes, with a short conventional message. If `git` or `gh` is missing, or the
user wants their tool shareable, walk them through
`${CLAUDE_PLUGIN_ROOT}/docs/git-github-setup.md` step by step rather than improvising.

## Choosing a layer

All three are first-class. Choose by what the tool needs, then read the matching model skill.

| Need | Layer | Model skill |
| --- | --- | --- |
| Node-graph manipulation, UI, batch, pipeline glue | Python | `nuke-python-model` |
| Per-pixel maths that suits the GPU, fast iteration, no build | BlinkScript | `nuke-blink-model` |
| Custom bbox/channel behaviour, file I/O, deep, 3D, full control | NDK (C++) | `nuke-ndk-model` |

Prototyping in BlinkScript then porting to the NDK is a reasonable path — the pure core
transfers directly, since it never depended on either.

## Before you write

1. Name the layer and the base class (see the model skill for that layer).
2. Read the canonical example that already demonstrates your pattern — the worked-examples
   table in `nuke-api-lookup` maps tasks to Foundry files; this plugin's own are under
   `${CLAUDE_PLUGIN_ROOT}/examples/`. Read the real file; do not invent structure.
3. Unsure of the paradigm itself (how caching/hashing/threading/deep/3D actually work)? The
   NDK Developer Guide page that explains it is in `refs/nuke-<VER>/devguide_index.md` (grep
   `devguide_map.tsv` by concept). Read it rather than reasoning from first principles.
4. Confirm any exact API signature you are unsure of — `nuke-api-lookup`.
5. Structuring a larger tool or pipeline (submitter, panel, publish/validate, gizmo library)?
   `${CLAUDE_PLUGIN_ROOT}/references/` holds short "practitioner landscape" field guides per
   layer plus `tool-architecture.md` (real exemplar repos, small → large). Community sources:
   verify any claim against the official tier before it shapes code.
6. Non-destructive by default: never overwrite a `.nk`, a render, or a plate without an
   explicit backup step the user agreed to.
