"""Quality gates on the shipped, pre-built refs.

The indexes are the plugin's ground truth; these tests pin the properties the
skills rely on: URL coverage after the doc_url fixes, the specific symbols
those fixes recovered, and build provenance in VERSIONS.md.
"""
import os
import random
import urllib.request

import pytest

VERSIONS = ["nuke-15.2", "nuke-16.1", "nuke-17.0"]


def rows_of(plugin_root, ver):
    tsv = plugin_root / "refs" / ver / "symbol_map.tsv"
    return [r.split("\t") for r in tsv.read_text().splitlines()[1:]]


def test_17_symbol_map_url_coverage(plugin_root):
    rows = rows_of(plugin_root, "nuke-17.0")
    with_url = sum(1 for r in rows if r[3].strip())
    assert with_url >= 320, f"only {with_url} symbols carry doc URLs"


def test_17_known_fixed_symbols_have_urls(plugin_root):
    text = (plugin_root / "refs/nuke-17.0/symbol_map.tsv").read_text()
    for sym, frag in [("MultiArray_KnobI", "MultiArray__KnobI.html"),
                      ("IRange", "structDD_1_1Image_1_1IRange.html")]:
        line = next(r for r in text.splitlines() if r.startswith(sym + "\t"))
        assert frag in line, f"{sym}: expected {frag} in: {line}"


def test_17_parser_gap_symbols_are_indexed(plugin_root):
    symbols = {r[0] for r in rows_of(plugin_root, "nuke-17.0")}
    for sym in ("RefCountedPtr", "rTriangle", "Knob::cstring"):
        assert sym in symbols, f"{sym} missing from regenerated index"


def test_versions_md_documents_every_shipped_dir(plugin_root):
    doc = (plugin_root / "refs" / "VERSIONS.md").read_text()
    for ver in VERSIONS:
        assert ver in doc


@pytest.mark.parametrize("ver", VERSIONS)
def test_symbol_map_and_index_md_agree(plugin_root, ver):
    tsv_syms = {r[0] for r in rows_of(plugin_root, ver)}
    md = (plugin_root / "refs" / ver / "ndk_index.md").read_text()
    md_syms = {ln.split("`")[1] for ln in md.splitlines() if ln.startswith("| `")}
    assert tsv_syms == md_syms


@pytest.mark.skipif(os.environ.get("NUKE_CONTEXT_NET_TESTS") != "1",
                    reason="network test; set NUKE_CONTEXT_NET_TESTS=1 to run")
@pytest.mark.parametrize("ver", VERSIONS)
def test_sampled_doc_urls_resolve(plugin_root, ver):
    urls = [r[3] for r in rows_of(plugin_root, ver) if r[3].strip()]
    for url in random.Random(0).sample(urls, min(10, len(urls))):
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=15) as resp:
            assert resp.status == 200, url
