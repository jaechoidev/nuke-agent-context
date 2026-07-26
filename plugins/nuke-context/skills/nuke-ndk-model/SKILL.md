---
name: nuke-ndk-model
description: The NDK (C++) mental model for Nuke - the DD::Image Op contract, thread-safe engine(), Interest caching, channels/bbox/format, and plugin registration. Use when writing or designing a Nuke tool in C++ / the NDK, after nuke-tool-structure sets the overall paradigm.
---

# The NDK model

Read `nuke-tool-structure` first for the paradigm. This is the C++ specifics.

An NDK plugin is a subclass of a `DD::Image` Op. **Pick the base class first** — it decides
which methods you implement and is the single biggest correctness lever. Read a shipped
`${CLAUDE_PLUGIN_ROOT}/examples/ndk/` example and the matching Foundry example (the
worked-examples table in `nuke-api-lookup` maps tasks to files under
`<install>/Documentation/NDKExamples/examples/`).

**Don't know the paradigm for a task?** `refs/nuke-<VER>/devguide_index.md` maps concepts →
the NDK Developer Guide page that explains them (grep `devguide_map.tsv` by keyword). Reach for
it before guessing — especially the *advanced* traps (`hashing`, `threading`, `caching`,
`memorymanagement`, `error`) where correct-looking code silently produces wrong pixels or
stalls. Read the linked page, don't reinvent the reasoning.

| You are building | Base class | Read (paradigm slice) |
| --- | --- | --- |
| Output pixel from the same input pixel | `PixelIop` | 2D per-pixel |
| Output needs neighbouring pixels / whole rows | `Iop` | 2D general |
| Reads several inputs per output | `Iop` (multi-input) / `MultiTileIop` | 2D multi-input |
| A source that draws (no input) | `Iop` / `DrawIop` | 2D generator |
| Metadata only, no pixel change | `NoIop` | 2D pass-through |
| Deep image data | `DeepFilterOp` | deep |
| 3D geometry | `SourceGeomOp` / `GeoOp` / `ModifyGeomOp` | 3D geometry |
| Read/write a file format | `Reader` / `Writer` (+ `…Format`) | file IO |

## The contract, concretely

Nuke calls these; you never call them yourself. Each has one job (see `nuke-tool-structure`
for the full table). In C++ terms:

```cpp
void _validate(bool for_real) override;   // set info_: format, bbox, channels. copy_info() first.
void _request(int x,int y,int r,int t, ChannelMask, int count) override;  // input().request(...)
void engine(int y,int x,int r, ChannelMask, Row& out) override;          // fill one scanline
void in_channels(int input, ChannelSet& mask) const override;            // PixelIop: channels you read
void pixel_engine(const Row& in,int y,int x,int r, ChannelMask, Row& out) override;  // PixelIop
void knobs(Knob_Callback f) override;     // declare knobs
int  knob_changed(Knob* k) override;      // react to knob edits
```

## Three things to get right every time

1. **`engine()` / `pixel_engine()` is reentrant.** Called per scanline on many threads. No
   writing to members, no lazy caches in `this`. Precompute in `_validate()` into a value you
   only read afterwards. Neighbouring-pixel access (blurs, filters) needs a cache — hold an
   `Interest` in `_validate()`/`_request()`; read `SimpleBlurCached.cpp`.

2. **`_validate()` declares the output; `_request()` declares the input pull.** Growing a
   bounding box, adding channels, or changing format happens in `_validate()` via `info_`.
   What you read from upstream is declared in `_request()`. Touching pixels in either is wrong.

3. **Registration must be exact or the node never appears:**
   ```cpp
   static Op* build(Node* node) { return new MyOp(node); }
   const Op::Description MyOp::d("MyOp", build);   // Class() returns d.name
   ```
   A wrong `Class()`/`Description` compiles and silently produces no node. Verify against a
   real example; confirm signatures with `nuke-api-lookup`.

## Channels, bbox, format — the image vocabulary

- A `ChannelSet` is which channels exist; iterate with `foreach(z, channels)`. Layers group
  channels (`rgba`, `depth`, custom AOVs). Look it up in the DDImage index
  (`${CLAUDE_PLUGIN_ROOT}/refs/nuke-<VER>/`), then read the real `ChannelSet.h`. Each index
  row's Docs URL is Foundry's doxygen page. See `nuke-api-lookup`.
- The bounding box (`info_.box()`) is the region with real pixels; outside it is black/held.
  Filters that read outside their output bbox must *request* the larger input area.
- Format is the image resolution/pixel-aspect; bbox can be larger or smaller than format.

## Examples to read

Shipped, original, compile-verified: `${CLAUDE_PLUGIN_ROOT}/examples/ndk/`. Foundry's
canonical set lives at `<install>/Documentation/NDKExamples/examples/` — read one before
writing; the structure is the hard part, not the maths.

## Practitioner field guide

For build folklore (ABI flags, per-minor recompile, the link set), the threading contract,
the custom-knob/GL surface, and where Deep code lives —
`${CLAUDE_PLUGIN_ROOT}/references/ndk.md`. Community sources: the guide tells you *where to
look*, the official tier tells you *what is true*. Verify any claim from it against the
index and the real headers before it shapes code; surface what you cannot verify as
unverified.
