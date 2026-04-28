# Noctua Skills

AI-agent skills for integrating Noctua Games SDKs. Two ways to consume:

| Surface | Scope | Version targeted |
|---|---|---|
| [`noctua-unity-sdk`](skills/noctua-unity-sdk/SKILL.md) (skill) | Noctua Unity SDK integration — install, `noctuagg.json`, Auth, IAP, Events, IAA + canonical ad-event schema, Firebase / Adjust attribution / push notifications, experiments & CPM floors, Android + iOS build post-processing, Noctua Inspector | SDK 0.109.0 / Unity 2022.3.62f2+ |
| [`noctua-sdk-mcp`](mcp/README.md) (MCP server) | Same content but **served live**: every reference, the latest SDK version, changelog, native dep versions, SKAdNetwork list, and a C#-parsed API surface (`get_api_reference`, `get_noctuagg_schema`, `get_error_codes`) | Tracks `main` of the upstream SDK and this skill repo |

The skill is plain markdown with Claude-compatible YAML frontmatter — works in Claude Code, Claude.ai, the Claude Agent SDK, and other AI agents (Cursor, Codex CLI, Aider, Copilot) via the root [`AGENTS.md`](AGENTS.md) entry point. The MCP exposes the same content over a single HTTP URL so game devs never have to manually re-install on each SDK release.

## Install

### Claude Code (personal) — recommended

Clone once, then symlink both the skill **and** the slash command so you can invoke `/noctua-unity-sdk` directly (no need to type `/skills` first):

```sh
git clone git@github.com:NoctuaLabs/noctua-skills.git ~/src/noctua-skills

mkdir -p ~/.claude/skills ~/.claude/commands

# Skill (auto-triggers on Noctua-related prompts)
ln -s ~/src/noctua-skills/skills/noctua-unity-sdk        ~/.claude/skills/noctua-unity-sdk

# Slash command (invoke directly: /noctua-unity-sdk <your question>)
ln -s ~/src/noctua-skills/commands/noctua-unity-sdk.md   ~/.claude/commands/noctua-unity-sdk.md
```

Restart Claude Code. Usage:

- `/noctua-unity-sdk how do I add an IAP button?` — invokes the skill directly
- Or just mention "Noctua SDK" in chat — the skill auto-activates via its description triggers

### Claude Code (per-project)

Inside your Unity game repo:

```sh
git submodule add git@github.com:NoctuaLabs/noctua-skills.git .claude/vendor/noctua-skills
mkdir -p .claude/skills .claude/commands
ln -s ../vendor/noctua-skills/skills/noctua-unity-sdk      .claude/skills/noctua-unity-sdk
ln -s ../vendor/noctua-skills/commands/noctua-unity-sdk.md .claude/commands/noctua-unity-sdk.md
```

Now every teammate who opens the project in Claude Code gets `/noctua-unity-sdk` automatically.

### Cursor

Cursor reads from `.cursor/rules/` and also respects root `AGENTS.md`:

```sh
git submodule add git@github.com:NoctuaLabs/noctua-skills.git .cursor/vendor/noctua-skills
mkdir -p .cursor/rules
ln -s ../vendor/noctua-skills/skills/noctua-unity-sdk/SKILL.md .cursor/rules/noctua-unity-sdk.md
```

### Codex CLI, Aider, Copilot workspace

These tools read [`AGENTS.md`](AGENTS.md) at the project root:

```sh
git submodule add git@github.com:NoctuaLabs/noctua-skills.git .noctua-skills
cp .noctua-skills/AGENTS.md ./AGENTS.md
```

Or point at this repo as a source and let the tool load `AGENTS.md` directly.

### Live MCP server (no manual updates ever)

Skip the symlink/submodule dance entirely — run the MCP once on a LAN host, point every teammate's Claude Code at the SSE URL, and your agent always sees the latest content + live SDK metadata.

On one machine on the LAN:

```sh
cd noctua-skills/mcp
python -m venv .venv && source .venv/bin/activate
pip install -e .
python server.py sse        # 0.0.0.0:8000, endpoint /sse
```

In each teammate's Claude Code config:

```jsonc
{
  "mcpServers": {
    "noctua-sdk": {
      "type": "sse",
      "url": "http://<host-lan-ip>:8000/sse"
    }
  }
}
```

Tools include `get_sdk_version`, `get_changelog`, `get_api_reference(module)`, `get_noctuagg_schema`, `get_error_codes`, plus one `get_<topic>` per skill reference (call `list_topics` to discover them). Full self-hosting + Docker instructions in [`mcp/README.md`](mcp/README.md).

### Any other agent

Paste the contents of [`skills/noctua-unity-sdk/SKILL.md`](skills/noctua-unity-sdk/SKILL.md) (and the specific `references/*.md` file you need) into your system prompt or custom instructions.

