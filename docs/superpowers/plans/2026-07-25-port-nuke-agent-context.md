# nuke-agent-context Port Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port nuke-agent-toolkit into a lean, zero-execution Claude Code plugin (`nuke-context`) in this repo, with corrected pre-built API refs, six content skills, community references, and expanded examples.

**Architecture:** Pure-content plugin (skills + refs + references + examples + docs) under `plugins/nuke-context/`; maintainer-only extractors in `tools/`; pytest suite in `tests/`. Two trust tiers (official `refs/`, verify-before-use `references/`) and a four-rung verification ladder, all enforced as skill guidance — no hooks, no setup command.

**Tech Stack:** Python 3.9+ stdlib only (extractors + tests via pytest), Claude Code plugin manifests, markdown/TSV content.

## Global Constraints

- Plugin name: `nuke-context`; marketplace name: `nuke-agent-context`; version `0.1.0` in both manifests (must agree).
- Source repo for ported content: `/Users/jaechoi/code/nuke-agent-toolkit` (READ-ONLY — never modify it).
- Ship **no Foundry prose**: indexes carry only names, signatures, header/line, URLs. No hooks, no commands, nothing executable in the plugin.
- Do not ship refs for beta builds (17.0v1-Beta stays out).
- Python: stdlib only, 3.9+ compatible. Tests: `python3 -m pytest tests/ -x -q` from repo root.
- Nuke installs available locally: 15.2v9, 16.1v3, 17.0v3 under `/Applications/` (17.0v1-Beta.4 exists — ignore it). Headers/doxygen live under `<install>/Documentation/NDKExamples/`.
- Commits: Conventional Commits, subject ≤72 chars, no trailers of any kind.
- Network-dependent tests must be opt-in via env var `NUKE_CONTEXT_NET_TESTS=1`, skipped otherwise.

---

### Task 1: Repo scaffolding and plugin manifests

**Files:**
- Create: `.gitignore`, `.claude-plugin/marketplace.json`, `plugins/nuke-context/.claude-plugin/plugin.json`, `LICENSE` (copy MIT from old repo, same author)
- Test: `tests/test_manifests.py`, `tests/conftest.py`

**Interfaces:**
- Produces: `tests/conftest.py` fixtures used by ALL later test tasks:
  - `repo_root` → `pathlib.Path` of repo root
  - `plugin_root` → `repo_root / "plugins" / "nuke-context"`
  - `tools_root` → `repo_root / "tools"`
  - `marketplace` → parsed dict of `.claude-plugin/marketplace.json`
  - `nuke_installs` → list of dicts `{"root": Path, "headers": Path, "doxygen": Path, "pydocs": Path}` for non-beta local installs; empty list when none (tests using it must skip when empty)

- [ ] **Step 1: Write failing manifest tests**

```python
# tests/test_manifests.py
import json, re

def test_marketplace_names_the_plugin(marketplace):
    plugins = {p["name"] for p in marketplace["plugins"]}
    assert "nuke-context" in plugins
    entry = next(p for p in marketplace["plugins"] if p["name"] == "nuke-context")
    assert entry["source"] == "./plugins/nuke-context"

def test_plugin_manifest_is_semver(plugin_root):
    m = json.loads((plugin_root / ".claude-plugin" / "plugin.json").read_text())
    assert m["name"] == "nuke-context"
    assert re.fullmatch(r"\d+\.\d+\.\d+", m["version"])

def test_manifest_versions_agree(marketplace, plugin_root):
    m = json.loads((plugin_root / ".claude-plugin" / "plugin.json").read_text())
    entry = next(p for p in marketplace["plugins"] if p["name"] == "nuke-context")
    assert entry["version"] == m["version"]

def test_no_hooks_or_commands_shipped(plugin_root):
    assert not (plugin_root / "hooks").exists()
    assert not (plugin_root / "commands").exists()
```

- [ ] **Step 2: Write `tests/conftest.py`**

Copy `~/code/nuke-agent-toolkit/tests/conftest.py` as the starting point, then adapt: `plugin_root` points at `plugins/nuke-context`; add `tools_root`; `nuke_installs` filters out any install whose directory name contains `Beta`, and derives `doxygen = root/"Documentation"/"NDKExamples"/"Plugins"`, `headers = root/"Documentation"/"NDKExamples"/"include"/"DDImage"`. Keep the old repo's detection logic (it imports `nuke_detect.py`) but load it from `tools_root`.

- [ ] **Step 3: Run tests, verify they fail** — `python3 -m pytest tests/test_manifests.py -x -q`. Expected: FAIL (missing manifests).

- [ ] **Step 4: Create the manifests**

`.claude-plugin/marketplace.json`:
```json
{
  "name": "nuke-agent-context",
  "owner": { "name": "jaechoidev" },
  "metadata": {
    "description": "Version-pinned Nuke API context and practitioner knowledge for AI-assisted tool development."
  },
  "plugins": [
    {
      "name": "nuke-context",
      "source": "./plugins/nuke-context",
      "description": "Nuke tool development context: grounded Python/NDK/BlinkScript API lookup, performance principles, verification ladder, and working examples.",
      "version": "0.1.0"
    }
  ]
}
```

