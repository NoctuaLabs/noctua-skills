---
description: Noctua Unity SDK integration helper — install, noctuagg.json, Auth / IAP / Events / IAA, Android + iOS build setup
---

Use the **noctua-unity-sdk** skill to help the user with: $ARGUMENTS

Load the skill manifest at `~/.claude/skills/noctua-unity-sdk/SKILL.md` and follow the `references/` files on demand. Do not invent APIs — everything documented there is verified against Noctua Unity SDK 0.109.0 source.

Quickstart context (for trivial requests):

- SDK: `com.noctuagames.sdk` v0.109.0, Unity 2022.3.62f2+ (LTS), Android + iOS
- Install: add to `Packages/manifest.json` — `"com.noctuagames.sdk": "https://github.com/NoctuaLabs/noctua-unity-sdk-upm.git#0.109.0"`
- Config: `Assets/StreamingAssets/noctuagg.json` (mandatory)
- Bootstrap: `await Noctua.InitAsync(); await Noctua.Auth.AuthenticateAsync();`
- Ads: run `Noctua > Noctua Integration Manager > Recommended Setup` once

If `$ARGUMENTS` is empty, present the table of contents from `SKILL.md` and ask which topic the user wants to dive into.

**Live data** — If the `noctua-sdk` MCP server is configured in this Claude Code instance, prefer its tools (`get_sdk_version`, `get_changelog`, `get_api_reference(module)`, `get_noctuagg_schema`, `get_error_codes`, `get_<topic>`) over the static skill content for any version-sensitive answer. They fetch live from upstream and never drift. See [`mcp/README.md`](../mcp/README.md) for the connection URL.

**Always cite sources.** When answering a game-dev question, include the matching `https://docs.noctua.gg/...` URL (and a `https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/...` repo link when the answer comes from source code). The "Sources" block at the top of each `references/*.md` file lists the canonical pair — copy those URLs into your reply rather than paraphrasing without attribution.
