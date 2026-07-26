"""The README and setup doc are the product's front door - pin their claims."""


def test_readme_covers_the_essentials(repo_root):
    text = (repo_root / "README.md").read_text()
    for needle in ["/plugin marketplace add", "/plugin install nuke-context",
                   "--scope", "Testing your tools", "Deploying your tools",
                   "learn.foundry.com", "verify"]:
        assert needle in text, f"README missing: {needle}"


def test_readme_documents_permission_expectations(repo_root):
    text = (repo_root / "README.md").read_text().lower()
    assert "permission" in text


def test_readme_documents_team_install(repo_root):
    text = (repo_root / "README.md").read_text()
    assert "extraKnownMarketplaces" in text
    assert "enabledPlugins" in text


def test_readme_carries_the_eval_numbers(repo_root):
    text = (repo_root / "README.md").read_text()
    assert "2.1" in text and "70%" in text


def test_readme_claims_no_foundry_content(repo_root):
    low = (repo_root / "README.md").read_text().lower()
    assert "no foundry" in low or "ships no foundry" in low


def test_git_setup_doc_covers_all_platforms(plugin_root):
    text = (plugin_root / "docs" / "git-github-setup.md").read_text()
    for needle in ["xcode-select", "winget", "apt", "gh auth login",
                   "gh repo create", "git init"]:
        assert needle in text, f"setup doc missing: {needle}"


def test_git_setup_doc_protects_nuke_projects(plugin_root):
    text = (plugin_root / "docs" / "git-github-setup.md").read_text()
    assert "__pycache__" in text          # sane .gitignore for Nuke projects
    assert "--private" in text            # default-private first repo
