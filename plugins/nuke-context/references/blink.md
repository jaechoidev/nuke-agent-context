# BlinkScript — the practitioner landscape

*Community field guide. Unofficial and unversioned — orientation, not authority.
For the language itself use the shipped Blink guide and built-in index
(`refs/nuke-<VER>/blinkguide_index.md`, `blink_index.md`); verify anything here
against them.*

The community splits into two tiers, and knowing which one you're reading saves
time.

## The onboarding tier — accurate, but the official docs already cover it

Guillermo Algora's [BlinkScript guide](https://guillermoalgora.com/blinkscript-guide.html)
is the cleanest structured primer: kernel granularity (`ePixelWise` gives you all
channels of a pixel at once, `eComponentWise` runs per channel in R,G,B,A order),
the access specifiers (`eRead`/`eWrite`/`eReadWrite`), the sampling modes
(`eAccessPoint` → `eAccessRanged1D`/`2D` → `eAccessRandom`), and edge handling
(`eEdgeNone` fastest, `eEdgeClamped`, `eEdgeConstant`). It's correct and worth a
pass if the mental model hasn't clicked — but it largely restates Foundry's own
Blink guide, so treat it as a second explanation, not new knowledge. Two useful
reminders it makes concrete: **pick the narrowest access mode you can** (declaring
random access when you only need point/ranged costs real speed), and **`debugPrint()`
is your only debugger** — there is no GLSL-style tooling.

## The frontier tier — where practitioners go past the guide

This is the part worth mining, because it's *not* in the official docs.

**Deliberately defeating parallelism.** Blink is parallel-by-design: `process()`
runs per pixel with no ordering. Erwan Leroy's
[3D lightning kernel](https://erwanleroy.com/making-3d-lightning-in-nuke-using-blinkscript/)
needs the opposite — a sequential algorithm where each pixel depends on the
previous one — so it structures the kernel so only a single pixel actually
computes while every other invocation aborts early, emulating serial iteration
inside a parallel framework, and turns GPU processing *off* on purpose. If you
ever need order-dependent work in Blink, this is the pattern to study.

**Blink ships no random function.** Unlike most GLSL toolchains, there's no
built-in RNG, so the same lightning article ports a Shadertoy sine-scramble hash
for deterministic pseudo-randomness (and uses 4D Perlin noise for the branch
displacement). Expect to bring your own noise — our `bookofshaders/10_random`
and `13_fbm` example kernels show the same lesson.

**State persistence / feedback loops.** Mads Hagbarth — who spoke about Blink at
SIGGRAPH 2019 — documents a
[GPU memory-allocation trick](https://hagbarth.net/blog/) to build a Nuke feedback
loop, persisting state across iterations that stateless-per-frame kernels aren't
meant to hold. Advanced and unofficial; reach for it only when a genuine
iterative accumulation has no cleaner route. (Note: Hagbarth's
[point-rendering-engine post](https://hagbarth.net/nuke-point-rendering-engine-introduction/)
is often filed under Blink but isn't actually about it — it's motivation for
custom renderers beyond the native Scanline limits.)

## The applied-utility school — Blink as per-pixel vector algebra

A distinct group uses Blink less as a look-dev shader and more as a GPU math
engine over 3D data passes (Position, Normal, vector AOVs):

- Adrian Pueyo's [open-source gizmos](https://adrianpueyo.com/gizmos/) — *aPMatte*
  reads a Position AOV to generate mattes and world-space 4D noise; *C44Kernel*
  is a 4×4 ColorMatrix that multiplies pixels by an arbitrary matrix (transforming
  vector/normal passes); *apDespill* is a Blink despiller/keyer. Source-available,
  production-used.
- [lcrs/blinks](https://github.com/lcrs/blinks) — a set of small single-purpose
  kernels (`Ls_Cross`, `Ls_Dot`, `Ls_Reflect`, `Ls_Normalize`, `Ls_Length`,
  `Ls_Advect` vector-field advection, `Ls_PtoDepth` position→depth). The school's
  philosophy: expose one linear-algebra op per node and compose in the DAG rather
  than write one monolithic shader. Lightly documented — the value is in reading
  the kernels. `Ls_GlueP` pairing a kernel with a `.gizmo` shows the standard
  kernel-plus-wrapper distribution pattern.

## Where to start

If Blink is new, skim Algora, then read our example kernels
(`examples/blink/`) and the Book of Shaders ports. When you hit something the
guide doesn't cover — serial dependencies, custom noise, AOV math — Leroy and the
utility repos above are the frontier. Confirm every built-in you call against
`blink_index.md`; the community sources predate current versions and occasionally
use functions your Nuke lacks.
