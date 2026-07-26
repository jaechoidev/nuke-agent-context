import hashlib
import importlib.util
import pathlib
import re
import subprocess
import sys

import pytest


def load(tools_root):
    p = tools_root / "extract_ndk_index.py"
    spec = importlib.util.spec_from_file_location("extract_ndk_index", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["extract_ndk_index"] = mod
    spec.loader.exec_module(mod)
    return mod


def by_version(nuke_installs):
    d = {i["root"].name.replace("Nuke", ""): i["headers"] for i in nuke_installs}
    if not d:
        pytest.skip("no Nuke install with DDImage headers found")
    return d


# --- synthetic headers -------------------------------------------------------
# Hand-written C++ that exercises every branch of the parser. Nothing here is
# copied from any vendor header: these tests must run without a Nuke install and
# must not carry third-party text into the repo.

SYNTHETIC = {
    # Sorts first, so if forward declarations were indexed this file would win
    # the setdefault race and own both names.
    "AaaForward.h": (
        "// Only forward declarations live here.\n"
        "class Widget;\n"
        "struct Gadget;\n"
        "class Renamed : public Widget;\n"
    ),
    "Widget.h": (
        "/*! \\class Widget\n"
        "    A widget holds pixels. This second sentence is dropped.\n"
        "*/\n"
        "class NUKE_API Widget : public Base\n"
        "{\n"
        "public:\n"
        "  int x;\n"
        "};\n"
    ),
    "Gadget.h": (
        "//! A gadget does gadget things.\n"
        "//! Continuation line, same comment.\n"
        "struct Gadget {\n"
        "};\n"
    ),
    "Redirect.h": (
        "/*! \\class Elsewhere\n"
        "    Elsewhere is documented above its neighbour.\n"
        "*/\n"
        "class Neighbour\n"
        "{\n"
        "};\n"
        "\n"
        "class Elsewhere\n"
        "{\n"
        "};\n"
    ),
    "Tagged.h": (
        "/*! \\brief Strips doxygen tags.\n"
        " *  \\param a ignored\n"
        " */\n"
        "class Tagged\n"
        "{\n"
        "};\n"
    ),
    "Braced.h": (
        "/** Brace sits on its own line. */\n"
        "class Braced\n"
        "  : public Widget\n"
        "{\n"
        "};\n"
        "\n"
        "class Undocumented\n"
        "{\n"
        "};\n"
        "\n"
        "template <class T>\n"
        "class Templated\n"
        "{\n"
        "};\n"
    ),
}


def write_synthetic(dirpath, extra=None):
    dirpath.mkdir(parents=True, exist_ok=True)
    for name, text in {**SYNTHETIC, **(extra or {})}.items():
        (dirpath / name).write_text(text)
    return dirpath


# --- the reference installs --------------------------------------------------


def test_key_classes_resolve_with_descriptions(tools_root, nuke_installs):
    """The classes a compositor actually touches must be found AND described."""
    mod = load(tools_root)
    hdrs = by_version(nuke_installs)["17.0v3"]
    idx = mod.build_index(hdrs)
    expected = {
        "Row": "Row.h", "Iop": "Iop.h", "Op": "Op.h", "Knob": "Knob.h",
        "ChannelSet": "ChannelSet.h", "Format": "Format.h", "Box": "Box.h",
        "DeepOp": "DeepOp.h", "GeoOp": "GeoOp.h", "Reader": "Reader.h",
        "Writer": "Writer.h", "PixelIop": "PixelIop.h", "Interest": "Interest.h",
    }
    for name, header in expected.items():
        assert name in idx, f"{name} not indexed"
        assert idx[name].header == header
        assert idx[name].desc, f"{name} has no description"
        assert idx[name].line > 0


def test_description_coverage_at_least_60_percent(tools_root, nuke_installs):
    mod = load(tools_root)
    versions = by_version(nuke_installs)
    assert versions, "no installs to measure coverage on"
    for label, hdrs in versions.items():
        idx = mod.build_index(hdrs)
        assert idx, f"{label}: empty index"
        described = sum(1 for s in idx.values() if s.desc)
        pct = 100 * described // len(idx)
        assert pct >= 60, f"{label}: only {pct}% described"


def test_no_forward_declarations_indexed(tools_root, nuke_installs):
    """`class Iop;` is a forward decl, not a definition — must not be indexed."""
    mod = load(tools_root)
    hdrs = by_version(nuke_installs)["17.0v3"]
    idx = mod.build_index(hdrs)
    # Row.h forward-declares Iop and CacheLineUnlockGuard; neither belongs to Row.h
    assert idx["Iop"].header == "Iop.h"
    assert "CacheLineUnlockGuard" not in idx or idx["CacheLineUnlockGuard"].header != "Row.h"


def test_identical_apis_produce_identical_hash(tools_root, nuke_installs):
    """16.1v3 and 17.0v3 ship byte-identical headers -> one shared index."""
    mod = load(tools_root)
    v = by_version(nuke_installs)
    h16 = mod.index_hash(mod.build_index(v["16.1v3"]))
    h17 = mod.index_hash(mod.build_index(v["17.0v3"]))
    assert h16 == h17


def test_different_apis_produce_different_hash(tools_root, nuke_installs):
    mod = load(tools_root)
    v = by_version(nuke_installs)
    h15 = mod.index_hash(mod.build_index(v["15.2v9"]))
    h17 = mod.index_hash(mod.build_index(v["17.0v3"]))
    assert h15 != h17


def test_symbol_counts_match_reference(tools_root, nuke_installs):
    mod = load(tools_root)
    v = by_version(nuke_installs)
    assert len(mod.build_index(v["15.2v9"])) == 445
    assert len(mod.build_index(v["16.1v3"])) == 511
    assert len(mod.build_index(v["17.0v3"])) == 511


def test_cli_writes_both_artifacts(tools_root, nuke_installs, tmp_path):
    hdrs = by_version(nuke_installs)["17.0v3"]
    out = tmp_path / "out"
    work = tmp_path / "work"
    work.mkdir()
    r = subprocess.run(
        [sys.executable, str(tools_root / "extract_ndk_index.py"),
         str(hdrs), "--out", str(out)],
        capture_output=True, text=True, cwd=work)
    assert r.returncode == 0, r.stderr
    md = (out / "ndk_index.md").read_text()
    tsv = (out / "symbol_map.tsv").read_text()
    assert "| `Row` |" in md
    assert "Row\tRow.h\t" in tsv
    assert len(tsv.strip().splitlines()) == 511 + 1        # + header row
    # Nothing may be written outside --out: these artifacts are derived from
    # Foundry headers and must never land in the repo.
    assert list(work.iterdir()) == [], f"wrote outside --out: {list(work.iterdir())}"


# --- independent oracles -----------------------------------------------------
# The tests above compare the parser against numbers the parser itself produced
# on a previous run. These check it against facts it did not generate: the raw
# bytes of the headers, and order-independence properties of the renderers.


def test_every_recorded_line_really_declares_that_symbol(tools_root, nuke_installs):
    """Read the header back and look at the line the index points to.

    The oracle is the header text itself, not another copy of CLASS_RE: a much
    looser rule (line begins with class/struct, mentions the name, is not a
    forward declaration). An off-by-one in the line number lands on the previous
    line -- usually a comment or a blank -- and fails here.
    """
    mod = load(tools_root)
    for label, hdrs in by_version(nuke_installs).items():
        idx = mod.build_index(hdrs)
        assert idx, f"{label}: empty index"
        cache = {}
        for sym in idx.values():
            src = cache.setdefault(
                sym.header, (pathlib.Path(hdrs) / sym.header).read_text(
                    errors="replace").splitlines())
            assert 1 <= sym.line <= len(src), f"{label}: {sym.name} line out of range"
            line = src[sym.line - 1]
            assert line.lstrip().startswith(("class", "struct")), \
                f"{label}: {sym.name} -> {sym.header}:{sym.line} is not a declaration: {line!r}"
            assert re.search(rf"\b{re.escape(sym.base)}\b", line), \
                f"{label}: {sym.name} not named on {sym.header}:{sym.line}: {line!r}"
            assert not line.rstrip().endswith(";"), \
                f"{label}: {sym.name} -> forward declaration {line!r}"


def _declared_outside_comments(text: str) -> set:
    """Class/struct names in real code, ignoring anything inside a comment.

    Deliberately NOT the parser's own comment stripper -- a hand-rolled scan, so
    the two cannot share a bug. DDImage ships `class MyOp : public Op {` inside a
    doxygen \\code block in Op.h; an oracle that reads raw text calls that
    'declared' and rubber-stamps a symbol the parser invented.
    """
    out, i, n, st = [], 0, len(text), 0        # st: 0 code, 1 block, 2 line
    while i < n:
        c, nxt = text[i], (text[i + 1] if i + 1 < n else "")
        if st == 0:
            if c == "/" and nxt == "*":
                st, i = 1, i + 2
                continue
            if c == "/" and nxt == "/":
                st, i = 2, i + 2
                continue
            out.append(c)
        elif st == 1:
            if c == "*" and nxt == "/":
                st, i = 0, i + 2
                continue
            if c == "\n":
                out.append(c)
        else:
            if c == "\n":
                st = 0
                out.append(c)
        i += 1
    return set(re.findall(r"\b(?:class|struct)[ \t]+(?:\w+[ \t]+)?(\w+)", "".join(out)))


def test_index_invents_no_symbols(tools_root, nuke_installs):
    """Every indexed name must be declared in real code in its header.

    Checked against an independently written comment-aware scan, so a symbol
    lifted out of an example inside a comment fails here.
    """
    mod = load(tools_root)
    hdrs = by_version(nuke_installs)["17.0v3"]
    idx = mod.build_index(hdrs)
    assert idx, "empty index"
    declared = {h.name: _declared_outside_comments(h.read_text(errors="replace"))
                for h in sorted(pathlib.Path(hdrs).glob("*.h"))}
    assert declared, "oracle found no headers"
    for sym in idx.values():
        assert sym.header in declared, f"{sym.name}: unknown header {sym.header}"
        assert sym.base in declared[sym.header], \
            f"{sym.name} is not declared in real code in {sym.header}"


def test_phantom_classes_from_doc_examples_are_not_indexed(tools_root, nuke_installs):
    """DDImage documents its plugin idiom with `class MyOp : public Op {` inside
    a doxygen \\code block. Indexing those fabricates classes that do not exist."""
    mod = load(tools_root)
    for label, hdrs in by_version(nuke_installs).items():
        bases = {s.base for s in mod.build_index(hdrs).values()}
        assert bases, f"{label}: empty index"
        for phantom in ("MyOp", "MyGeomOp", "MyEngine", "MyReader", "MyWriter"):
            assert phantom not in bases, f"{label}: indexed comment example {phantom}"


def test_nested_classes_are_qualified_not_collapsed(tools_root, nuke_installs):
    """`Description` is declared in 13 headers as a nested class, and every NDK
    plugin registers itself with `static const Op::Description description;`.
    Collapsing them to one flat key sends the agent to the wrong idiom."""
    mod = load(tools_root)
    idx = mod.build_index(by_version(nuke_installs)["17.0v3"])
    assert idx["Op::Description"].header == "Op.h"
    assert idx["Reader::Description"].header == "Reader.h"
    assert idx["DeepReader::Description"].header == "DeepReader.h"
    # No definition may be discarded: several distinct Description types coexist.
    descs = {k for k in idx if k.rsplit("::", 1)[-1] == "Description"}
    assert len(descs) >= 8, f"Description definitions collapsed: {sorted(descs)}"


def test_descriptions_are_not_stolen_from_a_neighbour(tools_root, nuke_installs):
    """A doc comment separated from a declaration by real code belongs to that
    code, not to the declaration. Without a blank-gap rule `PolyMesh::SubFace`
    inherits PolyMesh's sentence and claims to be the containing surface."""
    mod = load(tools_root)
    idx = mod.build_index(by_version(nuke_installs)["17.0v3"])
    for outer, inner in [("PolyMesh", "SubFace"), ("Bundle", "CompareKey"),
                         ("GeometryList", "ObjectRange")]:
        key = f"{outer}::{inner}"
        assert key in idx, f"{key} missing"
        if idx[key].desc and outer in idx:
            assert idx[key].desc != idx[outer].desc, \
                f"{key} adopted {outer}'s description: {idx[key].desc!r}"


def test_descriptions_are_prose_not_punctuation(tools_root, nuke_installs):
    """`////////...` section dividers parse as `///` doc comments. Adopting one
    gives a class a description that is a run of 61 slashes."""
    mod = load(tools_root)
    for label, hdrs in by_version(nuke_installs).items():
        idx = mod.build_index(hdrs)
        assert idx, f"{label}: empty index"
        for sym in idx.values():
            if not sym.desc:
                continue
            useful = sum(1 for c in sym.desc if c.isalnum() or c.isspace())
            assert useful / len(sym.desc) >= 0.6, \
                f"{label}: {sym.name} description is not prose: {sym.desc!r}"


def test_renderings_are_sorted_by_name(tools_root, nuke_installs):
    """Checked pairwise, not by re-running sorted() on the same key function."""
    mod = load(tools_root)
    idx = mod.build_index(by_version(nuke_installs)["17.0v3"])
    assert len(idx) > 1, "need at least two symbols to check ordering"
    rows = mod.render_symbol_map(idx).strip().splitlines()[1:]
    names = [r.split("\t")[0] for r in rows]
    assert len(names) == len(idx)
    for a, b in zip(names, names[1:]):
        assert a < b, f"symbol_map not ascending: {a!r} then {b!r}"
    md_names = re.findall(r"^\| `([^`]+)` \|", mod.render_index_md(idx), re.M)
    assert md_names == names, "ndk_index.md and symbol_map.tsv disagree on order"


def test_hash_ignores_insertion_order(tools_root, nuke_installs):
    """Canonical means canonical: same symbols, different dict order, same hash."""
    mod = load(tools_root)
    idx = mod.build_index(by_version(nuke_installs)["17.0v3"])
    assert len(idx) > 1
    shuffled = dict(reversed(list(idx.items())))
    assert list(shuffled) != list(idx), "reversal did not change insertion order"
    assert mod.index_hash(shuffled) == mod.index_hash(idx)
    assert mod.render_symbol_map(shuffled) == mod.render_symbol_map(idx)
    assert mod.render_index_md(shuffled) == mod.render_index_md(idx)


def test_hash_is_sha256_of_the_published_routing_data(tools_root, tmp_path):
    """Recompute the digest from the TSV artifact, a separate rendering path.

    Catches a hash that silently stops covering what it claims to cover -- e.g.
    one that drops the line number, or hashes the object repr.
    """
    mod = load(tools_root)
    hdrs = write_synthetic(tmp_path / "hdrs")
    idx = mod.build_index(hdrs)
    assert idx, "empty index"
    rows = mod.render_symbol_map(idx).strip().splitlines()[1:]
    canon = "\n".join("|".join(r.split("\t")) for r in rows)
    assert mod.index_hash(idx) == hashlib.sha256(canon.encode()).hexdigest()[:12]
    assert len(mod.index_hash(idx)) == 12


def test_hash_changes_when_a_symbol_moves(tools_root, tmp_path):
    """A line number shift is an API-relevant change and must alter the hash."""
    mod = load(tools_root)
    a = write_synthetic(tmp_path / "a")
    b = write_synthetic(tmp_path / "b")
    (b / "Widget.h").write_text("\n" + (a / "Widget.h").read_text())
    ia, ib = mod.build_index(a), mod.build_index(b)
    assert set(ia) == set(ib), "the edit must not change which symbols exist"
    assert ib["Widget"].line == ia["Widget"].line + 1
    assert mod.index_hash(ia) != mod.index_hash(ib)
    # ...and an untouched copy still hashes identically.
    assert mod.index_hash(mod.build_index(write_synthetic(tmp_path / "c"))) \
        == mod.index_hash(ia)


# --- parser behaviour on hand-written headers --------------------------------


def test_parse_header_reads_descriptions(tools_root, tmp_path):
    mod = load(tools_root)
    hdrs = write_synthetic(tmp_path / "hdrs")

    widget = mod.parse_header(hdrs / "Widget.h")
    assert set(widget) == {"Widget"}
    assert widget["Widget"].header == "Widget.h"
    assert widget["Widget"].line == 4
    assert widget["Widget"].desc == "A widget holds pixels."   # one sentence only

    gadget = mod.parse_header(hdrs / "Gadget.h")               # //! line comments
    assert gadget["Gadget"].line == 3
    assert gadget["Gadget"].desc == "A gadget does gadget things."

    tagged = mod.parse_header(hdrs / "Tagged.h")               # \brief, \param
    assert tagged["Tagged"].desc == "Strips doxygen tags."
    assert "\\" not in tagged["Tagged"].desc
    assert "*" not in tagged["Tagged"].desc

    braced = mod.parse_header(hdrs / "Braced.h")               # brace on next line
    assert braced["Braced"].line == 2
    assert braced["Braced"].desc == "Brace sits on its own line."
    assert braced["Undocumented"].desc == ""                   # no comment, no prose
    assert braced["Templated"].line == 12                      # template <class T> skipped
    assert "T" not in braced


def test_doc_comment_naming_another_class_is_not_misattributed(tools_root, tmp_path):
    r"""`\class Elsewhere` above `class Neighbour` documents Elsewhere, not Neighbour."""
    mod = load(tools_root)
    hdrs = write_synthetic(tmp_path / "hdrs")
    syms = mod.parse_header(hdrs / "Redirect.h")
    assert syms["Neighbour"].desc == "", syms["Neighbour"].desc
    assert syms["Elsewhere"].desc == "Elsewhere is documented above its neighbour."
    assert syms["Elsewhere"].line == 8


def test_forward_declarations_never_win_the_definition(tools_root, tmp_path):
    """AaaForward.h sorts first, so a parser that indexed `class Widget;` would
    record it there. Definitions live in Widget.h and Gadget.h."""
    mod = load(tools_root)
    hdrs = write_synthetic(tmp_path / "hdrs")
    assert "class Widget;" in (hdrs / "AaaForward.h").read_text()
    assert mod.parse_header(hdrs / "AaaForward.h") == {}
    idx = mod.build_index(hdrs)
    assert idx["Widget"].header == "Widget.h"
    assert idx["Gadget"].header == "Gadget.h"
    assert "Renamed" not in idx


def test_build_index_accepts_a_string_path(tools_root, tmp_path):
    mod = load(tools_root)
    hdrs = write_synthetic(tmp_path / "hdrs")
    assert mod.build_index(str(hdrs)) == mod.build_index(hdrs)


def test_symbol_is_a_hashable_dataclass(tools_root, tmp_path):
    mod = load(tools_root)
    idx = mod.build_index(write_synthetic(tmp_path / "hdrs"))
    s = idx["Widget"]
    assert (s.name, s.header, s.line, s.desc) == ("Widget", "Widget.h", 4,
                                                  "A widget holds pixels.")
    assert len({s, mod.Symbol("Widget", "Widget.h", 4, "A widget holds pixels.")}) == 1


# --- the published markdown is the artifact the agent actually reads ---------

MD_ROW = re.compile(r"^\| `([^`]+)` \| ([^|]+?) \| (\d+) \| ?(.*?) ?\|$")


def _parse_index_md(text: str) -> dict:
    """Read ndk_index.md back into {symbol: (header, line)}."""
    out = {}
    for ln in text.splitlines():
        m = MD_ROW.match(ln)
        if m:
            out[m.group(1)] = (m.group(2).strip(), int(m.group(3)))
    return out


def _parse_index_md_descriptions(text: str) -> dict:
    """Read ndk_index.md back into {symbol: description}."""
    out = {}
    for ln in text.splitlines():
        m = MD_ROW.match(ln)
        if m:
            out[m.group(1)] = m.group(4).strip()
    return out


def test_published_markdown_carries_the_descriptions(tools_root, nuke_installs):
    """Blanking the Purpose column left the suite green: the routing checks only
    compare name/header/line. The description is why the agent picks one symbol
    over another, so it has to be published, not merely computed."""
    mod = load(tools_root)
    idx = mod.build_index(by_version(nuke_installs)["17.0v3"])
    got = _parse_index_md_descriptions(mod.render_index_md(idx))
    assert got, "no rows parsed"
    described = {k: v.desc for k, v in idx.items() if v.desc}
    assert len(described) > 300, f"only {len(described)} descriptions to publish"
    for name, desc in described.items():
        assert got.get(name, "").startswith(desc[:60]), \
            f"{name}: markdown lost the description ({got.get(name)!r})"


def test_variant_definitions_are_counted_not_silently_dropped(tools_root, nuke_installs):
    """Thread.h defines Lock, SignalLock, ReadWriteLock and RecursiveLock twice
    over, under `#if !defined(_WIN32)` / `#else`. Same logical class, so one
    routing entry is right -- but the duplication must be recorded, not hidden."""
    mod = load(tools_root)
    idx = mod.build_index(by_version(nuke_installs)["17.0v3"])
    assert idx["RecursiveLock"].variants == 4, idx["RecursiveLock"]
    assert idx["Lock"].variants == 2, idx["Lock"]
    assert idx["Lock"].header == "Thread.h"
    # and the count reaches the published artifact
    assert "_(4 variants)_" in mod.render_index_md(idx)


def test_cross_header_collisions_keep_the_first_and_count_the_rest(tools_root, tmp_path):
    """Qualification removes every real cross-header collision in DDImage today,
    so this branch is unreachable on the shipped headers. Exercised synthetically
    so a future Nuke release cannot reintroduce silent dropping unnoticed."""
    mod = load(tools_root)
    d = tmp_path / "hdrs"
    d.mkdir()
    (d / "Aaa.h").write_text("namespace DD {\nclass Widget\n{\n};\n}\n")
    (d / "Bbb.h").write_text("namespace DD {\nclass Widget\n{\n};\n}\n")
    idx = mod.build_index(d)
    assert idx["Widget"].header == "Aaa.h", "first definition must win"
    assert idx["Widget"].variants == 2, "the second must be counted, not dropped"


def test_published_markdown_routing_matches_the_index(tools_root, nuke_installs):
    """ndk_index.md is the file the agent reads to choose a header, and it was
    previously unvalidated: hardcoding one header for every row, or adding 1 to
    every line number, left the whole suite green. Parse it back and compare.
    """
    mod = load(tools_root)
    for label, hdrs in by_version(nuke_installs).items():
        idx = mod.build_index(hdrs)
        rows = _parse_index_md(mod.render_index_md(idx))
        assert rows, f"{label}: no rows parsed out of ndk_index.md"
        assert len(rows) == len(idx), \
            f"{label}: {len(idx)} symbols but {len(rows)} markdown rows"
        for name, sym in idx.items():
            assert name in rows, f"{label}: {name} missing from markdown"
            assert rows[name] == (sym.header, sym.line), \
                f"{label}: {name} markdown says {rows[name]}, index says " \
                f"({sym.header}, {sym.line})"


def test_markdown_and_tsv_agree_on_header_and_line(tools_root, nuke_installs):
    """The two published artifacts are rendered separately; if they disagree,
    one of them is lying to the agent."""
    mod = load(tools_root)
    idx = mod.build_index(by_version(nuke_installs)["17.0v3"])
    rows = _parse_index_md(mod.render_index_md(idx))
    tsv = {}
    for ln in mod.render_symbol_map(idx).splitlines()[1:]:
        name, header, line = ln.split("\t")
        tsv[name] = (header, int(line))
    assert rows and tsv
    assert set(rows) == set(tsv), "markdown and tsv list different symbols"
    for name in rows:
        assert rows[name] == tsv[name], \
            f"{name}: markdown {rows[name]} vs tsv {tsv[name]}"


def test_every_markdown_row_has_the_full_column_count(tools_root, nuke_installs):
    """A description containing a pipe would silently shift the table columns."""
    mod = load(tools_root)
    idx = mod.build_index(by_version(nuke_installs)["17.0v3"])
    body = [ln for ln in mod.render_index_md(idx).splitlines()
            if ln.startswith("| `")]
    assert body
    for ln in body:
        assert ln.count("|") == 5, f"column count wrong: {ln!r}"


# --- CLI ---------------------------------------------------------------------


def test_cli_output_matches_the_api(tools_root, tmp_path):
    mod = load(tools_root)
    hdrs = write_synthetic(tmp_path / "hdrs")
    out = tmp_path / "out"
    work = tmp_path / "work"
    work.mkdir()
    r = subprocess.run(
        [sys.executable, str(tools_root / "extract_ndk_index.py"),
         str(hdrs), "--out", str(out)],
        capture_output=True, text=True, cwd=work)
    assert r.returncode == 0, r.stderr
    idx = mod.build_index(hdrs)
    assert (out / "symbol_map.tsv").read_text() == mod.render_symbol_map(idx)
    assert (out / "ndk_index.md").read_text() == mod.render_index_md(idx)
    assert list(work.iterdir()) == [], f"wrote outside --out: {list(work.iterdir())}"
    described = sum(1 for s in idx.values() if s.desc)
    assert f"{len(idx)} symbols" in r.stdout
    assert f"{described} described" in r.stdout
    assert mod.index_hash(idx) in r.stdout
    # The out directory is created if absent, and nothing lands outside it.
    assert sorted(p.name for p in out.iterdir()) == ["ndk_index.md", "symbol_map.tsv"]


def test_cli_requires_an_explicit_out_directory(tools_root, tmp_path):
    """No default --out: vendor-derived text must never land somewhere implicit."""
    hdrs = write_synthetic(tmp_path / "hdrs")
    r = subprocess.run(
        [sys.executable, str(tools_root / "extract_ndk_index.py"),
         str(hdrs)],
        capture_output=True, text=True, cwd=tmp_path)
    assert r.returncode != 0
    assert "--out" in r.stderr
    assert not list((tmp_path).glob("*.md")) and not list((tmp_path).glob("*.tsv"))


def test_cli_rejects_a_bad_directory(tools_root, tmp_path):
    script = str(tools_root / "extract_ndk_index.py")
    missing = subprocess.run(
        [sys.executable, script, str(tmp_path / "nope"), "--out", str(tmp_path / "o1")],
        capture_output=True, text=True)
    assert missing.returncode == 1
    assert "not a directory" in missing.stderr.lower()
    assert not (tmp_path / "o1").exists(), "failed run must not create --out"

    (tmp_path / "empty").mkdir()
    empty = subprocess.run(
        [sys.executable, script, str(tmp_path / "empty"), "--out", str(tmp_path / "o2")],
        capture_output=True, text=True)
    assert empty.returncode == 1
    assert "no classes found" in empty.stderr.lower()
    assert not (tmp_path / "o2").exists()


def test_markdown_table_survives_real_descriptions(tools_root, nuke_installs):
    """A `|` in a doc comment would silently split a row into extra columns.

    None of the three reference installs contains one, so this is a guard
    against a future header rather than a current defect -- but a broken table
    is exactly the kind of thing that reads fine in a diff and misroutes the
    agent at runtime.
    """
    mod = load(tools_root)
    for label, hdrs in by_version(nuke_installs).items():
        idx = mod.build_index(hdrs)
        assert idx, f"{label}: empty index"
        rows = [ln for ln in mod.render_index_md(idx).splitlines() if ln.startswith("| `")]
        assert len(rows) == len(idx), f"{label}: {len(rows)} rows for {len(idx)} symbols"
        for row in rows:
            assert row.count("|") == 5, f"{label}: malformed row {row!r}"


def test_index_covers_only_the_public_top_level_headers(tools_root, nuke_installs):
    """`glob("*.h")` is deliberately non-recursive: DDImage/private/ is internal
    API the agent must never be pointed at."""
    mod = load(tools_root)
    hdrs = pathlib.Path(by_version(nuke_installs)["17.0v3"])
    nested = [p for p in hdrs.rglob("*.h") if p.parent != hdrs]
    assert nested, "expected DDImage to ship nested headers"
    assert any(p.parent.name == "private" for p in nested)
    idx = mod.build_index(hdrs)
    assert idx
    top_level = {p.name for p in hdrs.glob("*.h")}
    assert {s.header for s in idx.values()} <= top_level
    for sym in idx.values():
        assert "/" not in sym.header and (hdrs / sym.header).is_file()


def test_markdown_table_is_well_formed(tools_root, tmp_path):
    mod = load(tools_root)
    idx = mod.build_index(write_synthetic(tmp_path / "hdrs"))
    assert idx
    md = mod.render_index_md(idx)
    rows = [ln for ln in md.splitlines() if ln.startswith("| `")]
    assert len(rows) == len(idx)
    for row in rows:
        assert row.count("|") == 5, row          # 4 cells -> 5 pipes
        assert "\n" not in row
    assert f"{len(idx)} classes" in md
    for sym in idx.values():                     # descriptions stay one-line
        assert "\n" not in sym.desc and len(sym.desc) <= 205


# --- doc URLs (redistributable mode: link to Foundry, don't copy prose) ------
# The committed baseline must carry no Foundry documentation text. Instead of the
# scraped Purpose prose, `--doc-base` emits a public learn.foundry.com URL the
# agent can fetch on demand. The doxygen page name is derived from the symbol.

NDK_BASE = "https://learn.foundry.com/nuke/developers/17.0/ndkreference/Plugins"


def test_doc_url_builds_the_doxygen_class_page(tools_root):
    mod = load(tools_root)
    assert mod.doc_url("Iop", NDK_BASE) == \
        NDK_BASE + "/classDD_1_1Image_1_1Iop.html"


def test_doc_url_qualifies_nested_classes(tools_root):
    """`Op::Description` -> classDD_1_1Image_1_1Op_1_1Description.html (:: -> _1_1)."""
    mod = load(tools_root)
    assert mod.doc_url("Op::Description", NDK_BASE) == \
        NDK_BASE + "/classDD_1_1Image_1_1Op_1_1Description.html"


def test_doc_url_omitted_when_the_page_does_not_exist(tools_root, tmp_path):
    """Not every symbol is a DD::Image class (Tile has no such page). Verified
    against the real doxygen dir, a missing page yields no URL, never a 404."""
    mod = load(tools_root)
    dox = tmp_path / "dox"
    dox.mkdir()
    (dox / "classDD_1_1Image_1_1Iop.html").write_text("x")
    assert mod.doc_url("Iop", NDK_BASE, dox) == \
        NDK_BASE + "/classDD_1_1Image_1_1Iop.html"
    assert mod.doc_url("Tile", NDK_BASE, dox) == ""


def test_doc_url_escapes_underscores(tools_root, tmp_path):
    mod = load(tools_root)
    (tmp_path / "classDD_1_1Image_1_1MultiArray__KnobI.html").write_text("x")
    url = mod.doc_url("MultiArray_KnobI", "https://x/Plugins", tmp_path)
    assert url == "https://x/Plugins/classDD_1_1Image_1_1MultiArray__KnobI.html"


def test_doc_url_finds_struct_pages(tools_root, tmp_path):
    mod = load(tools_root)
    (tmp_path / "structDD_1_1Image_1_1IRange.html").write_text("x")
    assert mod.doc_url("IRange", "https://x/Plugins", tmp_path).endswith(
        "structDD_1_1Image_1_1IRange.html")


def test_doc_url_nested_and_underscored(tools_root, tmp_path):
    mod = load(tools_root)
    (tmp_path / "structDD_1_1Image_1_1Knob_1_1Visibility__Fn.html").write_text("x")
    assert mod.doc_url("Knob::Visibility_Fn", "https://x/Plugins", tmp_path).endswith(
        "structDD_1_1Image_1_1Knob_1_1Visibility__Fn.html")


def test_doc_url_absent_page_is_empty(tools_root, tmp_path):
    mod = load(tools_root)
    assert mod.doc_url("NoSuchThing", "https://x/Plugins", tmp_path) == ""


def test_doc_base_render_swaps_prose_for_a_url(tools_root, tmp_path):
    """In --doc-base mode the Purpose prose is gone and a Docs URL takes its place."""
    mod = load(tools_root)
    idx = mod.build_index(write_synthetic(tmp_path / "hdrs"))
    md = mod.render_index_md(idx, doc_base=NDK_BASE)
    assert "A widget holds pixels" not in md, "Foundry-style prose leaked into URL mode"
    assert "| Symbol | Header | Line | Docs |" in md
    assert NDK_BASE + "/classDD_1_1Image_1_1Widget.html" in md
    rows = [ln for ln in md.splitlines() if ln.startswith("| `")]
    assert rows and all(ln.count("|") == 5 for ln in rows)


def test_doc_base_symbol_map_gains_a_url_column(tools_root, tmp_path):
    mod = load(tools_root)
    idx = mod.build_index(write_synthetic(tmp_path / "hdrs"))
    tsv = mod.render_symbol_map(idx, doc_base=NDK_BASE)
    header = tsv.splitlines()[0]
    assert header == "symbol\theader\tline\turl"
    row = next(r for r in tsv.splitlines()[1:] if r.startswith("Widget\t"))
    assert row.split("\t")[3] == NDK_BASE + "/classDD_1_1Image_1_1Widget.html"


def test_default_render_is_unchanged_without_doc_base(tools_root, tmp_path):
    """No --doc-base -> the existing prose layout, byte for byte."""
    mod = load(tools_root)
    idx = mod.build_index(write_synthetic(tmp_path / "hdrs"))
    assert "| Symbol | Header | Line | Purpose |" in mod.render_index_md(idx)
    assert mod.render_symbol_map(idx).splitlines()[0] == "symbol\theader\tline"
