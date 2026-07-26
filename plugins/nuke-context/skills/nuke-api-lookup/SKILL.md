---
name: nuke-api-lookup
description: Look up exact Nuke API signatures before writing them - DDImage classes, BlinkScript kernels, and Nuke Python. Use whenever you are about to write, call, or override any Nuke API and are not certain of the exact signature, or when a build fails with an unknown method or wrong argument error.
---

# Never write a Nuke API you have not looked up

Nuke's API is large, proprietary, and version-skewed. A signature that looks plausible is
frequently wrong, and a wrong DDImage override compiles into a plugin that silently never
gets called — no error, no node, nothing to debug.

**The rule: if you have not read the declaration in this session, look it up.**

## Where the index lives, and picking the version

The indexes ship with this plugin at `${CLAUDE_PLUGIN_ROOT}/refs/nuke-<VER>/`
(`nuke-15.2`, `nuke-16.1`, `nuke-17.0` — see `refs/VERSIONS.md` for provenance). Always
present; no setup, no Nuke install required.

Pin one version dir per project, matching the user's Nuke:

- Detect installs (`ls /Applications | grep -i nuke` on macOS; `C:\Program Files\` on
  Windows; `/usr/local/` on Linux) or ask the user once.
- If their exact version has no dir, use the **nearest older** baseline and say so —
  a newer API surface must never be assumed on an older Nuke.

These files are large (`python_index.md` is over a megabyte). **Grep them; never read one
whole** — a full read wastes the entire context window on rows you don't need.

## NDK / DDImage — the three-tier rule

First, find the symbol:

```bash
grep -i "<Symbol>" ${CLAUDE_PLUGIN_ROOT}/refs/nuke-<VER>/symbol_map.tsv
```

Do **not** anchor the pattern to the start of the line. Nested classes are recorded under
their qualified name, so `Description` appears as `Op::Description`, `Reader::Description`,
`DeepReader::Description` and a dozen more. An anchored search finds none of them. That
distinction matters: every NDK plugin registers itself with
`static const Op::Description description;` — and `Reader::Description` is a different type
with a different constructor. Picking the wrong one produces code that looks right and does
not work.

For a concept rather than a name, scan `ndk_index.md` (one row per class) or grep
`devguide_map.tsv` for the guide page that explains the paradigm.

Then get the exact signature — three tiers, in order:

1. **The row has a Docs URL** → WebFetch that versioned `learn.foundry.com` page for the
   declaration and prose. Trust it for semantics, but remember tier 2 outranks it.
2. **No URL, or you need certainty** → read the real header if a local Nuke exists:
   `<install>/Documentation/NDKExamples/include/DDImage/<Header>.h` at the recorded line.
   The header is the only full authority — about 37% of DDImage has no public doc page,
   and Foundry's doxygen also documents API that **no longer exists in the headers**
   (`GenericImagePlane` in 17.0). Docs explain; headers decide.
3. **Neither is available** → the symbol still exists (it is in the index): write the call
   from the index's name and location, state that the signature is unverified, and let the
   compiler confirm — it names a wrong member outright.

Entries marked `(N variants)` are declared more than once, usually behind
`#if !defined(_WIN32)`. Same class, platform-specific implementation.

## Worked examples

Foundry ships ~108 example plugins that compile, at
`<install>/Documentation/NDKExamples/examples/`. Read one before inventing a pattern.

| Task | Example |
| --- | --- |
| Per-pixel operation | `Add.cpp`, `Saturation.cpp` |
| Spatial filter needing neighbouring pixels | `SimpleBlur.cpp`, `Convolve.cpp` |
| Caching across scanlines | `SimpleBlurCached.cpp` |
| Channel manipulation | `AddChannels.cpp`, `ChannelSelector.cpp` |
| Every knob type | `KnobParade.cpp` |
| Knobs created at runtime | `DynamicKnobs.cpp` |
| Temporal / multi-frame access | `TemporalMedian.cpp` |
| Deep data | `DeepRead.cpp`, `DeepCrop.cpp` |
| File reader / writer | `exrReader.cpp`, `dpxWriter.cpp` |
| 3D geometry | `GeoTriangle.cpp`, `GeoTwist.cpp` |
| Viewer handles | `Handle.cpp`, `Draw2D.cpp` |
| GPU / Blink from within the NDK | `GPUFileShader.cpp` |

This plugin's own compile-verified examples: `${CLAUDE_PLUGIN_ROOT}/examples/ndk/`.

## BlinkScript

Blink is small enough to hold in full: `blink_index.md` lists every built-in, type and
keyword (70 entries) with inline signatures, each linking to the one reference page.
Anything you call that is not listed — and not a `param`/`local`/`Image` you declared —
will not compile in Nuke. Confirm kernel granularity, access pattern, and image spec before
writing — those are the parts that fail silently rather than erroring.

## Nuke Python

Three sources, cheapest first:

1. **The index** — `python_index.md` / `python_symbols.tsv` (6000+ symbols with call-form
   signatures and a Docs URL per row). Grep to confirm a symbol exists. A method absent
   here should not be written.
2. **The guide** — grep `pyguide_map.tsv` for the concept, WebFetch the page for how-to
   prose. (If a Context7 MCP connection is available it also indexes the Python guide;
   optional, never required.)
3. **Introspection** — cannot be stale, needs a Nuke binary:

```bash
<NUKE_BINARY> -t -c "import nuke; help(nuke.Node.knob)"
```

(NDK and Blink are not on Context7 — the index, the Docs URL, or the real header are the
sources.)

## When the lookup fails

If a symbol is not in the index and not in the headers, **it does not exist in this Nuke
version**. Say so. Do not substitute something similar-sounding. Check whether it was added
in a later release and tell the user which one — a compositor pinned to 15.2 needs to know
that the answer is "upgrade", not "here is code that will not compile".
