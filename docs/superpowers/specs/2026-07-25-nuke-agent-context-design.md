# nuke-agent-context — design

**Date:** 2026-07-25
**Status:** draft for review
**Supersedes:** `nuke-agent-toolkit` (kept locally as the port source; never pushed)

## Goal

A lean, shareable Claude Code plugin that makes agents good at Nuke tool
development across all three layers — Python, NDK (C++), BlinkScript — by
grounding them in version-pinned API facts, practitioner knowledge, and
performance principles. Install is `/plugin install`; nothing is generated,
executed, or hooked on the user's machine.

Three goals, unchanged from the original project:

1. **API grounding** — the agent never writes a Nuke API it hasn't looked up,
   for all three languages, without depending on Context7 or any paid service.
2. **Performance principles** — scanline/planar model, threading contract,
   memory discipline available to the agent while it designs, not after.
3. **SE quality** — tools structured like software (pure core, thin shell,
   testable), not just working scripts.

## What changed from nuke-agent-toolkit

| | toolkit (old) | context (new) |
| --- | --- | --- |
| API index | generated on user's machine from installed headers/docs | **pre-built, committed to repo**, per Nuke version, with public doc URLs |
| Enforcement | 4 shell hooks (guard, test-first, test protection, post-edit runner) | **none** — guidance in skills; Claude Code's own permissions suffice |
| Setup | `/nuke-agent:setup` scaffolds CMake project + CLAUDE.md + tests | **none** — plugin is inert content; no setup command |
| Trust surface | executes project-supplied `test-cmd`; needed a disclosure section | **zero execution**; nothing to disclose |
| SE process | TDD enforced by hooks | guidance in `nuke-tool-structure`; Superpowers-style skills do process |
| Extractors | run at setup by installers | maintainer-only, in `tools/`; installers never run them |

The eval result that justifies the grounding approach (2.1× compile rate,
−70% invented APIs, `evals/FINDINGS.md` in the old repo) carries over as the
motivating evidence; the eval harness itself ports in a later phase.

## Repo layout

```
nuke-agent-context/
  .claude-plugin/marketplace.json
  plugins/nuke-context/
    .claude-plugin/plugin.json
    refs/                        version-pinned official API facts (pre-built)
      VERSIONS.md                what was built from which install + docs version
      nuke-15.2/  nuke-16.1/  nuke-17.0/
        python_index.md / python_symbols.tsv / python_methods.txt
        ndk_index.md / symbol_map.tsv
        blink_index.md / blink_symbols.tsv
        devguide_index.md / devguide_map.tsv      (54-page NDK guide map, concept anchors)
        pyguide_index.md / pyguide_map.tsv
        blinkguide_index.md / blinkguide_map.tsv
    references/                  community field guides (reference-only tier: verify before use)
      README.md  ndk.md  blink.md  python.md  pyside-panels.md  tool-architecture.md
    skills/
      nuke-api-lookup/           the core rule + three-tier lookup (below)
      nuke-python-model/         mental model: nodes/knobs/callbacks, GUI vs terminal
      nuke-ndk-model/            mental model: Op lifecycle, validate/request/engine
      nuke-blink-model/          kernel model: granularity, access, edge handling
      nuke-performance/          NEW — distilled from dev-guide advanced chapters
      nuke-tool-structure/       SE quality; absorbs nuke-tdd as guidance
    examples/
      python/  blink/ (incl. bookofshaders/)  ndk/
      INDEX.md                   one line per example: concept + APIs exercised
    docs/
      git-github-setup.md        install git + gh, GitHub account, auth, first push
                                 (shipped in the plugin so the agent can walk a
                                 TA through it interactively; linked from README)
  tools/                         maintainer-only; not part of the plugin
    nuke_detect.py
    extract_python_api.py  extract_ndk_index.py  extract_blink_api.py
    extract_examples_index.py
  docs/superpowers/specs/        this file
  SOURCES.md                     curation tracker (distilled → references/)
  tests/                         manifest/skill/example validation (ported)
  evals/                         later phase: port ablation harness
```

Dropped entirely: `hooks/`, `commands/setup.md`, CMake template generation
(a commented `CMakeLists.txt` lives in `examples/ndk/` as a file instead),
`.nuke-agent/` project marker.

## Grounding: how lookup works

Two trust tiers, explicit everywhere:

- **`refs/` — official, version-pinned.** Symbol exists ⟺ it's in the index
  for your Nuke version. Signatures and doc URLs included.
