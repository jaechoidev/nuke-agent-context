import json
import re


def test_marketplace_names_the_plugin(marketplace):
    plugins = {p["name"] for p in marketplace["plugins"]}
    assert "nuke-context" in plugins
    entry = next(p for p in marketplace["plugins"] if p["name"] == "nuke-context")
    assert entry["source"] == "./plugins/nuke-context"


def test_plugin_manifest_is_semver(plugin_root):
    m = json.loads((plugin_root / ".claude-plugin" / "plugin.json").read_text())
    assert m["name"] == "nuke-context"
    assert re.fullmatch(r"\d+\.\d+\.\d+", m["version"])


def test_manifest_versions_agree(marketplace, plugin_root):
    m = json.loads((plugin_root / ".claude-plugin" / "plugin.json").read_text())
    entry = next(p for p in marketplace["plugins"] if p["name"] == "nuke-context")
    assert entry["version"] == m["version"]


def test_no_hooks_or_commands_shipped(plugin_root):
    assert not (plugin_root / "hooks").exists()
    assert not (plugin_root / "commands").exists()
