# The NDK (C++) — the practitioner landscape

*Community field guide. Unofficial and unversioned — orientation, not authority.
For the API use `refs/nuke-<VER>/ndk_index.md` and the dev-guide map
(`devguide_index.md`); the paradigm lives in the `nuke-ndk-model` skill. Verify
anything here against those and the real headers.*

Foundry's docs cover the plain Op skeleton well (subclass `Iop`, a `static
Description` to register, the `_validate`/`_request`/`engine` signatures). What
they bury or omit — and what every beginner tutorial re-derives — is the
*practitioner folklore*: the build matrix, the threading contract, and the
barely-documented knob/GL surface. That folklore is what this guide points you at.

## The backbone: Erwan Leroy's NDK series

[Erwan Leroy's 5-part series](https://erwanleroy.com/intro-to-writing-nuke-c-plugins-a-k-a-the-ndk-part-1-intro-compiling/)
(2023–2024, Nuke 14/15) is the only current, actively-maintained, end-to-end path,
and it uniquely covers the hard surfaces the older tutorials skip. Read it first.

**[Part 1 — compiling](https://erwanleroy.com/intro-to-writing-nuke-c-plugins-a-k-a-the-ndk-part-1-intro-compiling/)**
is the build reference, and the build is where a strong C++ dev loses the most
time. Non-obvious facts it pins down:
- You recompile per **minor** Nuke version (14.0 → 14.1), not just per major, and
  drop the plugin in a version-specific dir (`~/.nuke/14.0/`).
- On Linux you need the **old GCC ABI**: `-D_GLIBCXX_USE_CXX11_ABI=0` (Nuke
  14.1/15) — a flag nobody sets by default. Specific GCC version windows apply.
- On Windows the VS toolset must match the Nuke build (VS2015→N12, 2017→N13,
  2019→N14/15), and Nuke 15 wants `NOMINMAX`.
- The link set is non-obvious: `DDImage`, `RIPFramework`, `glew32`, **`tbb` /
  `tbbmalloc`** (TBB is Nuke's threading substrate), `opengl32`.
- Apple Silicon on Nuke <15 must build `x86_64` and run under Rosetta.

**[Part 2 — architecture, `_validate`, knobs](https://erwanleroy.com/writing-nuke-c-plugins-a-k-a-the-ndk-part-2-architecture-the-validate-and-knobs-functions-and-first-simple-plugins/):**
the Op hierarchy (Op → Iop → NoIop/PixelIop/DrawIop/FileIop/PlanarIop); the
`static Iop::Description` (class name + menu path + build func) *is* the
registration mechanism — there's no C++ `main`/export; Nuke auto-wraps every Op
in a Node you never instantiate from C++. `_validate()` must `copy_info()` first,
then mutate channels, then call `set_out_channels()` — which is a real optimizer
signal, not cosmetic (`Mask_None` shows a red "nothing changed" indicator). The
same `knobs()` function both builds and serialises knobs (store-by-reference into
a member).

**[Part 3 — `engine` / `pixel_engine`](https://erwanleroy.com/writing-nuke-c-plugins-a-k-a-the-ndk-part-3-engine-and-pixel-engine-functions/):**
processing is **row/scanline-based** (a Row is 1px tall, full width; memory
allocated only between `x` and `r`), not per-pixel or per-tile. `in_channels()` is
decoupled from output channels (how shuffles work); `_request()` declares upstream
needs (override it for blur/gather ops that read outside their output box).
*Caveat:* this page teaches the row API but does **not** cover thread-safety — the
biggest NDK gotcha — so pair it with the threading rule below.

**[Part 4 — custom knobs, GL handles, Table_Knob](https://erwanleroy.com/writing-nuke-c-plugins-ndk-part-4-custom-knobs-gl-handles-and-the-table-knob/)**
is the only source that covers this surface in depth: custom Qt knobs need the
**MOC split** (`.moc.h` + separate Qt binaries from Foundry), they **don't**
auto-expose to Python (wire `PyTypeObject`/`setPythonType()` by hand), viewer GL
uses `build_handle`/`draw_handle` with a *static* index-dispatched `handle_cb`
callback, and `Table_Knob` is **not in the public API** (Foundry's Tracker uses a
private version). Reach here when you need in-viewer handles or bespoke UI.

**[Part 5 — the PointGradient node](https://erwanleroy.com/writing-nuke-c-plugins-ndk-part-5-the-pointgradient-node/)**
is more dev-log than tutorial, but carries one durable NDK pattern: **precompute
heavy data structures once in `_validate()`** (there, a Delaunay triangulation),
then only read them per-pixel in `engine()` — never recompute per pixel. (Also a
cautionary tale about GPL dependencies like CGAL.)

## The one rule the backbone omits — threading

The clearest statement of the threading contract is in
[Sujay Reddy's beginner guide](https://medium.com/@sujay_reddy/beginners-guide-to-building-a-nuke-c-plugin-2d787811c364)
(dated 2018/Nuke 11, thin otherwise): `_validate()` and `_request()` run on the
**main thread**; `engine()` runs on **worker threads and must be thread-safe** —
no mutable member state written from it. Order is `_validate → _request →
engine`. This is the single fact that turns a correct-looking Op into a random
crash, and it's the heart of our `nuke-ndk-model` skill.

## The rest of the map

- **Deep** — none of the tutorials touch it; the reference codebase is
  [charlesangus/DeepC](https://github.com/charlesangus/DeepC), a large suite of
  deep-compositing NDK nodes (per-sample iteration, 4D world-position+time noise)
  reported to target Nuke 16+. It also builds via a **Docker cross-build**
  (NukeDockerBuild), sidestepping the per-minor-version toolchain pain — worth
  studying as a build strategy. (Repo stats drift; check the live repo.)
- **[Max van Leeuwen's NDK tutorial](https://maxvanleeuwen.com/project/nuke-ndk/)**
  (2017/Nuke 11) is superseded by Leroy structurally, but preserves one nugget:
  the plugin name must match **identically** across C++ class, compiled filename,
  and registration or it silently fails to load; and an old `DDImage_API.h`
  version-check can be commented out to run a mismatched compiler.
- **[Vivek Reddy's getting-started](https://www.vivekc.com/getting-started-with-the-nuke-ndk/)**
  is VS2010/Nuke-7 era and **blocked automated review (HTTP 403)** — treat as
  dated and unverified; don't rely on its build steps for a modern Nuke.

## Where to start

Leroy Part 1–3 for the mainline, the threading rule above before you write
`engine()`, our `examples/ndk/` for compiling reference tools, Part 4 when you
need custom UI/handles, and DeepC when you go deep. Confirm every `DD::Image`
symbol against `ndk_index.md` and read the real header — the community sources
predate current versions.
