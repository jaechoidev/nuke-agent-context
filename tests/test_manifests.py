import json
import re


def test_no_marketplace_manifest_shipped(repo_root):
    """Archived: the repo must not be an installable marketplace. The plugin
    manifest stays so researchers can load it via --plugin-dir."""
    assert not (repo_root / ".claude-plugin" / "marketplace.json").exists()


def test_plugin_manifest_is_semver(plugin_root):
    m = json.loads((plugin_root / ".claude-plugin" / "plugin.json").read_text())
    assert m["name"] == "nuke-context"
    assert re.fullmatch(r"\d+\.\d+\.\d+", m["version"])


def test_no_hooks_or_commands_shipped(plugin_root):
    assert not (plugin_root / "hooks").exists()
    assert not (plugin_root / "commands").exists()
