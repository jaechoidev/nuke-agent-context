# Community field guides — the practitioner landscape

Short, original "learn the landscape" articles for each layer of Nuke tool
development, distilled from the community resources the maintainer curated. Each
one orients you to how practitioners actually approach the problem and links out
to the source when you need the depth.

## What these are — and are not

- **Original synthesis.** Every article is written from scratch; sources are
  cited, never republished. Go to the linked page for the full treatment.
- **A different trust tier from the official refs.** These summarise blogs,
  tutorials and open-source repos — *unofficial, unversioned, and liable to rot.*
  Treat them as practitioner perspective, not authority. When a claim here
  matters for correctness, verify it against the version-pinned official
  references (`refs/nuke-<VER>/`) and the real headers/docs. Where the two
  disagree, the official source wins.
- **A map, not a manual.** The articles teach the terrain and route you to the
  best source; exact APIs and signatures live in the API indexes, and the
  authoritative concept explanations live in the Foundry guides
  (`refs/nuke-<VER>/devguide_index.md`, `pyguide_index.md`, `blinkguide_index.md`).

## The guides

| Layer / topic | Read |
| --- | --- |
| NDK (C++ plugins) | [ndk.md](ndk.md) |
| BlinkScript (GPU kernels) | [blink.md](blink.md) |
| Nuke Python | [python.md](python.md) |
| PySide / panel UI | [pyside-panels.md](pyside-panels.md) |
| Tool & pipeline architecture (exemplar repos) | [tool-architecture.md](tool-architecture.md) |
