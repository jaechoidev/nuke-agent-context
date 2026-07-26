# Git + GitHub for Nuke tool developers

You built a tool. This page gets it into version control and onto GitHub —
so you can undo mistakes, hand it to another artist, and install it at the
next studio. Fifteen minutes, once.

**Why bother:** history is undo for code. Every "it worked yesterday" becomes
`git diff`; every "send me your tool" becomes a URL. A tool that lives only in
your `~/.nuke` folder dies with that machine.

## 1. Install git

- **macOS** — either of:
  ```bash
  xcode-select --install        # Apple's command-line tools (includes git)
  brew install git              # or Homebrew, if you use it
  ```
- **Windows**:
  ```powershell
  winget install Git.Git
  ```
  (or download Git for Windows from git-scm.com)
- **Linux**:
  ```bash
  sudo apt install git          # Debian/Ubuntu
  sudo dnf install git          # Fedora/Rocky
  ```

Tell git who you are (goes into every commit):

```bash
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
```

## 2. Install the GitHub CLI (`gh`)

- macOS: `brew install gh`
- Windows: `winget install GitHub.cli`
- Linux: `sudo apt install gh` (or see cli.github.com for your distro)

## 3. Create a GitHub account and sign in

1. Create the account at github.com (enable two-factor auth when prompted —
   studios will expect it).
2. Connect the CLI to it:
   ```bash
   gh auth login
   ```
   Choose **GitHub.com → HTTPS → Login with a web browser** and follow the
   one-time code. That's the whole authentication story — no SSH keys needed
   to start.

## 4. Put your tool under version control

From the tool's directory:

```bash
git init
```

Create a `.gitignore` so renders and caches never enter history:

```gitignore
__pycache__/
*.pyc
*.nk~
*.autosave
renders/
build/
.DS_Store
```

Then the first commit:

```bash
git add .
git commit -m "feat: initial version of <toolname>"
```

## 5. First push — your tool gets a URL

```bash
gh repo create <toolname> --private --source . --push
```

`--private` means only you (and people you invite) can see it — flip to
public later if you want to share on Nukepedia. The command prints the URL;
that URL *is* your tool's home now.

## 6. The everyday loop

After each working change (the agent does this at verified milestones):

```bash
git add -u
git commit -m "fix: handle empty selection"
git push
```

To get your tool onto another machine: `gh repo clone <you>/<toolname>`.

---

That's everything. If any command errors, paste the error to the agent — the
fix is usually one line.
