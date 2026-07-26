"""Every shipped NDK example must compile against the real NDK.

The corpus is teaching material -- an example that does not build teaches the
wrong thing. This is the standing guarantee behind the "compile-verified" label
on the NDK examples. Blink/Python examples carry an "unverified (no license)"
label instead and are checked for invented APIs elsewhere.
"""
import importlib.util
import shutil
import subprocess
import sys

import pytest

REPO = __import__("pathlib").Path(__file__).resolve().parent.parent
NDK_EXAMPLES = REPO / "plugins" / "nuke-context" / "examples" / "ndk"


def load_detect(tools_root):
    p = tools_root / "nuke_detect.py"
    spec = importlib.util.spec_from_file_location("nuke_detect", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["nuke_detect"] = mod
    spec.loader.exec_module(mod)
    return mod


def ndk_examples():
    return sorted(NDK_EXAMPLES.glob("*.cpp"))


def test_there_is_an_ndk_corpus():
    assert ndk_examples(), "no NDK examples to verify"


@pytest.mark.skipif(shutil.which("cmake") is None, reason="cmake not installed")
@pytest.mark.parametrize("example", ndk_examples(), ids=lambda p: p.name)
def test_ndk_example_compiles(plugin_root, tools_root, tmp_path, example):
    installs = load_detect(tools_root).find_installs()
    if not installs:
        pytest.skip("no Nuke install found")
    inst = installs[-1]

    (tmp_path / "src" / "ops").mkdir(parents=True)
    shutil.copy(example, tmp_path / "src" / "ops" / example.name)
    name = example.stem
    (tmp_path / "CMakeLists.txt").write_text(
        (plugin_root / "examples" / "ndk" / "CMakeLists.txt.example")
        .read_text()
        .replace("@PROJECT@", name)
        .replace("@NUKE_CMAKE_DIR@", str(inst.cmake_dir)))

    cfg = subprocess.run(["cmake", "-S", str(tmp_path), "-B", str(tmp_path / "build")],
                         capture_output=True, text=True)
    assert cfg.returncode == 0, f"{example.name} configure:\n{cfg.stdout}{cfg.stderr}"
    b = subprocess.run(["cmake", "--build", str(tmp_path / "build")],
                       capture_output=True, text=True)
    assert b.returncode == 0, f"{example.name} build:\n{b.stdout}{b.stderr}"
    # a loadable bundle, not just an object file
    dylib = tmp_path / "build" / f"{name}.dylib"
    assert dylib.is_file(), f"{example.name} produced no plugin"


def test_ndk_examples_declare_what_they_teach():
    """Each example is teaching material: it must say what pattern it teaches
    and that it is original, in a header comment."""
    for ex in ndk_examples():
        head = ex.read_text()[:600].lower()
        assert "teaches:" in head, f"{ex.name}: no 'Teaches:' header"
        assert "original" in head, f"{ex.name}: does not state it is original"