- **`references/` — community, unversioned, reference-only.** Practitioner
  orientation with cited sources. **Never a basis for writing code directly:
  any claim from this tier that is about to influence code must first be
  verified against the official tier** — the refs index, the versioned Foundry
  page, the real header, or a compile/`nuke -t` check — because community
  knowledge is frequently legacy (PySide2-era patterns, version-specific build
  flags, workarounds Foundry has since fixed). Verified-then-used, never
  believed. When it conflicts with refs/headers, official wins; when it can't
  be verified, it is presented to the user as unverified community practice,
  not applied silently.

The `nuke-api-lookup` skill's three-tier rule for a symbol's exact signature:

1. **Doc URL in the index** → WebFetch the versioned learn.foundry.com page.
2. **No URL, Nuke installed locally** → read the real header
   (`Documentation/NDKExamples/include/DDImage/`).
3. **Neither** → the symbol exists (it's in the index) but its signature is
   unverified; write it, then let the compiler confirm. Never invent an
   alternative that isn't in the index.

Rationale (verified 2026-07-25): after the URL fixes below, ~64% of DDImage
symbols have public doc pages; ~36% are genuinely undocumented. Foundry's
doxygen also documents *stale* API that no longer exists in the headers
(`GenericImagePlane`, `BaseHandle` in 17.0), so the hierarchy is:
index routes → docs explain → headers/compiler are ground truth.

Python (6,116 symbols) and Blink (self-contained index with inline signatures)
have no URL gap.

## Known defects to fix during the port (verified against live site)

1. **`doc_url()` misses struct pages.** Doxygen emits
   `structDD_1_1Image_1_1<Name>.html` for structs; extractor only tries
   `class` form. (28 symbols affected.)
2. **`doc_url()` doesn't escape underscores.** Doxygen doubles them:
   `MultiArray_KnobI` → `MultiArray__KnobI.html`. (Overlapping set; both
   fixes together recover 47 symbols: 278 → 325 of 511.)
3. **Header parser gaps:** misses template classes (`RefCountedPtr` in
   `RefCountedObject.h`), `rTriangle` (`rTriangle.h`), nested `Knob::cstring`.
   Investigate parser; fix or document as known limits.
4. After fixes, **regenerate all three version dirs** before first publish.

## Skills

Six skills, all content-only. Changes from the toolkit versions:

- **nuke-api-lookup** — rewrite the NDK section for the three-tier rule and
  in-plugin refs paths (`refs/nuke-<VER>/`, not `.nuke-agent/refs/`). Add
  version-selection guidance: match the user's installed Nuke (ask or detect
  via `ls /Applications | grep -i nuke` / platform equivalent); if their exact
  version has no dir, use the nearest older one and say so.
- **nuke-performance** — NEW. Distilled from the dev-guide advanced chapters
  (opscommon, memorymanagement, multithreading, planar) + community frontier
  knowledge already captured in `references/`. Principles: request only needed
  channels/bbox; engine is reentrant — no per-scanline allocation, no shared
  mutable state; declare bbox honestly; Python orchestrates, never touches
  pixels; Blink access-mode choice (point ≪ ranged ≪ random) drives GPU cost;
  hash() correctness so the cache works. Routes to devguide_map anchors for
  depth instead of duplicating Foundry prose.
- **nuke-tool-structure** — absorbs the useful half of nuke-tdd as guidance:
  pure core / thin shell, test the core headless, and the **verification
  ladder** (below) before claiming done. Also carries **version-control
  discipline**: at the start of tool work, check for a git repo; if absent,
  recommend `git init` (once, with a one-line why — tools are software,
  history is undo) and proceed respecting the user's answer. During
  development, commit at verified milestones — each time a verification rung
  passes, not on a timer — with short conventional messages. If git or `gh`
  is missing on the machine, route the user to the shipped setup guide
  (below) rather than improvising install instructions.
- **nuke-python-model / nuke-ndk-model / nuke-blink-model** — port with path
  updates and a pointer to their `references/` field guide, framed with the
  verify-before-use rule: the guide tells you *where to look*, the official
  tier tells you *what is true*.

Port note: `references/README.md` gets the same hardening — its "different
trust tier" section becomes an explicit instruction that every claim must be
verified against the official tier before it influences code, with unverifiable
claims surfaced to the user as such.

Dropped skills: `nuke-setup` (no setup), `nuke-tdd` (absorbed).

## Examples

Port all existing (python 6, blink 5 + 9 bookofshaders, ndk 8) and extend
with a complex tier targeting the eval's known weak spots and the user-priority
areas:

