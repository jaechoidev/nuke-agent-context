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
    assert not [d for d in (plugin_root / "refs").iterdir()
                if "Beta" in d.name or "beta" in d.name]


def test_references_guides_present(plugin_root):
    for name in ["README.md", "ndk.md", "blink.md", "python.md",
                 "pyside-panels.md", "tool-architecture.md"]:
        assert (plugin_root / "references" / name).is_file()


def test_tools_are_outside_plugin(repo_root, plugin_root):
    assert (repo_root / "tools" / "extract_ndk_index.py").is_file()
    assert not (plugin_root / "scripts").exists()
