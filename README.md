# nuke-agent-context

> **⚠️ Archived — negative result.** This plugin was built on a real, measured
> effect and then killed by a better measurement. A controlled follow-up
> benchmark (418 graded runs, 2×2 factorial, paired statistics, live licensed
> Nuke 17) found its effect on task success **indistinguishable from zero** on
> current frontier models: +2.9 points overall (CI spans zero, McNemar
> p = 0.50), at 2.5× the tokens. The one surviving signal — a +14.8-point NDK
> compile effect — is erased by simply letting the agent compile and test its
> own work, and did not reproduce on a Sonnet-class model at all. Current
> models no longer meaningfully fabricate Nuke APIs (1 invented reference in
> 418 runs), which was the failure mode this plugin existed to prevent.
> **Full write-up: [Does grounding still pay?](https://jaechoidev.github.io/posts/2026/07/nuke-context-benchmark/)**
>
> The repo stays up as a record of the approach. Still potentially useful:
> the `tools/` extractors (version-pinned API indexes from a local Nuke
> install), the refs/verification-ladder design, and the eval methodology.
> The plugin is unmaintained; it still installs if you want to study it, but
> the measured advice is: give your agent a way to compile and run instead.

A Claude Code plugin (`nuke-context`) that makes AI agents good at Nuke tool
development — Python, BlinkScript, and the NDK (C++).

Install it, then prompt as usual. The plugin changes how the agent works, not
how you work: before writing any Nuke API it looks the symbol up in a
version-pinned index, reads the real documentation or header for the exact
signature, applies Nuke's performance model while designing, verifies the
result against the strongest oracle available, and reports how far up that
ladder it got. Nothing runs at install time — the plugin is pure content: no
hooks, no setup step, nothing executable.

The original evidence that motivated it: in an 8-case ablation against the
NDK's hardest surface (deep ops, readers, temporal access), grounding lifted
the compile rate **2.1×** (38% → 79%) and cut invented API references by
**70%** on a Sonnet-class model of the time. That harness lives in `evals/`;
the follow-up study that overturned it is linked in the banner above.

## Install

Personal (interactive scope picker — choose **User** for everywhere, or
**Project**/**Local** to activate only in your Nuke tools repo):

```
/plugin marketplace add jaechoidev/nuke-agent-context
/plugin install nuke-context@nuke-agent-context
```

Scriptable equivalent:

```bash
claude plugin install nuke-context@nuke-agent-context --scope project   # or user / local
```

Team (commit to your tools repo's `.claude/settings.json`; collaborators are
prompted to trust and install on first open):

```json
{
  "extraKnownMarketplaces": {
    "nuke-agent-context": {
      "source": { "source": "github", "repo": "jaechoidev/nuke-agent-context" }
    }
  },
  "enabledPlugins": {
    "nuke-context@nuke-agent-context": true
  }
}
```

Idle cost when enabled globally is a few hundred tokens of skill descriptions;
the content only loads when a task touches Nuke.

## What's inside

| Layer | What | Trust tier |
| --- | --- | --- |
| `refs/nuke-{15.2,16.1,17.0}/` | Pre-built API indexes: 6,116 Python symbols, 523 DDImage classes, the full Blink language, concept→page maps for every Foundry guide — each row linking to the versioned `learn.foundry.com` page | **Official.** Version-pinned facts; provenance in `refs/VERSIONS.md` |
| `references/` | Community field guides per layer (NDK, Blink, Python, PySide panels, tool architecture), distilled from practitioner blogs and exemplar repos, cited per claim | **Reference-only.** Verified against the official tier before use — never believed |
| `skills/` | Six skills: api-lookup (the never-write-unlooked-up rule), three per-layer mental models, performance principles, tool structure + verification | Behaviour |
| `examples/` | Working examples across all three layers, each labelled with what it teaches and how it was verified (NDK ones compile against a real Nuke) | Teaching material |

How grounding works: symbol existence is answered offline by grepping the
index; exact signatures come from the versioned doc URL (WebFetch), the real
local header, or — when neither exists — the compiler's verdict. Headers
outrank docs: Foundry's doxygen carries stale pages for API that no longer
ships, so nothing below the compiler is fully trusted, and community claims
verify against official sources before they shape code.

## Testing your tools

The agent climbs a four-rung verification ladder and tells you which rung it
reached:

1. **Static** — every API symbol checked against the index; no invented API.
2. **Headless** — `nuke -t`: import, build the node, compile the kernel (uses
   a license seat).
3. **Live session** *(optional, recommended)* — a community Nuke MCP server
   (e.g. `dughogan/nuke_mcp`, `kleer001/nuke-mcp`) connected to a running
   Nuke lets the agent create nodes, render, and read real errors. **Trust
   note:** these are third-party servers that execute arbitrary Python inside
   your Nuke session — vet one before installing it. This plugin never
   bundles, depends on, or configures one.
4. **Human checklist** — when the rungs above aren't available, you get a
   concrete manual test list instead of a "works!" claim.

## Permissions to expect

Claude Code will ask before the plugin's lookups touch anything outside the
project: reading Nuke's headers under `/Applications` (or your install path),
fetching `learn.foundry.com` doc pages, and running `nuke -t`. Allow these —
they are exactly how the plugin keeps the agent honest. Deny them and the
agent falls back to weaker rungs and says so.

## Deploying your tools

Your tools deserve version control and a home. The agent recommends `git init`
in new tool projects, commits at verified milestones, and can walk you through
the full setup — installing git and the GitHub CLI, creating an account, and
your first push — using
[`plugins/nuke-context/docs/git-github-setup.md`](plugins/nuke-context/docs/git-github-setup.md).

## Updating for a new Nuke version

Maintainers regenerate the indexes from a local install with the extractors in
`tools/` (installers never run them):

```bash
python3 tools/extract_ndk_index.py "<install>/Documentation/NDKExamples/include/DDImage" \
  --out plugins/nuke-context/refs/nuke-<VER> \
  --doc-base "https://learn.foundry.com/nuke/developers/<VER>/ndkreference/Plugins" \
  --doxygen "<install>/Documentation/NDKExamples/Plugins"
```

## License and content

MIT. The plugin ships **no Foundry content**: indexes carry only derived facts
(names, signatures, locations, public URLs); the field guides are original
synthesis with citations. Foundry documentation is read from your disk or
their public site, where it belongs.
