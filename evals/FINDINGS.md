# Pass 1.5 — Eval Findings

**Date:** 2026-07-23
**Question:** Does the `nuke-agent` plugin make Claude Code better at writing Nuke NDK
plugins than vanilla Claude Code?
**Answer:** Yes, substantially — on the objective metrics the toolkit targets.

---

## Result

Two arms, identical except for the plugin. 8 cases targeting obscure NDK surface (deep ops,
scanline caching, runtime knobs, bbox declaration, 3D geo, custom readers, temporal access,
layers), 3 runs each = 24 runs per arm. Model: Sonnet. Grading is objective — the headers
say whether a symbol exists, the compiler says whether the code builds. No LLM judge.

| Metric | without plugin | with plugin | delta |
|---|---|---|---|
| **Compiles** | 9/24 (38%) | 19/24 (79%) | **+42 pts (2.1×)** |
| **Runs with zero invented APIs** | 14/24 (58%) | 18/24 (75%) | +17 pts |
| **Invented API references** | 20 | 6 | **−70%** |
| Ordinary C++ errors | 18 | 9 | −50% |
| No code produced (timeout) | 1 | 0 | — |

### Per case (compiles, of 3 runs)

| Case | without | with |
|---|---|---|
| 01 deep-crop | 2/3 | 3/3 |
| 02 cached-spatial | 2/3 | 3/3 |
| 03 dynamic-knobs | 1/3 | 3/3 |
| 04 bbox-expansion | 2/3 | 3/3 |
| 05 geo-op | 0/3 | 2/3 |
| 06 file-reader | 0/3 | 1/3 |
| 07 temporal | 1/3 | 1/3 |
| 08 channels | 1/3 | 3/3 |

The plugin is **better or equal on every case, strictly better on seven of eight.** The two
cases where both arms struggle (06 file-reader, 07 temporal) are the ones requiring the most
NDK surface area — a reader subclass and multi-frame request logic — and are the natural
targets for the Pass 2 topic skills.

### What the baseline invents

Representative fabrications from the `without` arm, none of which exist in Nuke 17.0:
`compute_normals`, `compute_UVs`, `delete_object`, `writable_primitives` on `GeometryList`;
`DeepPlane::exists`; `Input_Channel_knob`; `#include "DDImage/Lock.h"`. Every one is
plausible — the right shape, the right neighbourhood — and wrong. That is precisely the
failure mode the toolkit exists to prevent, and with the plugin the count drops by 70%.

The residual `with`-arm inventions (`Chan_DeepFront`, `Tile` used as a bare name) are
near-misses — real concepts, slightly wrong qualification — not fabrications.

---

## The result is only trustworthy because the measurement was wrong three times first

This is the more important half of the writeup. Each of the following would have produced a
confident, publishable, **false** number if reported when first seen. The toolkit's own
thesis — do not trust plausible output; verify against ground truth — applied to the eval
itself at every step.

### Bug 1 — the grader measured class names, not method calls

The first grader flagged invented **classes** via a regex over `DD::Image::X`. The dominant
real failure mode is a plausible **method on a real class** — `IopInfo::setBBox()`,
`Box::empty()` — which the regex never saw. Worse, agents write `using namespace DD::Image`,
so there were often zero qualified references to check, and a hallucination-ridden file
scored "100% clean".

**Fix:** the compiler is the authoritative oracle. It names the invented member outright
(`no member named 'setBBox'`). Errors are now classified into invented-API versus ordinary
C++ mistakes.

### Bug 2 — "no code" conflated a timeout with a permission denial

After the first fix, the `with` arm's compile rate appeared to *collapse* to 17% — below the
baseline. The counterintuitive direction was the tell. 13 of 24 `with` runs were scored "no
code produced", read as timeouts.

They were not timeouts. In headless `-p` mode, Claude Code **denies file reads outside the
working directory by default**, and the Nuke headers live under `/Applications`. So the
`with` arm invoked the lookup skill, was denied the header read, and either guessed from
memory or stalled asking for permission. Its index — symlinked into the project — stayed
readable, which is exactly why invented-API still improved while compile rate cratered: the
agent got class *names* right and method *signatures* wrong.

The agent told us itself, in its output: *"Want me to try again in a mode where header access
is permitted?"*

**Fix:** run both arms with `--permission-mode bypassPermissions` (safe — every run is a
throwaway temp dir and the grader never executes the code). The plugin is now the only
difference between arms. Verified on one case: identical prompt, add the flag, and the run
goes from "no code" to compiles / zero invented / all includes valid.

### Bug 3 — the confound was invisible until the numbers refused to reconcile

The invalid run reported `with` = 4/24 compiled, but also only 1 invented API and 1 other C++
error across those runs. Those cannot both be true: 24 − 4 = 20 failures need a cause. The
arithmetic not closing is what forced the per-case dig that found Bug 2. A summary that
doesn't reconcile against its own detail is a defect, not a rounding artifact.

**Lesson carried forward:** the harness now prints `compiled + built-but-failed + no-code`
and asserts it equals the run count, so a gap can't hide again.

---

## Caveats, stated plainly

- **n=3 per case, one model (Sonnet), one platform (macOS/arm64), 8 cases.** This is a
  directional result, not a benchmark. The effect is large enough (2.1× compile rate) to
  trust the direction; the exact magnitude will move.
- **The comparison is end-to-end**, not plugin-only. The `with` arm has the plugin *and* a
  set-up project (CLAUDE.md, a generated index). That is deliberate — the setup is part of
  what the toolkit delivers — but it means the number credits the whole package, not the
  grounding mechanism in isolation.
- **`bypassPermissions` is not how a real session runs.** A real user grants header reads
  interactively. The flag reproduces "the agent is allowed to read the headers", which is the
  realistic state; it is not measuring a permission-free fantasy.
- **Grading is objective but narrow.** "Compiles" and "no invented API" are necessary, not
  sufficient — they do not check that the node is *correct*, only that it is real and builds.
  Correctness would need golden-image tests, which is a Pass 2+ concern.

---

## Reproduce

```bash
python3 evals/run_ablation.py --runs 3 --model sonnet --timeout 900 \
  --out evals/results/full-3x.json
```

Raw results: `evals/results/full-3x.json`. The invalid (pre-permission-fix) run is preserved
at `evals/results/full-3x-INVALID-default-perms.json` for the record.
