# Refs build provenance

Each directory is generated from a real local Nuke install by the extractors
in `tools/` (maintainer-run; installers never regenerate). The Python, Blink,
and guide indexes were built 2026-07-25 from the same installs' shipped docs;
the NDK indexes were regenerated 2026-07-25 with the fixed extractor
(doc_url struct pages + doxygen underscore escaping; parser now indexes
single-line template classes and lowercase-prefixed names — commit `feb8f6d`).

| Refs dir | Built from | Platform | NDK symbols | With doc URL | Doc base URL |
| --- | --- | --- | --- | --- | --- |
| `nuke-15.2` | Nuke15.2v9 | macOS arm64 | 456 | 300 | `https://learn.foundry.com/nuke/developers/15.2/ndkreference/Plugins` |
| `nuke-16.1` | Nuke16.1v3 | macOS arm64 | 523 | 331 | `https://learn.foundry.com/nuke/developers/16.1/ndkreference/Plugins` |
| `nuke-17.0` | Nuke17.0v3 | macOS arm64 | 523 | 331 | `https://learn.foundry.com/nuke/developers/17.0/ndkreference/Plugins` |

Notes:

- 16.1 and 17.0 ship byte-identical DDImage APIs (same index hash
  `bb980c59349c`); both directories are kept so version pinning stays
  explicit for users.
- A symbol without a URL is real but publicly undocumented (~37% of DDImage):
  the api-lookup skill's fallback is the local header, then the compiler.
- Foundry's doxygen also documents API absent from the shipped headers
  (e.g. `GenericImagePlane` in 17.0) — stale pages. Headers win; the index
  only records what the headers declare.
- Beta installs are never indexed.