## How it works

- [`skills/noctua-unity-sdk/SKILL.md`](skills/noctua-unity-sdk/SKILL.md) — the skill manifest. Short quickstart + an index pointing at detailed reference files.
- [`skills/noctua-unity-sdk/references/`](skills/noctua-unity-sdk/references/) — one file per topic (installation, `noctuagg.json` schema, Auth/IAP/Events/IAA APIs, IAA event schema, Firebase + push, experiments + CPM floors, Android/iOS build setup, editor tooling, Noctua Inspector, error handling, session tracking, full API reference). Agents load only what they need to keep context small.
- [`AGENTS.md`](AGENTS.md) — cross-tool entry point (Cursor / Codex CLI / Aider / Copilot).
- [`CLAUDE.md`](CLAUDE.md) — project memory for anyone working on **this repo** (maintaining the skill itself), not for game devs using it.

Every API signature, config field, type, and file path is verified against three sources of truth: the official docs at <https://docs.noctua.gg/sdk>, the open-source UPM repo at <https://github.com/NoctuaLabs/noctua-unity-sdk-upm>, and the C# DTOs. No hallucinations. Each reference file opens with a `> **Sources**` block linking the matching docs page and repo file(s) so the agent can cite them when answering.

## Updating

A `git push` to this repo updates the **remote** only — each game dev's local install needs to pull. Pick whichever update strategy matches how you installed the skill:

### Personal install (symlink to local clone) — recommended

The Claude Code symlink (`~/.claude/skills/noctua-unity-sdk` → your local clone) sees file changes immediately, so a single `git pull` is enough:

```sh
cd ~/src/noctua-skills && git pull --ff-only
```

To make this automatic, add either of the following:

**Option A — pull on every new shell** (`~/.zshrc` or `~/.bashrc`):

```sh
( cd ~/src/noctua-skills && git pull --quiet --ff-only origin main &>/dev/null & )
```

Each new terminal refreshes the clone in the background.

**Option B — daily cron** (`crontab -e`):

```cron
0 9 * * * cd ~/src/noctua-skills && git pull --ff-only origin main >/dev/null 2>&1
```

Pulls weekday mornings at 9am. Same idea works on Linux/macOS launchd.

### Per-project install (git submodule)

If you embedded the skill in your game repo as a submodule (the per-project Claude Code / Cursor pattern from above), bump the submodule pointer:

```sh
git submodule update --remote --merge .claude/vendor/noctua-skills
git commit -am "chore: bump noctua-skills"
```

To automate, add a workflow to your **game** repo (not this one) that opens a weekly bump PR:

```yaml
# .github/workflows/bump-noctua-skills.yml
name: Bump noctua-skills
on:
  schedule: [{cron: '0 9 * * 1'}]   # Mondays 09:00 UTC
  workflow_dispatch:
jobs:
  bump:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { submodules: recursive }
      - run: git submodule update --remote --merge .claude/vendor/noctua-skills
      - uses: peter-evans/create-pull-request@v6
        with:
          title: "chore: bump noctua-skills"
          branch: bot/bump-noctua-skills
          commit-message: "chore: bump noctua-skills"
```

The PR shows the changelog so reviewers can decide whether to merge.

### Pinned to a tag (deterministic builds)

For release branches or CI you may want the skill **frozen** to a specific commit. Tag releases of this repo (e.g. when the underlying Noctua SDK ships v0.110.0), then pin the submodule:

```sh
cd .claude/vendor/noctua-skills
git fetch --tags
git checkout v0.110.0
cd -
git commit -am "chore: pin noctua-skills to v0.110.0"
```

The skill won't move until you re-pin.

### Other install methods

- **Codex CLI / Aider / Copilot** (`cp AGENTS.md`): re-run the `cp` after `git pull`.
- **Pasted into a system prompt**: re-paste manually.

These methods are static copies — there's no symlink or submodule pointer to update.

## Contributing

Issues and PRs welcome. See [`CLAUDE.md`](CLAUDE.md) for the maintainer playbook (sources of truth, golden rules, common workflows, verification grep snippets). The short version — when the Noctua Unity SDK ships a new version:

1. Bump the SDK version in: `skills/noctua-unity-sdk/SKILL.md` frontmatter, `commands/noctua-unity-sdk.md`, `skills/noctua-unity-sdk/references/installation.md`, `README.md`, `AGENTS.md`.
2. Read the upstream `CHANGELOG.md` `[Unreleased]` block and update each affected reference file.
3. Cross-check API signatures against <https://docs.noctua.gg/sdk> and the C# source under `Runtime/View/`, `Runtime/Presenter/`, `Runtime/Model/DTOs/`.
4. Run the verification greps in [`CLAUDE.md`](CLAUDE.md) before committing.

## License

MIT — see [LICENSE](LICENSE).
