---
name: nuke-blink-model
description: The BlinkScript mental model for Nuke - the kernel/GPU per-pixel paradigm, access patterns (point/ranged/random), param/local/define/init/process, and image specs. Use when writing or designing a BlinkScript kernel, after nuke-tool-structure sets the overall paradigm.
---

# The BlinkScript model

Read `nuke-tool-structure` first for the paradigm. This is the Blink specifics.

A Blink kernel runs once per output pixel, compiled to CPU or GPU. You do not write a loop
over pixels — you write `process()`, which Blink calls for every pixel, massively in parallel.
The same reentrancy rule as the NDK applies and is even stricter: **no per-pixel state you
write and read back** — each invocation is independent.

## Kernel skeleton

```cpp
kernel MyKernel : public ImageComputationKernel<ePixelWise>
{
  Image<eRead, eAccessPoint> src;      // how you read the input
  Image<eWrite, eAccessPoint> dst;     // how you write the output

param:
  float amount;                        // knobs, set from Nuke

local:
  float derived;                       // per-kernel scratch, set in init()

  void define() { defineParam(amount, "Amount", 1.0f); }
  void init()   { derived = amount * 2.0f; }      // runs once, not per pixel
  void process() {
    dst() = src() * derived;           // the per-pixel work
  }
};
```

## The choices that decide correctness

1. **Granularity** — `ImageComputationKernel<ePixelWise>` gives `process()` all components of
   a pixel at once (`src()` is a `float4`); `<eComponentWise>` runs per channel. Pick
   `ePixelWise` when channels interact (a matrix, a key), `eComponentWise` for independent
   per-channel maths.

2. **Access pattern** — how you may read `src`:
   - `eAccessPoint` — only the current pixel. Fastest. Use unless you need neighbours.
   - `eAccessRanged1D` / `eAccessRanged2D` — a fixed window; declare it with `setRange()` /
     `setAxis()` in `init()`. For blurs and filters.
   - `eAccessRandom` — arbitrary coordinates via `src(x, y)`. For warps and gathers.
   Requesting more access than you use costs performance; requesting less than you read is a
   correctness bug.

3. **`define`/`init`/`process` split** — mirrors the NDK contract: `define()` declares knobs,
   `init()` precomputes once, `process()` does per-pixel work. Never do in `process()` what
   `init()` could do once.

## Look it up, don't guess

Blink is a small fixed language. Every built-in function, type and keyword is in the index
(`${CLAUDE_PLUGIN_ROOT}/refs/nuke-<VER>/blink_index.md`) — 70 entries with inline
signatures, each linking to the reference page. If you call something not listed and not a
`param`/`local`/`Image` you declared, the kernel will not compile in Nuke. Confirm against
the index — see `nuke-api-lookup`.

## Examples to read

Original nuke-context kernels: `${CLAUDE_PLUGIN_ROOT}/examples/blink/` (labelled — see each
file's header; Blink examples are API-checked, not runtime-compiled, because that needs a
licensed Nuke). Foundry's canonical kernels: `<Nuke>/Documentation/BlinkUserGuide/
ExampleKernels/`. Read one before writing.

## Practitioner field guide

For the guide itself — quick start, worked examples, library files, the kernel reference —
`refs/nuke-<VER>/blinkguide_index.md` links each page. For the practitioner landscape —
serialising a parallel kernel, bringing your own RNG, feedback via memory, Blink as AOV vector
algebra — `${CLAUDE_PLUGIN_ROOT}/references/blink.md`. Community sources: the guide tells
you *where to look*, the official tier tells you *what is true*. Verify any claim from it
against the built-in index before it shapes code; surface what you cannot verify as
unverified.