- **ndk/**: a minimal `Reader` subclass, a temporal/multi-frame op, a deep op
  beyond DeepGain, plus the commented `CMakeLists.txt`.
- **python/**: a full PySide6 dockable panel with per-node state persistence,
  and a small job-submitter-shaped tool (UI → introspect script → emit job)
  modeled on the exemplar repos in `references/tool-architecture.md`.
- **INDEX.md** regenerated by `tools/extract_examples_index.py`.

Every example states its verification route in a header comment (compiled
against which Nuke, or visually verified, per the old repo's convention).

## Version control & deployability

Target users are technical artists who may not have git set up. The design
treats "your tool is deployable" as part of SE quality:

- **Guidance, never enforcement.** No hooks; the agent (via
  `nuke-tool-structure`) recommends `git init` when a tool project has no
  repo, and checkpoints work with a commit each time a verification rung
  passes. The user can decline once and the agent stops asking.
- **`docs/git-github-setup.md`** ships inside the plugin: installing git
  (macOS: Xcode CLT/Homebrew; Windows: winget/Git for Windows; Linux: distro
  package), installing the `gh` CLI, creating a GitHub account, `gh auth
  login`, and the first `git init → commit → gh repo create → push` cycle.
  Because it's in the plugin directory, the agent can read it and walk the
  user through setup interactively instead of guessing at instructions.
- **README** gets a "Deploying your tools" section linking the same doc, plus
  the per-project plugin install guidance (interactive scope picker in
  `/plugin install`, `claude plugin install --scope project|local` in the CLI).

## Verification ladder

Codified in `nuke-tool-structure` and summarized in the README ("Testing your
tools"). The agent climbs as high as the environment allows and reports which
rung it reached:

1. **Static** (always available): symbol grep against `refs/`; no invented API.
2. **Headless** (Nuke installed): `nuke -t` — import the module, build the
   node, compile the Blink kernel, catch errors without the GUI. NDK: compile.
   Note license caveat: terminal mode consumes a license seat.
3. **Live session** (optional, recommended): a community **Nuke MCP server**
   (e.g. dughogan/nuke_mcp, kleer001/nuke-mcp) connected to a running Nuke —
   create the node, exec test snippets, render a frame, read real errors.
   The README recommends this for the best feedback loop, with an explicit
   trust note: these are third-party servers that execute arbitrary Python in
   your Nuke session; vet before installing. We never bundle, depend on, or
   auto-configure one; absence degrades gracefully to rungs 1–2.
4. **Human** (fallback, always the final rung): the agent hands the user a
   short manual test checklist (load path, knobs to touch, expected result,
   edge cases) instead of claiming the tool works.

## Licensing posture

Ship facts, never Foundry prose: symbol names, signatures, header/line
locations, and URLs into Foundry's own public docs. `references/` articles are
original synthesis with cited links. One pre-publish pass confirms no
description column carries verbatim doc text.

## Testing

Port from the old repo and adapt: manifest validation, skill lint
(frontmatter, paths resolve), examples compile/parse checks where possible
without a Nuke license on CI (Python: syntax + import-guard; Blink: parse
conventions; NDK: compile only locally, marked skip-on-CI). New test: every
`refs/` URL column row for a sampled subset returns 200 (network test, opt-in,
maintainer-run — not CI-blocking).

## Phases (implementation order)

1. **Port the spine** — repo scaffolding, marketplace/plugin manifests, copy
   refs + references + examples + tools, adapt tests. Plugin installable.
2. **Fix extractors, regenerate refs** — defects 1–4 above; VERSIONS.md.
3. **Skills** — port four, write nuke-performance, rework api-lookup.
4. **Examples: complex tier** — Reader/temporal/deep NDK, PySide panel,
   submitter-shaped tool.
5. **Evals (optional, later)** — port harness; re-run ablation to confirm the
   leaner design still holds the 2.1× result; numbers feed the README.
   The ported harness **captures per-run cost and token usage** (headless
   `--output-format json` exposes `total_cost_usd` and token counts; the old
   harness discarded them), so the context-overhead question is answered with
   a measured column next to compile rate, not an estimate.

## Open decisions

- **Plugin name:** `nuke-context` (repo `nuke-agent-context`). Old name
  `nuke-agent` would collide for anyone who installed the toolkit.
- Whether refs for 17.0v1-Beta stay maintainer-local (default: yes, don't ship
  beta indexes).