`plugins/nuke-context/.claude-plugin/plugin.json`:
```json
{
  "name": "nuke-context",
  "version": "0.1.0",
  "description": "Nuke tool development context: grounded API lookup, performance principles, verification, examples.",
  "author": { "name": "jaechoidev" },
  "license": "MIT",
  "keywords": ["nuke", "vfx", "compositing", "ndk", "blinkscript", "python"]
}
```

`.gitignore`: `__pycache__/`, `*.pyc`, `.pytest_cache/`, `.DS_Store`.

- [ ] **Step 5: Run tests, verify pass** — `python3 -m pytest tests/test_manifests.py -x -q`. Expected: PASS.
- [ ] **Step 6: Commit** — `git add -A && git commit -m "feat: scaffold nuke-context plugin manifests"`

---

### Task 2: Port refs, references, and tools

**Files:**
- Create: `plugins/nuke-context/refs/nuke-{15.2,16.1,17.0}/` (copy from `~/code/nuke-agent-toolkit/plugins/nuke-agent/refs/`), `plugins/nuke-context/references/*.md` (copy), `tools/` (copy `scripts/*.py` from old plugin — `nuke_detect.py`, `extract_ndk_index.py`, `extract_python_api.py`, `extract_blink_api.py`, `extract_examples_index.py`)
- Test: `tests/test_refs_layout.py`

**Interfaces:**
- Produces: `tools/extract_ndk_index.py` exposing `doc_url(name, doc_base, doxygen_dir)` and CLI writing `ndk_index.md` + `symbol_map.tsv` (unchanged from old repo until Task 3). Refs directory layout consumed by Tasks 3–7.

- [ ] **Step 1: Write failing layout test**

```python
# tests/test_refs_layout.py
import pytest
VERSIONS = ["nuke-15.2", "nuke-16.1", "nuke-17.0"]
PER_VERSION = ["python_index.md", "python_symbols.tsv", "ndk_index.md",
               "symbol_map.tsv", "blink_index.md", "blink_symbols.tsv",
               "devguide_index.md", "devguide_map.tsv",
               "pyguide_index.md", "pyguide_map.tsv",
               "blinkguide_index.md", "blinkguide_map.tsv"]

@pytest.mark.parametrize("ver", VERSIONS)
@pytest.mark.parametrize("fname", PER_VERSION)
def test_ref_file_present_and_nonempty(plugin_root, ver, fname):
    f = plugin_root / "refs" / ver / fname
    assert f.is_file() and f.stat().st_size > 0

def test_no_beta_refs(plugin_root):
    assert not [d for d in (plugin_root / "refs").iterdir() if "Beta" in d.name or "beta" in d.name]

def test_references_guides_present(plugin_root):
    for name in ["README.md", "ndk.md", "blink.md", "python.md",
                 "pyside-panels.md", "tool-architecture.md"]:
        assert (plugin_root / "references" / name).is_file()

def test_tools_are_outside_plugin(repo_root, plugin_root):
    assert (repo_root / "tools" / "extract_ndk_index.py").is_file()
    assert not (plugin_root / "scripts").exists()
```

