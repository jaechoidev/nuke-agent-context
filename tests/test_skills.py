"""Skill content gates.

Skills are the plugin's behavioural layer: these tests pin the frontmatter
contract Claude Code actually reads, and the specific claims each skill must
carry (the three-tier lookup rule, verify-before-use on community references,
grep-don't-read on the big indexes).
"""
import re

import pytest

# Parametrized from disk so Tasks 8-9's skills are covered the moment they land.
def skill_dirs(plugin_root):
    return sorted(p.name for p in (plugin_root / "skills").iterdir() if p.is_dir())


# Only these are real. `user-invocable` appears in no installed skill and is
# silently ignored, so a skill relying on it would behave unexpectedly.
VALID_FRONTMATTER = {"name", "description", "allowed-tools"}

MODEL_SKILLS = ["nuke-python-model", "nuke-ndk-model", "nuke-blink-model"]


def frontmatter(path):
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path} has no YAML frontmatter"
    fields = {}
    for line in m.group(1).splitlines():
        km = re.match(r"^([\w-]+):\s*(.*)$", line)
        if km:
            fields[km.group(1)] = km.group(2)
    return fields, text[m.end():]


def test_expected_skills_ship(plugin_root):
    names = skill_dirs(plugin_root)
    for required in ["nuke-api-lookup"] + MODEL_SKILLS:
        assert required in names
    for dropped in ["nuke-setup", "nuke-tdd"]:
        assert dropped not in names


def test_skills_have_valid_frontmatter(plugin_root):
    for skill in skill_dirs(plugin_root):
        fields, body = frontmatter(plugin_root / "skills" / skill / "SKILL.md")
        assert fields.get("name") == skill, f"name must match the directory: {fields}"
        assert fields.get("description"), f"{skill}: description drives skill selection"
        assert len(body.strip()) > 400, f"{skill}: body too thin to be useful"
        unknown = set(fields) - VALID_FRONTMATTER
        assert not unknown, f"{skill}: unrecognised frontmatter {sorted(unknown)}"
        d = fields["description"].lower()
        assert "use when" in d or "use whenever" in d, \
            f"{skill}: description states no trigger condition"


def test_no_skill_references_the_dropped_setup_layout(plugin_root):
    for skill in skill_dirs(plugin_root):
        body = (plugin_root / "skills" / skill / "SKILL.md").read_text()
        assert ".nuke-agent" not in body, f"{skill}: stale .nuke-agent path"
        assert "nuke-tdd" not in body, f"{skill}: references dropped nuke-tdd skill"


def test_lookup_skill_encodes_three_tier_rule(plugin_root):
    _, body = frontmatter(plugin_root / "skills" / "nuke-api-lookup" / "SKILL.md")
    for needle in ["WebFetch", "real header", "compiler"]:
        assert needle in body, f"three-tier rule incomplete: missing {needle!r}"
    assert "CLAUDE_PLUGIN_ROOT" in body


def test_lookup_skill_warns_against_anchoring_the_symbol_search(plugin_root):
    _, body = frontmatter(plugin_root / "skills" / "nuke-api-lookup" / "SKILL.md")
    assert "not** anchor" in body or "not anchor" in body.lower()
    assert "Op::Description" in body


def test_lookup_skill_forbids_substituting_a_similar_symbol(plugin_root):
    _, body = frontmatter(plugin_root / "skills" / "nuke-api-lookup" / "SKILL.md")
    low = body.lower()
    assert "does not exist" in low
    assert "do not substitute" in low


def test_lookup_skill_has_version_selection_guidance(plugin_root):
    _, body = frontmatter(plugin_root / "skills" / "nuke-api-lookup" / "SKILL.md")
    assert "nearest older" in body.lower()


def test_lookup_skill_warns_docs_can_be_stale(plugin_root):
    _, body = frontmatter(plugin_root / "skills" / "nuke-api-lookup" / "SKILL.md")
    assert "GenericImagePlane" in body   # the verified stale-docs example


def test_lookup_skill_forbids_whole_file_reads(plugin_root):
    _, body = frontmatter(plugin_root / "skills" / "nuke-api-lookup" / "SKILL.md")
    assert "never read one" in body.lower() or "never read it whole" in body.lower()


@pytest.mark.parametrize("skill", MODEL_SKILLS)
def test_model_skills_point_to_field_guide_with_verify_rule(plugin_root, skill):
    body = (plugin_root / "skills" / skill / "SKILL.md").read_text()
    assert "references/" in body
    assert "verif" in body.lower()
    assert "what is true" in body      # the guide-routes/official-decides framing


def test_performance_skill_covers_core_principles(plugin_root):
    _, body = frontmatter(plugin_root / "skills" / "nuke-performance" / "SKILL.md")
    for needle in ["_request", "engine", "bbox", "hash", "devguide_map",
                   "eAccessPoint", "thread"]:
        assert needle in body, f"missing principle marker: {needle}"


def test_performance_skill_routes_not_duplicates(plugin_root):
    text = (plugin_root / "skills" / "nuke-performance" / "SKILL.md").read_text()
    assert len(text) < 12_000, "stays a routing skill, not a textbook"
    assert "devguide_map" in text     # depth comes from routed guide anchors


def test_performance_skill_requires_measurement(plugin_root):
    _, body = frontmatter(plugin_root / "skills" / "nuke-performance" / "SKILL.md")
    assert "measure" in body.lower()  # perf claims verified, not believed
