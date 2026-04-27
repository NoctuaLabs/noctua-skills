---
name: noctua-unity-sdk
description: |
  Integrate the Noctua Games Unity SDK (v0.109.0, Unity 2022.3.62f2+ LTS) — UPM installation,
  noctuagg.json configuration at Assets/StreamingAssets, Noctua.InitAsync bootstrap,
  Auth / IAP / Event / IAA / Platform / App APIs, Android and iOS build post-processing
  (SKAdNetworks, AndroidManifest, CocoaPods), Noctua Integration Manager, and the
  sandbox Noctua Inspector. Use this skill when the user mentions "Noctua SDK",
  "noctuagg.json", "com.noctuagames.sdk", "Noctua.Auth/IAP/IAA/Event/Platform/App",
  "NoctuaException", or integrating Noctua Games into a Unity project.
---

# Noctua Unity SDK Integration Skill

You are helping a game developer integrate the **Noctua Games Unity SDK** (`com.noctuagames.sdk`) into a **Unity 2022.3.62f2+ (LTS)** project targeting Android and/or iOS. (`package.json` declares the technical minimum as 2021.3 for UPM resolution; 2022.3.62f2 is the team's supported floor.)

Every API, config field, and file path in this skill is verified against the SDK source. **Do not invent APIs.** If you need a detail that isn't covered here, say so and ask the user to share the relevant source file rather than guessing.

## Quickstart

1. **Install** via `Packages/manifest.json` → see [references/installation.md](references/installation.md)
2. **Create `Assets/StreamingAssets/noctuagg.json`** using the template in [references/noctuagg-json.md](references/noctuagg-json.md). Replace `clientId` and `gameId` with values from the Noctua console.
3. **Bootstrap** in a Splash scene:
   ```csharp
   using com.noctuagames.sdk;
   using Cysharp.Threading.Tasks;

   await Noctua.InitAsync();
   await Noctua.Auth.AuthenticateAsync();
   ```
   Full flow with event wiring in [references/initialization.md](references/initialization.md).
4. **Run `Noctua > Noctua Integration Manager > Recommended Setup`** once in the Unity editor to install the conflict-free AppLovin MAX + AdMob combo (only if ads are needed) — see [references/editor-tooling.md](references/editor-tooling.md).
5. **Build & run** — SDK auto-patches `Info.plist` (iOS SKAdNetworks, Adjust attribution) and `AndroidManifest.xml` (Facebook meta-data) at build time. No hand edits required.

## When to load which reference

| User task | Open reference |
|---|---|
| "How do I install it?" | [installation.md](references/installation.md) |
| "What goes in noctuagg.json?" | [noctuagg-json.md](references/noctuagg-json.md) |
| "How do I initialize?" / "Noctua init error" | [initialization.md](references/initialization.md) |
| Login / logout / switch account / social | [authentication.md](references/authentication.md) |
| Buy products / IAP pending / redeem codes | [iap.md](references/iap.md) |
| Track custom events / purchase / ad revenue | [events.md](references/events.md) |
| Show banner/interstitial/rewarded/app-open ad | [iaa-ads.md](references/iaa-ads.md) |
| `ad_loaded` / `ad_impression` / `wf_*` schema | [iaa-event-schema.md](references/iaa-event-schema.md) |
| Firebase IDs / Remote Config / Adjust attribution / push notifications | [firebase-and-push.md](references/firebase-and-push.md) |
| Announcement / customer service / locale | [platform-features.md](references/platform-features.md) |
| In-app review / app update | [app-manager.md](references/app-manager.md) |
| Android manifest / gradle / permissions | [android-setup.md](references/android-setup.md) |
| iOS Info.plist / SKAdNetworks / CocoaPods | [ios-setup.md](references/ios-setup.md) |
| Integration Manager / CocoaPods fixer | [editor-tooling.md](references/editor-tooling.md) |
| Debugging in sandbox (inspector overlay) | [sandbox-inspector.md](references/sandbox-inspector.md) |
| `NoctuaException`, error codes, try/catch | [error-handling.md](references/error-handling.md) |
| `session_*` events, engagement time | [session-tracking.md](references/session-tracking.md) |
| A/B experiments, segments, CPM floors | [experiments.md](references/experiments.md) |
| Full public API list | [api-reference.md](references/api-reference.md) |

## Sources to share with game devs

When a game dev asks "where does this come from?" or "do you have a link?", always include the matching official URL — don't paraphrase silently. The two canonical sources are:

- **Official docs:** https://docs.noctua.gg — root for both narrative guides (`/docs/...`) and the API reference (`/sdk/...`).
- **Open-source UPM repo:** https://github.com/NoctuaLabs/noctua-unity-sdk-upm — `Runtime/View/*` for facades, `Runtime/Presenter/*` for services, `Runtime/Model/DTOs/*` for `noctuagg.json` schema, `CHANGELOG.md` for release notes.

Per-topic landing pages (link these directly when answering):

| Topic | Official URL |
|---|---|
| Getting started / installation | https://docs.noctua.gg/docs/installation |
| Integration checklist | https://docs.noctua.gg/docs/integration-checklist |
| `Noctua` static facade | https://docs.noctua.gg/sdk/noctua |
| `Noctua.Auth` | https://docs.noctua.gg/sdk/auth |
| `Noctua.IAP` | https://docs.noctua.gg/sdk/iap |
| `Noctua.Event` | https://docs.noctua.gg/sdk/event |
| `Noctua.IAA` | https://docs.noctua.gg/sdk/iaa |
| IAA event tracking schema | https://docs.noctua.gg/sdk/iaa-event-tracking |
| `Noctua.App` | https://docs.noctua.gg/sdk/app |
| `Noctua.Platform.Content` | https://docs.noctua.gg/sdk/platform-content |
| `Noctua.Platform.Locale` | https://docs.noctua.gg/sdk/platform-locale |
| `Noctua.Firebase` (push, FCM, Remote Config) | https://docs.noctua.gg/sdk/noctua-firebase |
| Types reference | https://docs.noctua.gg/sdk/types |
| Unity tutorials (auth / IAP / IAA / tracking) | https://docs.noctua.gg/docs/unity/... (see SKILL.md table) |
| Noctua Inspector | https://docs.noctua.gg/docs/unity/debug-and-testing/noctua-inspector |
| Adjust attribution | https://docs.noctua.gg/docs/advanced/adjust-attribution |
| Firebase Remote Config | https://docs.noctua.gg/docs/advanced/firebase-remote-configs |
| Push notifications | https://docs.noctua.gg/docs/advanced/push-notifications |
| Pseudo user ID | https://docs.noctua.gg/docs/advanced/pseudo-user-id |

Each `references/*.md` file in this skill begins with a **Sources** block that links the matching official page and repo source file — copy those URLs into your replies when a game dev asks for the source.

## Golden rules

1. **Never hallucinate an API.** If it isn't in the references, check `Packages/com.noctuagames.sdk/Runtime/View/` in the user's project.
2. **`noctuagg.json` path is fixed**: `Assets/StreamingAssets/noctuagg.json`. Must exist before `InitAsync()`.
3. **Event callbacks must be wired before `InitAsync()`** — attaching after first fire misses the first event.
4. **All async SDK calls return `UniTask`** (`Cysharp.Threading.Tasks`). Wrap in `try { } catch (NoctuaException) { } catch (Exception) { }`.
5. **Do not manually emit** `watch_ads_Nx`, `taichi_*`, or `first_purchase` — the SDK auto-emits them and manual calls double-count.
6. **Ads require Integration Manager** (one-click Recommended Setup). Do not hand-edit `Packages/manifest.json` for ad adapters — use the menu.
7. **Maio conflict on iOS**: install Maio from only one mediator (AppLovin OR AdMob, not both). See [ios-setup.md](references/ios-setup.md).
8. **Sandbox only**: `Noctua.HttpLog`, `Noctua.DebugMonitor`, `Noctua.Inspector` are `null` in production (gated by `noctuagg.json → noctua.sandboxEnabled`).

## Canonical bootstrap (copy this)

```csharp
using System;
using com.noctuagames.sdk;
using Cysharp.Threading.Tasks;
using UnityEngine;

public class NoctuaBootstrap : MonoBehaviour
{
    private async void Start()
    {
        Noctua.OnInitSuccess            += ()  => Debug.Log("Noctua init success");
        Noctua.Auth.OnAccountChanged    += u   => Debug.Log($"Account changed: {u?.Player?.Nickname ?? "signed out"}");
        Noctua.Auth.OnAccountDeleted    += p   => Debug.Log($"Account deleted: {p?.Id}");
        Noctua.IAP.OnPurchaseDone       += o   => Debug.Log($"Purchase done: {o.Id}");
        Noctua.IAP.OnPurchasePending    += o   => Debug.Log($"Purchase pending: {o.Id}");

        try
        {
            await Noctua.InitAsync();
            await Noctua.Auth.AuthenticateAsync();
        }
        catch (NoctuaException nex)
        {
            Debug.LogError($"NoctuaException {nex.ErrorCode}: {nex.Message}");
        }
        catch (Exception e)
        {
            Debug.LogError($"Noctua init failed: {e.Message}");
        }
    }
}
```
