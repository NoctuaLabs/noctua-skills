# CLAUDE.md — Noctua Skills

Project-level guidance for Claude Code (and any agent that reads `CLAUDE.md`) when working **on this repo itself** — i.e. maintaining the AI-agent skills in `skills/`. For end-user game-dev guidance, see [AGENTS.md](AGENTS.md) and the skill at [`skills/noctua-unity-sdk/SKILL.md`](skills/noctua-unity-sdk/SKILL.md).

## Repo layout

```
.
├── AGENTS.md                         # Cross-tool entry point (Cursor, Codex, Aider, etc.)
├── README.md                         # Install instructions for end users
├── LICENSE                           # MIT
├── commands/
│   └── noctua-unity-sdk.md           # Claude Code slash command (/noctua-unity-sdk)
├── skills/
│   └── noctua-unity-sdk/
│       ├── SKILL.md                  # Skill manifest (frontmatter + quickstart + routing table)
│       └── references/               # 22 topic-scoped reference files loaded on demand
└── mcp/                              # noctua-sdk-mcp — live MCP server (Python + FastMCP)
    ├── server.py                     # FastMCP entrypoint, auto-registers tools
    ├── server_types.py               # SkillRef / ApiModule / DtoFile dataclasses
    ├── sources/                      # upstream fetcher + per-domain tool implementations
    ├── pyproject.toml · Dockerfile · railway.toml
    └── README.md                     # connect / self-host / deploy instructions
```

## MCP server (`mcp/`)

The MCP server in [`mcp/`](mcp/) serves the same skill content **and** live SDK metadata over HTTP so game devs never have to re-install on each release. Tools fall into three groups:

1. **Skill content** — one `get_<topic>` tool per `skills/noctua-unity-sdk/references/*.md`, fetched live from this repo's `main` branch.
2. **SDK metadata** — `get_sdk_version`, `get_changelog`, `get_native_dependencies`, `get_skadnetwork_ids` (parsed from `noctua-unity-sdk-upm`).
3. **C#-parsed API surface** — `list_api_modules`, `get_api_reference(module)`, `get_noctuagg_schema`, `get_error_codes` (regex over the upstream C#; these are canonical and never drift).

When a new `references/<topic>.md` lands, append a row to `SKILL_REFS` in [`mcp/sources/skill_refs.py`](mcp/sources/skill_refs.py) and the tool auto-registers on the next restart. When the upstream SDK adds a new facade module, add an entry to `API_MODULES` in [`mcp/sources/api_surface.py`](mcp/sources/api_surface.py). When Noctua restructures DTO file paths, update `NOCTUAGG_DTOS` in the same file.

## What this skill is

Ships AI-agent guidance for integrating the **Noctua Games Unity SDK** (`com.noctuagames.sdk`) into Unity 2022.3.62f2+ projects. Targets SDK **v0.109.0**.

## Sources of truth (in priority order)

When making any change to the skill, verify against — and cite — these:

1. **Official docs:** https://docs.noctua.gg/sdk (API reference, per-module pages) and https://docs.noctua.gg/docs (tutorials).
2. **Open-source UPM repo:** https://github.com/NoctuaLabs/noctua-unity-sdk-upm (default branch `main`). Most useful paths:
   - `Runtime/View/*` — public facade classes (`Noctua.cs`, `NoctuaAuthentication.cs`, etc.)
   - `Runtime/Presenter/*` — services (`MediationManager.cs`, `NoctuaIAPService.cs`, `ExperimentManager.cs`, `NativeCrashForwarder.cs`, etc.)
   - `Runtime/Model/DTOs/*` — `noctuagg.json` schema (`GlobalConfig.cs`, `NoctuaConfig.cs`, `AdjustConfig.cs`, `FirebaseConfig.cs`, `FacebookConfig.cs`, `CoPublisherConfig.cs`, `GameServiceModels.cs`)
   - `Runtime/Model/Entities/NoctuaException.cs` — error codes
   - `Editor/Build/BuildPostProcessor.cs` — iOS/Android build patches (SKAdNetworks, plist, manifest)
   - `Editor/Dependencies/NativePluginDependencies.xml` — version pins
   - `CHANGELOG.md` — release notes; check `[Unreleased]` for surface added since the last tag
   - `package.json` — SDK version + Unity floor
3. **Repo source files** — when official docs don't cover something or you suspect docs lag the source, read the C# directly via `https://raw.githubusercontent.com/NoctuaLabs/noctua-unity-sdk-upm/main/<path>`.

`gh` CLI is not installed locally — use `curl` against the GitHub REST and raw content APIs.

## Golden rules for editing the skill

