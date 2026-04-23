# AGENTS.md — Noctua Unity SDK

This file briefs any AI coding agent (Cursor, Codex CLI, Aider, Copilot, Claude Code, etc.) on how to help a game developer integrate the **Noctua Unity SDK**.

**SDK version targeted:** 0.109.0 · **Unity:** 2022.3.62f2+ (LTS) · **Platforms:** Android, iOS

## When this applies

Activate this guidance when the user mentions any of:

- "Noctua SDK", "Noctua Unity SDK", "com.noctuagames.sdk"
- `noctuagg.json`, `Noctua.InitAsync`, `NoctuaException`
- `Noctua.Auth`, `Noctua.IAP`, `Noctua.IAA`, `Noctua.Event`, `Noctua.Platform`, `Noctua.App`
- Integrating Noctua Games analytics, auth, IAP, or ads into a Unity project

## Golden rules

1. **Never invent APIs.** Every `Noctua.*` method, property, and event listed in the references is verified against SDK source. If the user asks for something not documented here, say so and point to the SDK source file — don't guess.
2. **`noctuagg.json` is mandatory** and must live at `Assets/StreamingAssets/noctuagg.json`. Without it `Noctua.InitAsync()` throws `NoctuaException(NoctuaErrorCode.Application, ...)`.
3. **`Noctua.InitAsync()` is awaited once** in the game's bootstrap (usually a Splash scene). Wire event callbacks (`Noctua.OnInitSuccess`, `Noctua.Auth.OnAccountChanged`, `Noctua.IAP.OnPurchaseDone`) **before** calling `InitAsync`.
4. **All async APIs return `UniTask`** (`Cysharp.Threading.Tasks`). Always wrap calls in `try { ... } catch (NoctuaException nex) { ... } catch (Exception e) { ... }`.
5. **Don't call `Debug.Log`** — the SDK uses its own `ILogger`. Game code can use `Debug.Log` normally, but SDK-layer modifications must use `NoctuaLogger`.
6. **iOS and Android build post-processing is automatic.** The SDK rewrites `Info.plist` (SKAdNetworks, attribution endpoint) and `AndroidManifest.xml` (Facebook meta-data) via `BuildPostProcessor` — don't hand-edit these files.
7. **Ads (IAA)** require running `Noctua > Noctua Integration Manager > Recommended Setup` once after install. It installs AppLovin MAX 8.6.2 + AdMob 11.0.0 without conflicts.
8. **Maio is mutually exclusive** between AppLovin and AdMob — install it from one, never both. Run `Noctua > iOS > Fix CocoaPods Conflicts` on iOS if pod install fails.

## References (load on demand)

| Topic | File |
|---|---|
| Install via UPM, native deps | [skills/noctua-unity-sdk/references/installation.md](skills/noctua-unity-sdk/references/installation.md) |
| `noctuagg.json` full schema + template | [skills/noctua-unity-sdk/references/noctuagg-json.md](skills/noctua-unity-sdk/references/noctuagg-json.md) |
| `Noctua.InitAsync` bootstrap flow | [skills/noctua-unity-sdk/references/initialization.md](skills/noctua-unity-sdk/references/initialization.md) |
| `Noctua.Auth` — login, social, account | [skills/noctua-unity-sdk/references/authentication.md](skills/noctua-unity-sdk/references/authentication.md) |
| `Noctua.IAP` — products, purchase, pending | [skills/noctua-unity-sdk/references/iap.md](skills/noctua-unity-sdk/references/iap.md) |
| `Noctua.Event` — custom events, revenue | [skills/noctua-unity-sdk/references/events.md](skills/noctua-unity-sdk/references/events.md) |
| `Noctua.IAA` — ads (banner/interstitial/rewarded/app-open) | [skills/noctua-unity-sdk/references/iaa-ads.md](skills/noctua-unity-sdk/references/iaa-ads.md) |
| `Noctua.Platform` — locale, web content | [skills/noctua-unity-sdk/references/platform-features.md](skills/noctua-unity-sdk/references/platform-features.md) |
| `Noctua.App` — in-app review, updates | [skills/noctua-unity-sdk/references/app-manager.md](skills/noctua-unity-sdk/references/app-manager.md) |
| Android build setup | [skills/noctua-unity-sdk/references/android-setup.md](skills/noctua-unity-sdk/references/android-setup.md) |
| iOS build setup (SKAdNetworks, CocoaPods) | [skills/noctua-unity-sdk/references/ios-setup.md](skills/noctua-unity-sdk/references/ios-setup.md) |
| Editor menu tooling | [skills/noctua-unity-sdk/references/editor-tooling.md](skills/noctua-unity-sdk/references/editor-tooling.md) |
| Noctua Inspector (sandbox debug overlay) | [skills/noctua-unity-sdk/references/sandbox-inspector.md](skills/noctua-unity-sdk/references/sandbox-inspector.md) |
| Error handling (`NoctuaException`) | [skills/noctua-unity-sdk/references/error-handling.md](skills/noctua-unity-sdk/references/error-handling.md) |
| Session & engagement tracking | [skills/noctua-unity-sdk/references/session-tracking.md](skills/noctua-unity-sdk/references/session-tracking.md) |
| Full public API index | [skills/noctua-unity-sdk/references/api-reference.md](skills/noctua-unity-sdk/references/api-reference.md) |

## Minimal working sample

```csharp
using System;
using com.noctuagames.sdk;
using Cysharp.Threading.Tasks;
using UnityEngine;

public class NoctuaBootstrap : MonoBehaviour
{
    private async void Start()
    {
        Noctua.OnInitSuccess += () => Debug.Log("Noctua ready");
        Noctua.Auth.OnAccountChanged += u => Debug.Log($"Account: {u?.DisplayName}");
        Noctua.IAP.OnPurchaseDone     += o => Debug.Log($"Purchase done: {o.OrderId}");

        try
        {
            await Noctua.InitAsync();                  // loads noctuagg.json
            await Noctua.Auth.AuthenticateAsync();     // auto-login or show UI
        }
        catch (NoctuaException nex) { Debug.LogError($"Noctua {nex.ErrorCode}: {nex.Message}"); }
        catch (Exception e)         { Debug.LogError($"Init failed: {e.Message}"); }
    }
}
```

Place `noctuagg.json` (supplied by Noctua console) at `Assets/StreamingAssets/noctuagg.json` before pressing Play.
