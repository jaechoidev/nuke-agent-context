---
name: nuke-performance
description: Nuke tool performance principles - choosing Python vs BlinkScript vs NDK by granularity, the scanline request/engine discipline, bbox and channel hygiene, hashing/caching correctness, and Blink GPU cost. Use when designing any Nuke tool, when choosing which layer to build in, when a tool or script is slow, or when writing NDK _request/engine or Blink kernels.
---

# Nuke performance principles

Nuke is a lazy, pull-based, scanline-oriented engine with an aggressive cache.
Every principle below is a consequence of that sentence. Depth lives in the NDK
Developer Guide — grep `${CLAUDE_PLUGIN_ROOT}/refs/nuke-<VER>/devguide_map.tsv`
for the page anchor (concepts: `Memory Management`, `Op Hashing & Caching`,
`Architecture`, the Planar Iop chapter) and read the linked Foundry page rather
than reasoning from memory.

## 1. Choose the layer by granularity

- **Python orchestrates the DAG; it never touches pixels.** Building node
  graphs, wiring knobs, callbacks, panels: Python. Anything per-pixel in a
  Python loop is thousands of times too slow — reach for Blink or the NDK the
  moment the work is per-pixel.
- **BlinkScript** for per-pixel and neighbourhood math — it compiles to
  SIMD/GPU and parallelises for free.
- **NDK** for structural ops: new node types, deep data, readers/writers, 3D,
  anything needing the full Op contract.

The decision test: *what is the smallest unit of work?* Node → Python.
Pixel → Blink. Op/format/graph machinery → NDK.

## 2. The scanline contract (NDK)

- **Request only what you read.** `_request()` declares the input region and
  channels you will pull. Over-requesting inflates upstream work and memory;
  a filter that reads outside its output bbox must request that margin
  explicitly or it reads garbage.
- **Declare only what you produce.** `_validate()` sets the output bbox,
  channels, and format via `info_`. An oversized bbox makes every downstream
  node process pixels you never made; missing channels break the pull.
- **`engine()` runs on many threads, one scanline each.** It must be reentrant: no
  member writes, no lazy caches on `this`, no allocation per scanline —
  precompute in `_validate()`, read-only in `engine()`. A data race here is
  wrong pixels under load, not a crash. (Threading beyond the engine —
  spawning your own work — is `Memory Management` / `Architecture` guide
  territory; Nuke's substrate is TBB.)
- **Hashing is cache identity.** `append(Hash&)` must fold in every input
  that changes the output — miss one and Nuke serves stale cached pixels;
  fold in too much (a frame number an op doesn't use) and the cache never
  hits. See the `Op Hashing & Caching` chapter before touching `hash()`.
- **Memory belongs to Nuke's budget.** Big buffers go through the DDImage
  memory system (`Memory Management` chapter), not bare `new` — Nuke can't
  evict what it doesn't know about.

## 3. Blink cost model

- **Access mode is the price tag**: `eAccessPoint` < `eAccessRanged1D/2D` <
  `eAccessRandom`. Declare the narrowest mode that covers your reads — random
  access on a GPU defeats coalescing and can be an order of magnitude slower
  than a declared range.
- `ePixelWise` when channels interact; `eComponentWise` for independent
  per-channel math (it vectorises better).
- Work that is per-kernel-launch belongs in `init()`, never `process()` —
  `process()` runs once per pixel.
- Edge handling costs: `eEdgeNone` is fastest; only pay for
  `eEdgeClamped`/`eEdgeConstant` when reads actually cross the bbox.

## 4. Python-side hygiene

- Batch graph edits inside `nuke.Undo` groups and avoid `knobChanged`
  storms — a callback that edits knobs retriggers callbacks.
- Defer UI work; never block the event loop with long computation — push it
  to `nuke.executeInMainThread` only for the UI-touching slice, not the work.

## 5. Perf claims are verified, not believed

Any performance belief — from a community source, from this file, from
intuition — follows the verify-before-use rule: **measure** before and after
(Nuke's Profile node / `nuke -t` timing a render of a fixed frame range), and
let the numbers decide. A "fast" pattern that measures slower is wrong here,
whatever the blog said.
