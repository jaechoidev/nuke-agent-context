import importlib.util
import json
import pathlib
import re
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent

# Nuke install directories look like: Nuke15.2v9, Nuke17.0v3, Nuke17.0v1-Beta.4.
# Beta installs are excluded everywhere -- their docs/headers may not match the
# released SDK the refs are pinned to.
_NUKE_DIR_RE = re.compile(r"Nuke\d+\.\d+v\d+$")


@pytest.fixture(scope="session")
def repo_root():
    """Repository root — the directory holding plugins/ and tools/."""
    return REPO


@pytest.fixture(scope="session")
def plugin_root():
    return REPO / "plugins" / "nuke-context"


@pytest.fixture(scope="session")
def tools_root():
    return REPO / "tools"


# (the `marketplace` fixture is gone with the marketplace manifest — the
# archived repo is deliberately not installable)


def _load_nuke_detect():
    """Import tools/nuke_detect.py if it exists (Task 2 ports it); else None."""
    path = REPO / "tools" / "nuke_detect.py"
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("nuke_detect", path)
    mod = importlib.util.module_from_spec(spec)
    # Register before exec: dataclasses resolves cls.__module__ via sys.modules.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _entry(root: pathlib.Path) -> dict:
    return {
        "root": root,
        "headers": root / "Documentation" / "NDKExamples" / "include" / "DDImage",
        "doxygen": root / "Documentation" / "NDKExamples" / "Plugins",
        "pydocs": root / "Documentation" / "PythonDevGuide" / "Nuke",
    }


@pytest.fixture(scope="session")
def nuke_installs():
    """Every non-beta Nuke install with DDImage headers, oldest first.

    Ordered numerically, not lexically -- "Nuke9.0v8" precedes "Nuke17.0v3".
    Prefers tools/nuke_detect.py for detection; before Task 2 ports it, falls
    back to globbing /Applications directly. Empty list when nothing is found;
    tests that need installs must skip when the list is empty.
    """
    detect = _load_nuke_detect()
    if detect is not None:
        roots = [i.root for i in detect.find_installs()]
    else:
        roots = sorted(
            (r for r in pathlib.Path("/Applications").glob("Nuke*")
             if r.is_dir() and _NUKE_DIR_RE.match(r.name)),
            key=lambda r: [int(d) for d in re.findall(r"\d+", r.name)])
    out = []
    for root in roots:
        if "Beta" in root.name:
            continue
        entry = _entry(root)
        if entry["headers"].is_dir() and any(entry["headers"].glob("*.h")):
            out.append(entry)
    return out
