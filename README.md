# Noctua Skills

AI-agent skills for integrating Noctua Games SDKs. Currently ships one skill:

| Skill | Scope | Version targeted |
|---|---|---|
| [`noctua-unity-sdk`](skills/noctua-unity-sdk/SKILL.md) | Noctua Unity SDK integration (install, config, Auth, IAP, Events, IAA, build post-process) | SDK 0.109.0 / Unity 2022.3.62f2+ |

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
- [`skills/noctua-unity-sdk/references/`](skills/noctua-unity-sdk/references/) — one file per topic (installation, noctuagg.json schema, Auth/IAP/Events/IAA APIs, Android/iOS build setup, editor tooling, error handling). Agents load only what they need to keep context small.

Every API signature, config field, and file path is verified against the Noctua Unity SDK source — no hallucinations.

## Contributing

Issues and PRs welcome. When the Noctua Unity SDK ships a new version, update:

1. Version numbers in `skills/noctua-unity-sdk/SKILL.md` frontmatter and the installation reference.
2. Any API signatures that changed — cross-check against the SDK source files listed in the reference.
3. `skills/noctua-unity-sdk/references/api-reference.md` if the public surface changed.

## License

MIT — see [LICENSE](LICENSE).
