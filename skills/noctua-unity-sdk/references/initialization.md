# Initialization

The SDK is initialized once per app lifetime, typically in a **Splash** scene before loading gameplay.

Source: `Packages/com.noctuagames.sdk/Runtime/View/Noctua.Initialization.cs`, `Assets/SplashScript.cs` (sample).

## Minimal bootstrap

```csharp
using System;
using com.noctuagames.sdk;
using Cysharp.Threading.Tasks;
using UnityEngine;

public class SplashScript : MonoBehaviour
{
    private async void Start()
    {
        try
        {
            await Noctua.InitAsync();
            await Noctua.Auth.AuthenticateAsync();
            // Now safe to load Home/Gameplay scene
        }
        catch (NoctuaException nex)
        {
            Debug.LogError($"Noctua {nex.ErrorCode}: {nex.Message}");
        }
        catch (Exception e)
        {
            Debug.LogError($"Noctua init error: {e.Message}");
        }
    }
}
```

## Wiring events BEFORE `InitAsync`

Events registered **after** `InitAsync` completes will miss early firings. Wire them first:

```csharp
Noctua.OnInitSuccess += OnNoctuaReady;

Noctua.Auth.OnAccountChanged  += OnAccountChanged;   // fires on login / logout / switch
Noctua.Auth.OnAccountDeleted  += OnAccountDeleted;   // fires when user deletes account

Noctua.IAP.OnPurchaseDone     += OnPurchaseDone;     // verified purchase
Noctua.IAP.OnPurchasePending  += OnPurchasePending;  // awaiting backend verification

await Noctua.InitAsync();
await Noctua.Auth.AuthenticateAsync();
```

Available events (see [authentication.md](authentication.md), [iap.md](iap.md) for full signatures):

| Event | Arg type | Fires when |
|---|---|---|
| `Noctua.OnInitSuccess` | `Action` | `InitAsync` completes without error |
| `Noctua.Auth.OnAccountChanged` | `Action<UserBundle>` | login, logout, account switch (arg can be null on logout) |
| `Noctua.Auth.OnAccountDeleted` | `Action<Player>` | User-initiated account deletion |
| `Noctua.IAP.OnPurchaseDone` | `Action<OrderRequest>` | Backend-verified purchase |
| `Noctua.IAP.OnPurchasePending` | `Action<OrderRequest>` | Payment completed, verification in-flight |

## What `InitAsync` does

From `Noctua.Initialization.cs` — the constructor (run lazily on first `Noctua.*` access) performs the composition wiring; `InitAsync()` runs network-bound startup:

1. **Load `noctuagg.json`** from `Application.streamingAssetsPath` (5 s timeout)
2. **Deserialize** into `GlobalConfig` (throws `NoctuaException(Application)` on parse failure)
3. **Init logger** (`NoctuaLogger`)
4. **Wire services** — `EventSender`, `SessionTracker`, `NativeSessionTracker`, `UIFactory`, `MediationManager` (if `iaaEnabled`), `NoctuaEventService`, `NoctuaAuthentication`, `NoctuaIAPService`, `NoctuaGameService`, `NoctuaPlatform`, `NoctuaAppManager`
5. **Init native plugin** — `IosPlugin` / `AndroidPlugin` / `DefaultNativePlugin` (editor)
6. **Wait for native plugin init** — 10 s timeout, then force-init
7. **Send `sdk_init_start` event**
8. **Server config fetch** — resolves remote feature flags, IAA config merge
9. **Send `game_platform_type` event**
10. **Enable IAP + Auth** — `_iap.Enable()`, `_auth.Enable()`
11. **Set `_initialized = true`** → fire `OnInitSuccess`
12. **Spawn Noctua Inspector** if `sandboxEnabled: true` (see [sandbox-inspector.md](sandbox-inspector.md))

## Checking init state

```csharp
if (!Noctua.IsInitialized())
{
    // not safe to call Noctua.Auth / IAP / Event / IAA yet
}

if (Noctua.IsOfflineMode())
{
    // init succeeded offline (requires offlineFirstEnabled: true)
}

if (Noctua.IsOfflineFirst())
{
    // game is configured offline-first
}
```

## Offline-first mode

Set `noctua.offlineFirstEnabled: true` in `noctuagg.json`. If the network is unreachable during `InitAsync`:

- SDK completes init without the server round-trip
- `Noctua.IsOfflineMode()` returns `true`
- Events are **persisted locally** and flushed when connectivity returns
- Auth/IAP calls that require network still throw — guard with `Noctua.IsOfflineMode()`

Call `Noctua.OnOnline()` / `Noctua.OnOffline()` if your game has its own connectivity watcher to notify the native plugin, or `await Noctua.IsOfflineAsync()` to let the SDK ping and update state.

## Events emitted at init

Captured automatically, no game code required:

- `sdk_init_start` — immediately on `InitAsync` entry
- `game_platform_type` — after config load (reports Android/iOS/Editor)
- `session_start` — once the session tracker is wired
- `noctua_user_engagement` — paired with every session event

## Common init errors

| Symptom | Cause | Fix |
|---|---|---|
| `NoctuaException(Application): noctuagg.json not found` | File missing or wrong path | Place at `Assets/StreamingAssets/noctuagg.json` |
| `NoctuaException(Application): Failed to parse noctuagg.json` | Invalid JSON or missing `clientId` | Validate JSON; ensure `clientId` is set |
| Init hangs ~10 s then succeeds | Native plugin init timeout (offline / editor) | Normal in editor without native bridges. Ensure `offlineFirstEnabled: true` for offline dev |
| `ValueFactory re-entry` | SDK code called `Noctua.Instance.Value` during init | Bug in SDK modification — do not reference `Noctua.*` statics from the composition root |

## From the sample

See `Assets/SplashScript.cs` in the sample app for a production-style bootstrap with progress UI and scene transition.
