# Noctua Skills

AI-agent skills for integrating Noctua Games SDKs. Currently ships one skill:

| Skill | Scope | Version targeted |
|---|---|---|
| [`noctua-unity-sdk`](skills/noctua-unity-sdk/SKILL.md) | Noctua Unity SDK integration — install, `noctuagg.json`, Auth, IAP, Events, IAA + canonical ad-event schema, Firebase / Adjust attribution / push notifications, experiments & CPM floors, Android + iOS build post-processing, Noctua Inspector | SDK 0.109.0 / Unity 2022.3.62f2+ |

The content is plain markdown with Claude-compatible YAML frontmatter, so it works in Claude Code, Claude.ai, the Claude Agent SDK, **and** other AI agents (Cursor, Codex CLI, Aider, Copilot) via the root [`AGENTS.md`](AGENTS.md) entry point.

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

### Any other agent

Paste the contents of [`skills/noctua-unity-sdk/SKILL.md`](skills/noctua-unity-sdk/SKILL.md) (and the specific `references/*.md` file you need) into your system prompt or custom instructions.

## How it works

- [`skills/noctua-unity-sdk/SKILL.md`](skills/noctua-unity-sdk/SKILL.md) — the skill manifest. Short quickstart + an index pointing at detailed reference files.
- [`skills/noctua-unity-sdk/references/`](skills/noctua-unity-sdk/references/) — one file per topic (installation, `noctuagg.json` schema, Auth/IAP/Events/IAA APIs, IAA event schema, Firebase + push, experiments + CPM floors, Android/iOS build setup, editor tooling, Noctua Inspector, error handling, session tracking, full API reference). Agents load only what they need to keep context small.
- [`AGENTS.md`](AGENTS.md) — cross-tool entry point (Cursor / Codex CLI / Aider / Copilot).
- [`CLAUDE.md`](CLAUDE.md) — project memory for anyone working on **this repo** (maintaining the skill itself), not for game devs using it.

Every API signature, config field, type, and file path is verified against three sources of truth: the official docs at <https://docs.noctua.gg/sdk>, the open-source UPM repo at <https://github.com/NoctuaLabs/noctua-unity-sdk-upm>, and the C# DTOs. No hallucinations. Each reference file opens with a `> **Sources**` block linking the matching docs page and repo file(s) so the agent can cite them when answering.

## Contributing

Issues and PRs welcome. See [`CLAUDE.md`](CLAUDE.md) for the maintainer playbook (sources of truth, golden rules, common workflows, verification grep snippets). The short version — when the Noctua Unity SDK ships a new version:

1. Bump the SDK version in: `skills/noctua-unity-sdk/SKILL.md` frontmatter, `commands/noctua-unity-sdk.md`, `skills/noctua-unity-sdk/references/installation.md`, `README.md`, `AGENTS.md`.
2. Read the upstream `CHANGELOG.md` `[Unreleased]` block and update each affected reference file.
3. Cross-check API signatures against <https://docs.noctua.gg/sdk> and the C# source under `Runtime/View/`, `Runtime/Presenter/`, `Runtime/Model/DTOs/`.
4. Run the verification greps in [`CLAUDE.md`](CLAUDE.md) before committing.

## License

MIT — see [LICENSE](LICENSE).