1. **Never invent APIs.** Every `Noctua.*` method, property, event, config field, and type listed in the skill must exist in either docs.noctua.gg/sdk or the repo source. If you can't verify it, don't add it.
2. **Always cite sources.** Each `references/*.md` file opens with a `> **Sources**` block linking the matching docs.noctua.gg page + repo file(s). Maintain this — when adding new content, extend the Sources block.
3. **`noctuagg.json` schema is canonical at the DTOs**, not the docs. The DTOs in `Runtime/Model/DTOs/` are the deserializer's input contract. If a field isn't there, `Newtonsoft` silently ignores it — flag it as not real.
4. **Prefer official docs URL over deep code links** for end-user references. Use repo links (`Runtime/...`) when the question is "where does this live?" or for type/field details that aren't in the docs.
5. **Keep reference files small and topic-scoped** (200–400 lines typical). When a new module is added by the SDK, prefer a new file over bloating an existing one. The agent loads only what it needs.
6. **Keep version numbers honest:**
   - SDK version: from `package.json`
   - Unity LTS: team policy is **2022.3.62f2+**, even though `package.json` says `2021.3` (UPM only enforces a major-version floor)
   - Native deps: from `Editor/Dependencies/NativePluginDependencies.xml`
   - SKAdNetwork count: grep `Editor/Build/BuildPostProcessor.cs` for `skadnetwork`

## Common workflows

### Bumping the SDK version

When Noctua ships a new SDK release:

1. Read `https://raw.githubusercontent.com/NoctuaLabs/noctua-unity-sdk-upm/main/CHANGELOG.md` — focus on the new tag.
2. Update version frontmatter in:
   - `skills/noctua-unity-sdk/SKILL.md` (description + body)
   - `commands/noctua-unity-sdk.md`
   - `skills/noctua-unity-sdk/references/installation.md` (UPM URL fragment)
   - `README.md` (top table)
   - `AGENTS.md` header
3. For each new feature/changed API in the changelog, locate the matching reference file and update.
4. Re-run the verification grep (see "Verifying changes" below).
5. Commit with `docs(noctua-unity-sdk): bump to vX.Y.Z` and a body listing what changed.

### Adding a new reference file

1. Create `skills/noctua-unity-sdk/references/<topic>.md` with a `> **Sources**` callout at the top (docs.noctua.gg link + repo file links).
2. Add a row to the routing table in `SKILL.md` (`## When to load which reference`).
3. Cross-link from related existing files where it makes sense.
4. Verify all intra-skill links resolve (no broken `[label](file.md#anchor)`).

### Auditing the skill against the upstream

The skill should never drift silently from the SDK. To audit:

```sh
# 1. Pull the canonical version + last few changelog entries
curl -sL https://raw.githubusercontent.com/NoctuaLabs/noctua-unity-sdk-upm/main/package.json
curl -sL https://raw.githubusercontent.com/NoctuaLabs/noctua-unity-sdk-upm/main/CHANGELOG.md | head -120

# 2. Grep for known-stale tokens
grep -rn "google_play\|app_store\|HttpLog\.Entries\|nativeInternalTrackerEnabled" skills/ commands/
```

Recent representative audits found: hallucinated APIs (`Noctua.SetEventSender`, `IAP.Init()` as public, `IAA.IAAResponse` as public), wrong enum values (`PaymentType.google_play` should be `playstore`), wrong type fields (`Player.Picture` is `AvatarUrl`), wrong return types (`AppUpdateResult` is an enum, not a struct), and stale repo paths (`Runtime/Core/Logging/NoctuaException.cs` should be `Runtime/Model/Entities/NoctuaException.cs`). Hunt for these patterns when reviewing PRs.

## Verifying changes

Before committing, run:

```sh
# Known-bad tokens that have appeared in past audits — must return zero
grep -rn "AdColor[^y]\|noctua\.is_sandbox\|HttpLog\.Entries\|DebugMonitor\.Entries\|nativeInternalTrackerEnabled\|noctuagames/noctua-sdk-unity-upm\.git\|Runtime/Core/Logging/NoctuaException\|Runtime/Inspector/HttpInspectorLog\|Runtime/Inspector/TrackerDebugMonitor" skills/ commands/

# Source-link coverage — every reference file should have at least one docs.noctua.gg URL
for f in skills/noctua-unity-sdk/references/*.md; do
  grep -q "docs\.noctua\.gg" "$f" || echo "MISSING SOURCE LINK: $f"
done
```

## Style

- Markdown only. No HTML except `<details>` summaries when content is genuinely optional.
- `csharp` fenced blocks for code samples. Always include the `using` lines for non-obvious types.
- Tables for enum values, fields, and routing — easier for agents to parse than prose.
- Lead each reference file with a one-sentence purpose, then the `> **Sources**` callout, then content.
- US English. Lowercase event/field names match the C# casing exactly (`OnPurchaseDone`, not `onPurchaseDone`).
- No emojis in skill content.

## Commit conventions

This repo uses conventional commits:

- `feat(noctua-unity-sdk): ...` — new public-facing capability
- `fix(noctua-unity-sdk): ...` — correctness fix (wrong API, wrong path, broken link)
- `docs(noctua-unity-sdk): ...` — clarification, new examples, source-link additions
- `chore: ...` — repo-level (LICENSE, README polish, .gitignore)

Attribution is disabled in `~/.claude/settings.json` — don't add `Co-Authored-By: Claude` unless explicitly requested.

## License

MIT — see [LICENSE](LICENSE). When pasting Noctua SDK code samples (e.g. canonical bootstrap), keep them short and illustrative; don't mirror large blocks of upstream source.
