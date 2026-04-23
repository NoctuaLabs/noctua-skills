---
description: Noctua Unity SDK integration helper — install, noctuagg.json, Auth / IAP / Events / IAA, Android + iOS build setup
---

Use the **noctua-unity-sdk** skill to help the user with: $ARGUMENTS

Load the skill manifest at `~/.claude/skills/noctua-unity-sdk/SKILL.md` and follow the `references/` files on demand. Do not invent APIs — everything documented there is verified against Noctua Unity SDK 0.109.0 source.

Quickstart context (for trivial requests):

- SDK: `com.noctuagames.sdk` v0.109.0, Unity 2022.3.62f2+ (LTS), Android + iOS
- Install: add to `Packages/manifest.json` — `"com.noctuagames.sdk": "https://github.com/noctuagames/noctua-sdk-unity-upm.git#0.109.0"`
- Config: `Assets/StreamingAssets/noctuagg.json` (mandatory)
- Bootstrap: `await Noctua.InitAsync(); await Noctua.Auth.AuthenticateAsync();`
- Ads: run `Noctua > Noctua Integration Manager > Recommended Setup` once

If `$ARGUMENTS` is empty, present the table of contents from `SKILL.md` and ask which topic the user wants to dive into.
