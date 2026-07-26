"""The example->lesson index: routes the agent to the canonical Foundry pattern.

Grades against the real example files, not against another copy of the parser.
"""
import importlib.util
import subprocess
import sys


def load(tools_root):
    p = tools_root / "extract_examples_index.py"
    spec = importlib.util.spec_from_file_location("extract_examples_index", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["extract_examples_index"] = mod
    spec.loader.exec_module(mod)
    return mod


def examples_dir(nuke_installs):
    for i in nuke_installs:
        d = i["root"] / "Documentation" / "NDKExamples" / "examples"
        if d.is_dir() and any(d.glob("*.cpp")):
            return d
    return None


def test_known_examples_classify_into_the_right_paradigm(tools_root, nuke_installs):
    d = examples_dir(nuke_installs)
    assert d, "no examples directory found"
    idx = load(tools_root).build_index(d)
    assert idx, "empty index"
    expected = {
        "Add.cpp": ("PixelIop", "2D per-pixel"),
        "Saturation.cpp": ("PixelIop", "2D per-pixel"),
        "DeepCrop.cpp": ("DeepFilterOp", "deep"),
        "GeoTriangle.cpp": ("SourceGeomOp", "3D geometry source"),
    }
    for name, (base, cat) in expected.items():
        assert name in idx, f"{name} not indexed"
        assert idx[name].base == base, f"{name}: base {idx[name].base}"
        assert idx[name].category == cat, f"{name}: category {idx[name].category}"


def test_every_example_carries_a_lesson(tools_root, nuke_installs):
    idx = load(tools_root).build_index(examples_dir(nuke_installs))
    assert idx
    for ex in idx.values():
        assert ex.lesson.strip(), f"{ex.file} has no lesson"


def test_contract_overrides_are_detected(tools_root, nuke_installs):
    """A PixelIop example must show it overrides pixel_engine -- that mapping is
    the point of the index (which contract method a pattern demonstrates)."""
    idx = load(tools_root).build_index(examples_dir(nuke_installs))
    assert "pixel_engine" in idx["Add.cpp"].overrides
    assert "in_channels" in idx["Add.cpp"].overrides


def test_no_html_leaks_into_the_purpose(tools_root, nuke_installs):
    """A few example files embed doxygen HTML in HELP; it must be cleaned, not
    shown to the agent as < p > noise."""
    idx = load(tools_root).build_index(examples_dir(nuke_installs))
    for ex in idx.values():
        assert "<" not in ex.help and ">" not in ex.help, f"{ex.file}: {ex.help!r}"


def test_cli_writes_both_artifacts_and_nothing_else(tools_root, nuke_installs, tmp_path):
    d = examples_dir(nuke_installs)
    out = tmp_path / "out"
    work = tmp_path / "work"
    work.mkdir()
    r = subprocess.run(
        [sys.executable, str(tools_root / "extract_examples_index.py"),
         str(d), "--out", str(out)],
        capture_output=True, text=True, cwd=work)
    assert r.returncode == 0, r.stderr
    assert (out / "examples_index.md").is_file()
    assert (out / "examples_map.tsv").is_file()
    assert "Teaches" in (out / "examples_index.md").read_text()
    assert list(work.iterdir()) == [], f"wrote outside --out: {list(work.iterdir())}"


def test_index_covers_a_broad_range_of_categories(tools_root, nuke_installs):
    """The teaching value is breadth: 2D, deep, 3D, IO, particles should all
    appear, not just the easy per-pixel ops."""
    idx = load(tools_root).build_index(examples_dir(nuke_installs))
    cats = {e.category for e in idx.values()}
    for expected in ("2D per-pixel", "2D general", "deep", "3D geometry source", "file IO"):
        assert expected in cats, f"missing category {expected}; have {sorted(cats)}"
