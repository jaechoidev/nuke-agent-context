import importlib.util
import json
import subprocess
import sys


def load(tools_root):
    p = tools_root / "nuke_detect.py"
    spec = importlib.util.spec_from_file_location("nuke_detect", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["nuke_detect"] = mod
    spec.loader.exec_module(mod)
    return mod


def make_install(root, version, python="python3.11", headers=True, binary=True,
                 cmake=True, examples=True):
    """Build a synthetic Nuke install tree under `root` for hermetic tests.

    headers=True  -> DDImage/ with Op.h;  headers="empty" -> DDImage/ with no
    .h files (a header-stripped install);  headers=False -> no DDImage/ at all.
    """
    d = root / f"Nuke{version}"
    macos = d / f"Nuke{version}.app" / "Contents" / "MacOS"
    macos.mkdir(parents=True)
    if binary:
        (macos / f"Nuke{version.split('v')[0]}").write_text("#!/bin/sh\n")
    if python:
        (macos / python).write_text("#!/bin/sh\n")
    if cmake:
        (macos / "cmake").mkdir()
        (macos / "cmake" / "NukeConfig.cmake").write_text("# stub\n")
    ndk = d / "Documentation" / "NDKExamples"
    ndk.mkdir(parents=True)
    if examples:
        (ndk / "examples").mkdir()
    if headers:
        inc = ndk / "include" / "DDImage"
        inc.mkdir(parents=True)
        if headers != "empty":
            (inc / "Op.h").write_text("// stub\n")
    return d


def test_finds_every_install_with_headers(tools_root, nuke_installs):
    mod = load(tools_root)
    assert nuke_installs, "fixture found no Nuke install with DDImage headers"
    found = mod.find_installs()
    assert len(found) == len(nuke_installs)
    assert [i.root for i in found] == [n["root"] for n in nuke_installs]
    assert [i.headers for i in found] == [n["headers"] for n in nuke_installs]


def test_derives_paths_that_exist(tools_root, nuke_installs):
    mod = load(tools_root)
    installs = mod.find_installs()
    assert len(installs) == len(nuke_installs) > 0
    for inst in installs:
        assert inst.app.is_dir(), f"{inst.version}: app bundle missing"
        assert inst.binary.is_file(), f"{inst.version}: binary missing"
        assert inst.python.is_file(), f"{inst.version}: python missing"
        assert (inst.cmake_dir / "NukeConfig.cmake").is_file()
        assert inst.headers.is_dir()
        assert inst.headers.name == "DDImage"
        assert (inst.headers / "Op.h").is_file(), f"{inst.version}: no DDImage/Op.h"
        assert inst.examples.is_dir(), f"{inst.version}: NDK examples missing"
        assert inst.examples.name == "examples"
        assert any(inst.examples.iterdir()), f"{inst.version}: examples dir empty"


def test_version_parsing(tools_root, nuke_installs):
    mod = load(tools_root)
    versions = {i.version for i in mod.find_installs()}
    assert len(versions) == len(nuke_installs) > 0
    # every version looks like 15.2v9
    for v in versions:
        assert mod.VERSION_RE.fullmatch(v), v
    # ...and the version is exactly the install directory name minus "Nuke"
    for inst in mod.find_installs():
        assert inst.root.name == f"Nuke{inst.version}"
        assert inst.major_minor == inst.version.split("v")[0]


def test_installs_ordered_oldest_first(tools_root, tmp_path):
    """Ordering must be numeric across major, minor and build number.

    Proven against a synthetic tree, NOT against the `nuke_installs` fixture:
    the fixture applies its own sort, so a shared lexical bug would make the two
    agree rather than disagree. This machine has no single-digit-major install,
    which is exactly the case that separates lexical from numeric ordering --
    Task 7 takes find_installs()[-1] as "newest", so lexically it would build
    against Nuke 9 on a facility machine that keeps a legacy version around.
    """
    mod = load(tools_root)
    # Created in scrambled order so a missing sort cannot pass by accident.
    for v in ("17.0v3", "9.0v8", "15.2v10", "9.10v1", "10.5v7", "9.9v1", "15.2v9"):
        make_install(tmp_path, v)
    got = [i.version for i in mod.find_installs(tmp_path)]
    assert got == ["9.0v8", "9.9v1", "9.10v1", "10.5v7",
                   "15.2v9", "15.2v10", "17.0v3"], got
    # The lexical order these directory names would produce is a different list,
    # so the assertion above genuinely discriminates between the two sorts.
    lexical = [d.name.replace("Nuke", "") for d in sorted(tmp_path.glob("Nuke*"))]
    assert lexical != got
    assert got[-1] == "17.0v3", "installs[-1] must be the newest install"


def test_json_cli(tools_root):
    r = subprocess.run(
        [sys.executable, str(tools_root / "nuke_detect.py"), "--json"],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert isinstance(data, list) and data
    assert {"version", "root", "binary", "headers", "cmake_dir"} <= set(data[0])


def test_to_dict_is_all_strings(tools_root):
    mod = load(tools_root)
    installs = mod.find_installs()
    assert installs, "no installs to convert"
    fields = {"version", "root", "app", "binary", "python", "cmake_dir",
              "headers", "examples"}
    for inst in installs:
        d = inst.to_dict()
        assert set(d) == fields
        assert all(isinstance(v, str) for v in d.values()), d
        assert json.loads(json.dumps(d))["root"] == str(inst.root)


def test_docs_only_install_is_rejected(tools_root, tmp_path):
    """A Documentation-only tree (no DDImage headers) is not a usable install.

    `Nuke9.9v1-Beta.4` mirrors the real beta on disk and is rejected on two
    independent grounds (bad name, no headers); `Nuke9.9v8` isolates the header
    guard alone, so this test still fails if only one of the two checks breaks.
    """
    mod = load(tools_root)
    good = make_install(tmp_path, "9.9v9")
    beta = make_install(tmp_path, "9.9v1-Beta.4", headers=False)
    docs_only = make_install(tmp_path, "9.9v8", headers=False)
    assert beta.is_dir() and docs_only.is_dir()  # the decoys really are on disk
    found = mod.find_installs(tmp_path)
    assert [i.root for i in found] == [good]
    assert {beta, docs_only}.isdisjoint({i.root for i in found})


def test_header_directory_without_headers_is_rejected(tools_root, tmp_path):
    """DDImage/ that exists but holds no .h files is a header-stripped install.

    Isolates the `any(headers.glob("*.h"))` half of the guard: every other
    negative case omits DDImage/ entirely and so is already caught by is_dir().
    """
    mod = load(tools_root)
    good = make_install(tmp_path, "9.9v9")
    stripped = make_install(tmp_path, "8.8v8", headers="empty")
    inc = stripped / "Documentation" / "NDKExamples" / "include" / "DDImage"
    assert inc.is_dir(), "the decoy must have a real DDImage directory"
    assert not any(inc.iterdir()), "...containing nothing at all"
    found = mod.find_installs(tmp_path)
    assert [i.root for i in found] == [good]


def test_beta_directory_name_does_not_match_version_pattern(tools_root):
    """The regex must reject Nuke17.0v1-Beta.4 outright, not truncate to 17.0v1."""
    mod = load(tools_root)
    assert mod.DIR_RE.match("Nuke17.0v1-Beta.4") is None
    assert mod.VERSION_RE.fullmatch("17.0v1-Beta.4") is None
    m = mod.DIR_RE.match("Nuke17.0v3")
    assert m is not None and m.group("version") == "17.0v3"


def test_rejects_incomplete_installs(tools_root, tmp_path):
    """Headers alone are not enough: the app, binary and python must be there."""
    mod = load(tools_root)
    good = make_install(tmp_path, "9.9v9")
    no_headers = make_install(tmp_path, "8.8v8", headers=False)
    no_binary = make_install(tmp_path, "7.7v7", binary=False)
    no_python = make_install(tmp_path, "6.6v6", python=None)
    (tmp_path / "NukeStudioNotAVersion").mkdir()
    (tmp_path / "Nuke9.9v9.txt").write_text("decoy file, not a directory\n")
    # A plain file whose name matches DIR_RE exactly -- only the is-a-directory
    # test distinguishes it from a real install root.
    (tmp_path / "Nuke5.5v5").write_text("decoy file, not a directory\n")
    for d in (no_headers, no_binary, no_python):
        assert d.is_dir()
    found = mod.find_installs(tmp_path)
    assert [i.root for i in found] == [good]


def test_rejects_installs_with_missing_cmake_or_examples(tools_root, tmp_path):
    """Every path an Install exposes must exist.

    Task 7 substitutes `cmake_dir` into a CMake template and `examples` into the
    generated CLAUDE.md, so a derived-but-dangling path surfaces far from its
    cause. Each decoy here is complete except for one of the two, which isolates
    the two checks from each other and from the headers/binary/python guards.
    """
    mod = load(tools_root)
    good = make_install(tmp_path, "9.9v9")
    no_cmake = make_install(tmp_path, "8.8v8", cmake=False)
    no_examples = make_install(tmp_path, "7.7v7", examples=False)
    assert not (no_cmake / "Nuke8.8v8.app" / "Contents" / "MacOS" / "cmake").exists()
    assert (no_cmake / "Documentation" / "NDKExamples" / "examples").is_dir()
    assert not (no_examples / "Documentation" / "NDKExamples" / "examples").exists()
    assert (no_examples / "Nuke7.7v7.app" / "Contents" / "MacOS" / "cmake").is_dir()
    found = mod.find_installs(tmp_path)
    assert [i.root for i in found] == [good]
    assert found[0].cmake_dir.is_dir() and found[0].examples.is_dir()


def test_search_root_is_overridable(tools_root, tmp_path):
    """No hard-coded path: --search-root and the kwarg both retarget the scan."""
    mod = load(tools_root)
    root = make_install(tmp_path, "9.9v9", python="python3.12")
    installs = mod.find_installs(search_root=tmp_path)
    assert len(installs) == 1
    inst = installs[0]
    macos = root / "Nuke9.9v9.app" / "Contents" / "MacOS"
    ndk = root / "Documentation" / "NDKExamples"
    assert inst.version == "9.9v9"
    assert inst.major_minor == "9.9"
    assert inst.root == root
    assert inst.app == root / "Nuke9.9v9.app"
    assert inst.binary == macos / "Nuke9.9"
    assert inst.python == macos / "python3.12"
    assert inst.cmake_dir == macos / "cmake"
    assert inst.headers == ndk / "include" / "DDImage"
    assert inst.examples == ndk / "examples"

    r = subprocess.run(
        [sys.executable, str(tools_root / "nuke_detect.py"),
         "--json", "--search-root", str(tmp_path)],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert [d["version"] for d in data] == ["9.9v9"]
    assert data[0]["root"] == str(tmp_path / "Nuke9.9v9")


def test_picks_numerically_newest_python(tools_root, tmp_path):
    """When an install ships several interpreters, pick the highest version.

    Guards a lexical-sort trap: sorted() ranks "python3.9" above "python3.10".
    """
    root = make_install(tmp_path, "9.9v9", python="python3.9")
    macos = root / "Nuke9.9v9.app" / "Contents" / "MacOS"
    for extra in ("python3.10", "python3.11"):
        (macos / extra).write_text("#!/bin/sh\n")
    assert len(list(macos.glob("python3.[0-9]*"))) == 3
    mod = load(tools_root)
    installs = mod.find_installs(tmp_path)
    assert len(installs) == 1
    assert installs[0].python.name == "python3.11"


def test_ignores_non_interpreters_matching_the_python_glob(tools_root, tmp_path):
    """`python3.[0-9]*` also matches tooling, which must never be selected.

    python3.12-config outranks the real python3.11 on the numeric key, and
    python3.11-config *ties* with it -- so the tie would break on arbitrary glob
    order. The python3.13 directory is the same trap one level up: a name that
    parses as an interpreter but cannot be executed.
    """
    root = make_install(tmp_path, "9.9v9", python="python3.11")
    macos = root / "Nuke9.9v9.app" / "Contents" / "MacOS"
    for decoy in ("python3.11-config", "python3.11m", "python3.12-config"):
        (macos / decoy).write_text("#!/bin/sh\n")
    (macos / "python3.13").mkdir()
    assert len(list(macos.glob("python3.[0-9]*"))) == 5  # 1 real + 4 decoys
    mod = load(tools_root)
    installs = mod.find_installs(tmp_path)
    assert len(installs) == 1
    assert installs[0].python.name == "python3.11"
    assert installs[0].python.is_file()


def test_empty_search_root_reports_failure(tools_root, tmp_path):
    """Human-readable mode must exit non-zero when nothing is found."""
    mod = load(tools_root)
    assert mod.find_installs(tmp_path) == []
    r = subprocess.run(
        [sys.executable, str(tools_root / "nuke_detect.py"),
         "--search-root", str(tmp_path)],
        capture_output=True, text=True)
    assert r.returncode != 0
    assert "no usable nuke install" in r.stderr.lower(), r.stderr


def test_human_readable_output_lists_every_install(tools_root, nuke_installs):
    mod = load(tools_root)
    installs = mod.find_installs()
    assert len(installs) == len(nuke_installs) > 0
    r = subprocess.run(
        [sys.executable, str(tools_root / "nuke_detect.py")],
        capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    assert len(lines) == len(installs)
    for line, inst in zip(lines, installs):
        assert line.startswith(inst.version)
        assert str(inst.root) in line
        assert inst.python.name in line