- [ ] **Step 2: Run, verify fail** — `python3 -m pytest tests/test_refs_layout.py -q`. Expected: FAIL.
- [ ] **Step 3: Copy content** — `cp -R` the three refs version dirs, `references/`, and the five scripts into place (no `__pycache__`). Do not copy `python_methods.txt` requirement into the test (it's an extractor by-product; copy it if present, untested).
- [ ] **Step 4: Run, verify pass** — full layout test green.
- [ ] **Step 5: Commit** — `git commit -m "feat: port refs baselines, community references, extractor tools"`

---

### Task 3: Fix `doc_url()` — struct pages and underscore escaping (TDD)

**Files:**
- Modify: `tools/extract_ndk_index.py` (the `doc_url` function shown below)
- Test: `tests/test_extract_ndk_index.py` (ported in this task from old repo, with `load()` pointed at `tools_root`)

**Interfaces:**
- Consumes: `tools/extract_ndk_index.py` from Task 2.
- Produces: `doc_url(name: str, doc_base: str, doxygen_dir: Path | None) -> str` with corrected doxygen name mangling. Task 7 regenerates refs with it.

- [ ] **Step 1: Port the extractor test file** — copy `tests/test_extract_ndk_index.py` from the old repo; change its `load()` helper to `tools_root / "extract_ndk_index.py"`; keep all synthetic-header tests. Run `python3 -m pytest tests/test_extract_ndk_index.py -q` — expected: PASS (ports cleanly before the fix).

- [ ] **Step 2: Add failing doc_url tests**

```python
def test_doc_url_escapes_underscores(plugin_root, tmp_path):
    mod = load_tools()
    (tmp_path / "classDD_1_1Image_1_1MultiArray__KnobI.html").write_text("x")
    url = mod.doc_url("MultiArray_KnobI", "https://x/Plugins", tmp_path)
    assert url == "https://x/Plugins/classDD_1_1Image_1_1MultiArray__KnobI.html"

def test_doc_url_finds_struct_pages(tmp_path):
    mod = load_tools()
    (tmp_path / "structDD_1_1Image_1_1IRange.html").write_text("x")
    assert mod.doc_url("IRange", "https://x/Plugins", tmp_path).endswith(
        "structDD_1_1Image_1_1IRange.html")

def test_doc_url_nested_and_underscored(tmp_path):
    mod = load_tools()
    (tmp_path / "structDD_1_1Image_1_1Knob_1_1Visibility__Fn.html").write_text("x")
    assert mod.doc_url("Knob::Visibility_Fn", "https://x/Plugins", tmp_path).endswith(
        "structDD_1_1Image_1_1Knob_1_1Visibility__Fn.html")

def test_doc_url_absent_page_is_empty(tmp_path):
    mod = load_tools()
    assert mod.doc_url("NoSuchThing", "https://x/Plugins", tmp_path) == ""
```

(`load_tools()` = the file's existing `load()` helper bound to `tools_root`.)

- [ ] **Step 3: Run, verify the new tests fail** (underscore + struct cases).
- [ ] **Step 4: Implement the fix**

```python
def doc_url(name: str, doc_base: str,
            doxygen_dir: pathlib.Path | None = None) -> str:
    """Public Foundry doxygen URL for a DD::Image entity, or "" if none applies.

    Doxygen mangles a page name twice: every `_` in the C++ name doubles to
    `__`, then `::` becomes `_1_1` (so `MultiArray_KnobI` ->
    `...MultiArray__KnobI.html`, `Knob::Visibility_Fn` ->
    `...Knob_1_1Visibility__Fn.html`). Classes get a `class` page and structs a
    `struct` page, so both prefixes are tried. With a local doxygen dir the URL
    is only emitted for a page that exists there -- a real link or none, never
    a guess that 404s.
    """
    mangled = name.replace("_", "__").replace("::", "_1_1")
    for form in ("class", "struct"):
        page = f"{form}DD_1_1Image_1_1{mangled}.html"
        if doxygen_dir is None:
            return f"{doc_base.rstrip('/')}/{page}"
        if (pathlib.Path(doxygen_dir) / page).is_file():
            return f"{doc_base.rstrip('/')}/{page}"
    return ""
```

- [ ] **Step 5: Run full extractor suite, verify pass** — `python3 -m pytest tests/test_extract_ndk_index.py -q`.
- [ ] **Step 6: Commit** — `git commit -m "fix(extract): doc_url handles struct pages and doxygen underscore escaping"`

---

### Task 4: Close header-parser gaps (template classes, known misses)

**Files:**
- Modify: `tools/extract_ndk_index.py` (parser)
- Test: `tests/test_extract_ndk_index.py` (extend)

**Interfaces:**
- Consumes: parser internals from Task 3's file.
- Produces: parser that indexes `template<...> class X` declarations; verified real-header coverage of `RefCountedPtr`, `rTriangle`, `Knob::cstring`.

- [ ] **Step 1: Reproduce with synthetic headers — add failing tests**

```python
TEMPLATES = {
    "RefCountedObject.h": (
        "class RefCountedObject { public: int c; };\n"
        "template<class T>\n"
        "class RefCountedPtr\n"
        "{ public: T* p; };\n"
    ),
    "rTriangle.h": (
        "class DDImage_API rTriangle : public rPrimitive\n"
        "{ public: int a; };\n"
    ),
}

def test_template_classes_are_indexed(tmp_path):
    mod = load_tools()
    write_headers(tmp_path, TEMPLATES)   # same helper the synthetic tests use
    idx = mod.build_index(tmp_path)
    assert "RefCountedPtr" in idx

def test_lowercase_prefixed_classes_are_indexed(tmp_path):
    mod = load_tools()
    write_headers(tmp_path, TEMPLATES)
    idx = mod.build_index(tmp_path)
    assert "rTriangle" in idx
```

Adapt helper names to whatever the ported test file actually uses (`build_index` may be named differently — mirror the existing tests' call pattern exactly).

- [ ] **Step 2: Run, verify which fail.** If `rTriangle` passes synthetically, the real-header miss has another cause: run the extractor against `/Applications/Nuke17.0v3/Documentation/NDKExamples/include/DDImage` and diff for `RefCountedPtr`, `rTriangle`, `Knob::cstring`; inspect the real declaration sites and add a synthetic reproduction of the actual pattern before fixing. Do not fix without a failing test that reproduces the real pattern.
- [ ] **Step 3: Fix the parser minimally** (e.g. allow an optional `template<...>` line before `class`/`struct` declarations). Keep the existing forward-declaration and doc-example guards passing.
- [ ] **Step 4: Real-header assertion test** (runs only when installs exist):

```python
def test_known_real_classes_present(plugin_root, nuke_installs):
    if not nuke_installs:
        pytest.skip("no local Nuke install")
    mod = load_tools()
    idx = mod.build_index(nuke_installs[-1]["headers"])
    for sym in ["RefCountedPtr", "rTriangle"]:
        assert sym in idx, f"{sym} missing from real-header index"
```

(`Knob::cstring` only if the investigation shows it's a parser miss rather than a deliberate exclusion — document the outcome in the test either way.)
- [ ] **Step 5: Run full suite** — `python3 -m pytest tests/ -x -q`. Expected: PASS.
- [ ] **Step 6: Commit** — `git commit -m "fix(extract): index template classes; close known parser gaps"`

---

### Task 5: Port remaining extractor/example/detect tests

**Files:**
- Create (port + adapt paths): `tests/test_nuke_detect.py`, `tests/test_extract_examples.py` (old `test_extract_examples.py`), `tests/test_examples_python.py`, `tests/test_examples_blink.py`, `tests/test_examples_compile.py`
- Create: `plugins/nuke-context/examples/` (copy `python/`, `blink/` incl. `bookofshaders/`, `ndk/`, and `INDEX.md`/generated index artifacts from the old plugin)

**Interfaces:**
- Consumes: conftest fixtures (Task 1), tools (Task 2).
- Produces: examples corpus at `plugins/nuke-context/examples/{python,blink,ndk}` that Task 10 extends. NDK compile test marked `@pytest.mark.skipif` unless a local Nuke + compiler exist (same guard the old repo used).

- [ ] **Step 1: Copy examples** from old plugin (all three dirs, no `__pycache__`).
- [ ] **Step 2: Port the five test files**; adapt `plugin_root` references (path only — assertions unchanged). Drop any test that referenced `nuke-setup` assets, `tolerance.yaml`, or golden harness (features not ported).
- [ ] **Step 3: Run** — `python3 -m pytest tests/ -x -q`. Expected: PASS (compile tests skip if toolchain absent — verify they report `skipped`, not silently pass; the old suite already asserts this pattern).
- [ ] **Step 4: Commit** — `git commit -m "feat: port examples corpus and validation tests"`

---

### Task 6: Regenerate refs with the fixed extractor + VERSIONS.md

**Files:**
- Modify: `plugins/nuke-context/refs/nuke-{15.2,16.1,17.0}/ndk_index.md`, `symbol_map.tsv` (regenerated)
- Create: `plugins/nuke-context/refs/VERSIONS.md`
- Test: `tests/test_refs_quality.py`

**Interfaces:**
- Consumes: fixed extractor (Tasks 3–4), local installs.
- Produces: corrected `symbol_map.tsv` per version (17.0 gains ≥45 URLs and the parser-gap symbols). `VERSIONS.md` documents build provenance.

- [ ] **Step 1: Write failing quality test**

```python
# tests/test_refs_quality.py
def test_17_symbol_map_url_coverage(plugin_root):
    rows = (plugin_root / "refs/nuke-17.0/symbol_map.tsv").read_text().splitlines()[1:]
    with_url = sum(1 for r in rows if r.split("\t")[3].strip())
    assert with_url >= 320, f"only {with_url} symbols carry doc URLs"

def test_17_known_fixed_symbols_have_urls(plugin_root):
    text = (plugin_root / "refs/nuke-17.0/symbol_map.tsv").read_text()
    for sym, frag in [("MultiArray_KnobI", "MultiArray__KnobI.html"),
                      ("IRange", "structDD_1_1Image_1_1IRange.html")]:
        line = next(r for r in text.splitlines() if r.startswith(sym + "\t"))
        assert frag in line

def test_versions_md_documents_every_shipped_dir(plugin_root):
    doc = (plugin_root / "refs/VERSIONS.md").read_text()
    for ver in ["nuke-15.2", "nuke-16.1", "nuke-17.0"]:
        assert ver in doc
```

- [ ] **Step 2: Run, verify fail.**
- [ ] **Step 3: Regenerate** — for each install (15.2v9, 16.1v3, 17.0v3), run the extractor CLI exactly as the old refs were built (check `git log` in the old repo for the invocation; the CLI takes headers dir, `--doc-base https://learn.foundry.com/nuke/developers/<ver>/ndkreference/Plugins`, `--doxygen <install>/Documentation/NDKExamples/Plugins`) and overwrite `ndk_index.md` + `symbol_map.tsv` in the corresponding refs dir.
- [ ] **Step 4: Write `VERSIONS.md`** — a table: refs dir, built from install (e.g. `Nuke17.0v3` macOS), extractor commit, build date, doc-base URL, symbol count, URL coverage count.
- [ ] **Step 5: Optional network spot-check test** (guarded by `NUKE_CONTEXT_NET_TESTS=1`): sample 10 URL rows per version from `symbol_map.tsv`, HEAD-request each, assert 200.
- [ ] **Step 6: Run full suite; commit** — `git commit -m "feat(refs): regenerate NDK indexes with corrected doc URLs"`

---

### Task 7: Port and rework the three model skills + api-lookup

**Files:**
- Create: `plugins/nuke-context/skills/nuke-python-model/SKILL.md`, `.../nuke-ndk-model/SKILL.md`, `.../nuke-blink-model/SKILL.md`, `.../nuke-api-lookup/SKILL.md` (ported from old repo, reworked)
- Test: `tests/test_skills.py` (port frontmatter/description tests; add new assertions below)

**Interfaces:**
- Consumes: refs layout (`refs/nuke-<VER>/...`), references guides.
- Produces: skill set consumed at runtime; path convention `${CLAUDE_PLUGIN_ROOT}/refs/nuke-<VER>/` referenced in skill bodies (plugins resolve their own root via this env var — use it, not relative paths).

- [ ] **Step 1: Port `tests/test_skills.py`** — keep: frontmatter validity, no-invented-keys, description-says-when. Drop: setup-skill and golden-harness tests. Update the skill list fixture to the six new names (four exist after this task; `nuke-performance` and `nuke-tool-structure` added by Tasks 8–9 — parametrize from directory glob so the tests cover whatever exists).
- [ ] **Step 2: Add failing content assertions**

```python
def test_lookup_skill_encodes_three_tier_rule(plugin_root):
    text = (plugin_root / "skills/nuke-api-lookup/SKILL.md").read_text()
    for needle in ["WebFetch", "real header", "compiler"]:
        assert needle in text
    assert ".nuke-agent" not in text          # old per-project path must be gone
    assert "CLAUDE_PLUGIN_ROOT" in text       # refs resolved via plugin root

def test_lookup_skill_keeps_anchoring_and_substitution_rules(plugin_root):
    text = (plugin_root / "skills/nuke-api-lookup/SKILL.md").read_text()
    assert "anchor" in text.lower()           # do not anchor grep on ^
    assert "not in the index" in text.lower() # never substitute a similar symbol

def test_lookup_skill_has_version_selection_guidance(plugin_root):
    text = (plugin_root / "skills/nuke-api-lookup/SKILL.md").read_text()
    assert "nearest older" in text.lower()

def test_model_skills_point_to_field_guide_with_verify_rule(plugin_root):
    for s in ["nuke-python-model", "nuke-ndk-model", "nuke-blink-model"]:
        text = (plugin_root / "skills" / s / "SKILL.md").read_text()
        assert "references/" in text
        assert "verif" in text.lower()        # verify-before-use framing
```

- [ ] **Step 3: Rework the skills.** Port each SKILL.md from the old repo, then apply: (a) all refs paths become `${CLAUDE_PLUGIN_ROOT}/refs/nuke-<VER>/…` and grep examples updated accordingly; (b) `nuke-api-lookup` NDK section rewritten as the three-tier rule from the spec (doc URL → WebFetch; no URL + local install → read real header under `<install>/Documentation/NDKExamples/include/DDImage/`; neither → write from index name only and let the compiler verify; never invent a symbol absent from the index), plus version-selection guidance (detect installs, else ask; if exact version missing use nearest older and say so), plus the stale-docs warning (docs may describe removed API — headers win); (c) each model skill gains a short "Practitioner field guide" section pointing at its `references/` file with the verify-before-use rule stated: *the guide tells you where to look; the official tier tells you what is true; verify any claim from it against refs/headers before it shapes code, and surface unverifiable claims to the user as unverified*; (d) keep the existing grep-don't-read-whole-file instruction and add it where absent — the big indexes must never be read in full.
- [ ] **Step 4: Run** — `python3 -m pytest tests/test_skills.py -q`. Expected: PASS.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): port model skills; api-lookup gains three-tier rule"`

---

### Task 8: New `nuke-performance` skill

**Files:**
- Create: `plugins/nuke-context/skills/nuke-performance/SKILL.md`
- Test: `tests/test_skills.py` (extend)

**Interfaces:**
- Consumes: `refs/nuke-<VER>/devguide_map.tsv` anchors, `references/` frontier notes.
- Produces: the sixth skill; referenced by README (Task 10).

- [ ] **Step 1: Add failing assertions**

```python
def test_performance_skill_covers_core_principles(plugin_root):
    text = (plugin_root / "skills/nuke-performance/SKILL.md").read_text()
    for needle in ["_request", "engine", "bbox", "hash", "devguide_map",
                   "eAccessPoint", "thread"]:
        assert needle in text, f"missing principle marker: {needle}"

def test_performance_skill_routes_not_duplicates(plugin_root):
    text = (plugin_root / "skills/nuke-performance/SKILL.md").read_text()
    assert "learn.foundry.com" not in text.replace(
        "https://learn.foundry.com", "")  # no hardcoded page prose beyond routing
    assert len(text) < 12_000  # stays a routing skill, not a textbook
```

(The second test's intent: the skill routes to `devguide_map.tsv` anchors rather than embedding Foundry content; adjust the mechanical form if needed but keep the size cap.)

- [ ] **Step 2: Write the skill.** Frontmatter description: "Use when designing or reviewing any Nuke tool for speed or memory — before choosing Python vs Blink vs NDK, when a tool is slow, or when writing NDK `_request`/`engine` or Blink kernels." Body sections: (1) *Choose the layer by granularity* — Python orchestrates the DAG, never per-pixel; Blink for per-pixel math; NDK for structural ops — with the decision test; (2) *NDK scanline contract* — request only needed channels/bbox in `_request`; `engine` is called concurrently per scanline: reentrant, no allocation, no shared mutable state; declare the produced bbox honestly in `_validate`; over-request = memory, over-produce = cache waste; `hash()`/`append` correctness so caching works; (3) *Blink cost model* — access mode ladder `eAccessPoint < eAccessRanged < eAccessRandom`, narrowest wins on GPU; `ePixelWise` vs `eComponentWise` choice; edge-mode cost (`eEdgeNone` fastest); (4) *Memory* — route to the memory-management and op-cookbook anchors in `${CLAUDE_PLUGIN_ROOT}/refs/nuke-<VER>/devguide_map.tsv` (grep the concept column) instead of restating; (5) *Verify performance claims* — a perf belief from any community source follows the verify-before-use rule; measure with Nuke's profiler node/`nuke -t` timing before and after.
- [ ] **Step 3: Run, verify pass.**
- [ ] **Step 4: Commit** — `git commit -m "feat(skills): nuke-performance principles skill"`

---

### Task 9: `nuke-tool-structure` skill (absorbs TDD; ladder + git discipline)

**Files:**
- Create: `plugins/nuke-context/skills/nuke-tool-structure/SKILL.md` (port + extend)
- Modify: `plugins/nuke-context/references/README.md` (harden trust wording)
- Test: `tests/test_skills.py` (extend)

**Interfaces:**
- Consumes: verification-ladder + version-control sections of the spec; old `nuke-tool-structure` and `nuke-tdd` SKILL.md content.
- Produces: final skill; ladder wording reused by README (Task 10).

- [ ] **Step 1: Add failing assertions**

```python
def test_tool_structure_has_verification_ladder(plugin_root):
    text = (plugin_root / "skills/nuke-tool-structure/SKILL.md").read_text()
    for needle in ["nuke -t", "MCP", "checklist", "report which rung"]:
        assert needle.lower() in text.lower()

def test_tool_structure_has_git_discipline(plugin_root):
    text = (plugin_root / "skills/nuke-tool-structure/SKILL.md").read_text()
    assert "git init" in text
    assert "milestone" in text.lower() or "rung passes" in text.lower()
    assert "git-github-setup" in text        # routes to the shipped doc

def test_references_readme_is_verify_before_use(plugin_root):
    text = (plugin_root / "references/README.md").read_text()
    assert "verified" in text.lower() and "before" in text.lower()
    assert "unverified" in text.lower()      # surface unverifiable claims as such
```

- [ ] **Step 2: Write the skill.** Port old `nuke-tool-structure` (pure core / thin shell, testable-core layout) and fold in from `nuke-tdd` the guidance-worthy parts (write the test first for core logic; never edit a test to make it pass). Add: **Verification ladder** — the four rungs from the spec verbatim (static grep → `nuke -t` headless with license-seat note → optional community Nuke MCP server with the vet-it-yourself trust note → manual user checklist with load path, knobs to touch, expected result, edge cases), ending with "always report which rung you reached — done means verified to rung N". Add: **Version control** — check for a repo at tool-work start; if absent recommend `git init` once with a one-line why, respect a decline without repeating; commit at verified milestones (each time a ladder rung passes) with short conventional messages; if git or `gh` is missing route to `${CLAUDE_PLUGIN_ROOT}/docs/git-github-setup.md` and walk the user through it.
- [ ] **Step 3: Harden `references/README.md`** — rewrite the "different trust tier" bullet to the spec's language: every claim must be verified against the official tier (refs index, versioned Foundry page, real header, or compile/`nuke -t` check) before it influences code; unverifiable claims are presented to the user as unverified community practice, never applied silently.
- [ ] **Step 4: Run, verify pass. Full suite too** — `python3 -m pytest tests/ -x -q`.
- [ ] **Step 5: Commit** — `git commit -m "feat(skills): tool-structure with verification ladder and git discipline"`

---

### Task 10: README + git/GitHub setup doc

**Files:**
- Create: `README.md` (repo root), `plugins/nuke-context/docs/git-github-setup.md`
- Test: `tests/test_readme.py` (port pattern from old repo; new assertions)

**Interfaces:**
- Consumes: everything shipped; install-scope facts (verified 2026-07-25 against code.claude.com docs).
- Produces: user-facing entry points.

- [ ] **Step 1: Write failing README tests**

```python
def test_readme_covers_the_essentials(repo_root):
    text = (repo_root / "README.md").read_text()
    for needle in ["/plugin marketplace add", "/plugin install nuke-context",
                   "--scope", "Testing your tools", "Deploying your tools",
                   "learn.foundry.com", "verify"]:
        assert needle in text, f"README missing: {needle}"

def test_readme_documents_permission_expectations(repo_root):
    text = (repo_root / "README.md").read_text()
    assert "permission" in text.lower()      # allow header reads / WebFetch note

def test_git_setup_doc_covers_all_platforms(plugin_root):
    text = (plugin_root / "docs/git-github-setup.md").read_text()
    for needle in ["xcode-select", "winget", "apt", "gh auth login",
                   "gh repo create", "git init"]:
        assert needle in text
```

- [ ] **Step 2: Write `README.md`.** Sections: what it is (one-line pitch: install, then prompt as usual — the plugin changes how the agent works, not how you work); install — personal (`/plugin marketplace add jaechoidev/nuke-agent-context`, `/plugin install nuke-context@nuke-agent-context`, note the interactive scope picker: User/Project/Local) and scriptable (`claude plugin install nuke-context@nuke-agent-context --scope project`), plus the team pattern (committed `.claude/settings.json` with `extraKnownMarketplaces` + `enabledPlugins`, exact JSON block from the spec discussion); what's inside (refs tiers table, six skills, examples); how grounding works (three-tier lookup, two trust tiers, headers/compiler are ground truth); "Testing your tools" (the four-rung ladder; recommend a community Nuke MCP server with the explicit third-party trust warning; name the ones evaluated only if the maintainer has vetted one); "Deploying your tools" (link `plugins/nuke-context/docs/git-github-setup.md`); permission expectations (first header read under `/Applications`, first `learn.foundry.com` WebFetch, first `nuke -t` will prompt — allow them for the plugin to work); eval evidence (2.1× compile rate, −70% invented APIs, link to evals when ported); license + no-Foundry-content note.
- [ ] **Step 3: Write `git-github-setup.md`.** Audience: a TA who has never used git. Sections with exact commands: install git (macOS `xcode-select --install` or `brew install git`; Windows `winget install Git.Git`; Linux `sudo apt install git` / distro equivalents); configure identity (`git config --global user.name/email`); install `gh` (brew/winget/apt lines); create GitHub account (URL + 2FA recommendation); `gh auth login` walkthrough (HTTPS, browser flow); first deploy cycle (`git init`, `.gitignore` for Nuke projects — `__pycache__/`, `*.pyc`, renders, `.nk~` autosaves — `git add`, `git commit`, `gh repo create <name> --private --source . --push`); updating (`git add -u && git commit && git push`); one-paragraph "why bother" up top (history is undo; a repo is how a tool becomes shareable).
- [ ] **Step 4: Run, verify pass; commit** — `git commit -m "docs: README and git/GitHub setup guide"`

---

### Task 11: Complex examples tier — NDK

**Files:**
- Create: `plugins/nuke-context/examples/ndk/MinimalReader.cpp`, `examples/ndk/FrameBlend.cpp` (temporal), `examples/ndk/DeepMix.cpp`, `examples/ndk/CMakeLists.txt.example`
- Modify: `plugins/nuke-context/examples/INDEX.md` (regenerate via `tools/extract_examples_index.py`)
- Test: existing `tests/test_examples_compile.py` picks them up (glob-driven); extend only if the glob misses `.example`

**Interfaces:**
- Consumes: NDK model/performance skills' conventions; old examples' header-comment format (each example states purpose, APIs exercised, and its verification route — follow it exactly; read two old examples first).
- Produces: three compilable sources + a commented CMake file (excluded from compile glob via the `.example` suffix).

- [ ] **Step 1: Read two existing NDK examples** (`Exposure.cpp`, `DeepGain.cpp`) to absorb the exact header-comment and style conventions.
- [ ] **Step 2: Write `MinimalReader.cpp`** — smallest correct `Reader` subclass: a fixed-size solid-color "format" reader registered via `Reader::Description` (the point is the registration/`open`/`engine` shape for file readers, the eval's worst case). Every API symbol verified against `refs/nuke-17.0/symbol_map.tsv` + real header before writing.
- [ ] **Step 3: Write `FrameBlend.cpp`** — two-frame temporal average: `_request` asks for `outputContext().frame()` and `frame-1` via input contexts, engine blends; demonstrates multi-frame request logic (eval case 07).
- [ ] **Step 4: Write `DeepMix.cpp`** — DeepOp mixing two deep inputs; demonstrates `getDeepRequests`/`doDeepEngine` beyond DeepGain.
- [ ] **Step 5: Compile all three locally** against 17.0v3 using the same harness `tests/test_examples_compile.py` uses. Fix until clean. Run `python3 tools/extract_examples_index.py` to regenerate `INDEX.md` (check old repo CLI usage first).
- [ ] **Step 6: Write `CMakeLists.txt.example`** — Foundry's `find_package(Nuke)` / `add_nuke_plugin()` pattern from the old repo's template, commented per line.
- [ ] **Step 7: Run full suite; commit** — `git commit -m "feat(examples): complex NDK tier - reader, temporal, deep, cmake"`

---

### Task 12: Complex examples tier — Python UI

**Files:**
- Create: `plugins/nuke-context/examples/python/dockable_panel_stateful.py`, `examples/python/render_submitter_shape.py`
- Modify: `plugins/nuke-context/examples/INDEX.md` (regenerate)
- Test: existing `tests/test_examples_python.py` (glob-driven; parses + real-API check)

**Interfaces:**
- Consumes: `registerWidgetAsPanel` pattern (refs pyguide custom-panels page), `references/pyside-panels.md` patterns, old `pyqt_panel.py` conventions.
- Produces: two examples exercising the heavy-UI surface.

- [ ] **Step 1: Write `dockable_panel_stateful.py`** — PySide6 widget registered with `nukescripts.panels.registerWidgetAsPanel`, persisting its state onto a node knob (the `nuke_PySide_helper` pattern re-derived, not copied): a list widget of selected nodes + a per-node note stored in a hidden `Text_Knob`. Import-guarded so it parses headless (`try: import nuke ... except ImportError`) matching existing examples' convention.
- [ ] **Step 2: Write `render_submitter_shape.py`** — the *shape* of a submitter without a farm dependency: introspect Write nodes (`nuke.allNodes("Write")`), frame ranges, and file paths; build a job dict; show a PySide6 confirm dialog; "submit" = write a JSON job file next to the script. Header comment states it's an architecture example modeled on the exemplar submitters in `references/tool-architecture.md`.
- [ ] **Step 3: Verify** — `python3 -m pytest tests/test_examples_python.py -q` (parse + no-invented-API against local pydocs) and, headless, `nuke -t` import if an install is present. Regenerate `INDEX.md`.
- [ ] **Step 4: Commit** — `git commit -m "feat(examples): stateful dockable panel and submitter-shaped tool"`

---

### Task 13: Port eval harness with cost capture (final phase, optional gate)

**Files:**
- Create: `evals/` (copy `run_ablation.py`, `graders/grade.py`, `cases/`, `nuke_bridge.py`, `verify_live.py`, `FINDINGS.md` from old repo; drop `_raw/`, old logs, old results)
- Modify: `evals/run_ablation.py`
- Test: `tests/test_eval_harness.py` (new, minimal)

**Interfaces:**
- Consumes: plugin as shipped (the `with` arm now installs via `--plugin-dir` pointing at `plugins/nuke-context`).
- Produces: per-run `cost_usd`, `input_tokens`, `output_tokens` fields in results JSON; summary prints mean cost per arm.

- [ ] **Step 1: Port files; update the `with`-arm setup** to launch headless runs with `--plugin-dir <repo>/plugins/nuke-context` instead of the old marketplace install + project scaffold (keep `--permission-mode bypassPermissions` and the temp-dir isolation; keep the reconciliation assertion `compiled + failed + no_code == runs`).
- [ ] **Step 2: Add cost capture.** Runner already invokes `claude -p`; switch to `--output-format json`, parse `total_cost_usd` and `usage` token fields from the result payload, store per-run, and add to the summary: mean/total cost and tokens per arm, plus the delta.
- [ ] **Step 3: Minimal harness test**

```python
# tests/test_eval_harness.py
def test_summary_reconciles_and_carries_cost(tmp_path):
    from evals.run_ablation import summarize   # adjust to actual API
    runs = [{"produced_code": True, "build": {"compiles": True},
             "cost_usd": 0.5, "input_tokens": 1000, "output_tokens": 200}]
    s = summarize(runs)
    assert s["runs"] == s["compiled"] + s["built_but_failed"] + s["produced_no_code"]
    assert s["total_cost_usd"] == 0.5
```

(Adjust names to the ported module's real structure — if `summarize` doesn't exist as a function, extract it so it's testable.)
- [ ] **Step 4: Smoke run** — one case, one run per arm, confirm cost fields land in the JSON. Full 3× ablation is a maintainer action, not part of this plan.
- [ ] **Step 5: Commit** — `git commit -m "feat(evals): port ablation harness with per-run cost capture"`

---

## Self-review notes

- Spec coverage: manifests/naming (T1); refs + references + tools port (T2); doc_url fixes (T3); parser gaps (T4); examples port + tests (T5); regeneration + VERSIONS.md + optional network check (T6); skills incl. three-tier rule, version selection, grep-don't-read (T7); nuke-performance (T8); ladder + git discipline + references hardening (T9); README distribution/permissions + git-github-setup doc (T10); complex NDK examples + CMake file (T11); heavy-UI Python examples (T12); evals with cost capture (T13). Licensing posture is enforced by porting the redistributable (`--doc-base`) rendering path unchanged and by the no-Foundry-prose constraint in Global Constraints.
- Open decisions resolved per spec defaults: plugin name `nuke-context`; no beta refs (tested in T2).
