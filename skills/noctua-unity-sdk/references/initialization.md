# Initialization

> **Sources** — Official API: https://docs.noctua.gg/sdk/noctua · Tutorials: https://docs.noctua.gg/docs/installation, /integration-checklist, /unity/offline-first-guide · Repo: [Runtime/View/Noctua.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/View/Noctua.cs), [Runtime/View/Noctua.Initialization.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/View/Noctua.Initialization.cs)

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
| `Noctua.OnInitSuccess` | `Action?` (public field, not `event`) | `InitAsync` completes without error |
| `Noctua.Auth.OnAccountChanged` | `Action<UserBundle>` | login, logout, account switch (arg can be null on logout) |
| `Noctua.Auth.OnAccountDeleted` | `Action<Player>` | User-initiated account deletion |
| `Noctua.IAP.OnPurchaseDone` | `Action<OrderRequest>` | Backend-verified purchase |
| `Noctua.IAP.OnPurchasePending` | `Action<OrderRequest>` | Payment completed, verification in-flight |

## `InitAsync` signature

```csharp
public static UniTask InitAsync(Func<UniTask>? onSuccess = null);
```

The optional `onSuccess` callback runs after the init pipeline completes (after `OnInitSuccess` fires). Use it when you'd rather pass a delegate than subscribe to the field — both are supported.

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

## Implementation guide — offline-first init retry

When `noctuagg.json → noctua.offlineFirstEnabled` is `true`, the SDK auto-retries init **every 5 seconds** while the device is offline, until success. Game code does not need to schedule retries; subscribe to `OnInitSuccess` to react when the SDK finally connects:

```csharp
Noctua.OnInitSuccess += () =>
{
    Debug.Log("Noctua SDK initialized successfully");
    // Refresh feature flags, trigger any "online-only" UI here
};
```

If `InitAsync` raises an exception (genuine failure — bad config, parse error), the SDK surfaces it via the catch block. **Block the player from proceeding** — show an error dialog suggesting restart / retry; do not allow them into gameplay if init genuinely failed (per https://docs.noctua.gg/docs/installation#sdk-initialization).

## Implementation guide — handling offline auth

`AuthenticateAsync` throws a networking-flavoured exception when the device is offline. Catch and continue — events are still buffered locally and flushed on reconnect:

```csharp
try
{
    var bundle = await Noctua.Auth.AuthenticateAsync();
    // bundle.Player.Id may be 0 / null in offline-first recovery — intentional.
    // Skip server-side pairing (UpdatePlayerAccountAsync, etc.) when that happens.
}
catch (Exception e) when (e.Message.Contains("Networking"))
{
    Noctua.Event.TrackCustomEvent("login");   // buffered, flushes on reconnect
    // Continue to gameplay
}
```

What works / what doesn't while offline:

| Surface | Behaviour |
|---|---|
| `Noctua.InitAsync()` | Succeeds (offline-first), session marked offline. Genuine exceptions are NOT network errors. |
| `Noctua.Auth.AuthenticateAsync()` | Throws — catch the networking exception, continue |
| `Noctua.Event.Track*` | Works — events buffered locally, flushed on reconnect |
| `Noctua.IAP.*` | Blocked — SDK shows its own reconnect dialog automatically |
| `Noctua.Platform.Content.Show*` (announcement / customer service / reward) | Blocked — SDK shows reconnect dialog automatically |

## Implementation guide — placement of the bootstrap GameObject

Per https://docs.noctua.gg/docs/installation, attach the initializer to a GameObject in **every initial scene** (the scene that loads first when the game launches). Naming the object `NoctuaSDKInitializer` is conventional but not required. The initializer must stay alive for the full game session — do not put `OnPurchaseDone` / `OnInitSuccess` subscriptions in a class with a shorter lifetime, or pending purchases that arrive later in the session will fail to deliver.

## Implementation guide — pre-launch checklist

Run through this on a real device (not the Unity Editor) before submission. Sourced from https://docs.noctua.gg/docs/integration-checklist:

### Setup
- SDK version matches the latest stable release (`Packages/com.noctuagames.sdk/package.json`)
- `noctuagg.json` in `Assets/StreamingAssets/` has **production** credentials (confirm with Noctua team)
- `Application.version` is a SemVer string
- Android: `minSdkVersion ≥ 28`, `targetSdkVersion = 35` (mandatory Aug 2025+)
- iOS: deployment target ≥ 15, Xcode ≥ 16.0
- `Noctua.InitAsync()` is awaited at startup before any other SDK call
- No PlayerPrefs keys with `Noctua` prefix or `NativeGalleryPermission` are wiped by game code

### Authentication
- `AuthenticateAsync` returns a valid `UserBundle` on first launch
- Guest login works on a fresh install
- Social login (Google / Apple / Facebook) returns a full account
- Linking guest → social upgrades without data loss
- `ShowUserCenter` switch fires `OnAccountChanged`
- `OnAccountChanged` updates HUD / UI bound to player identity
- App resume after background: token auto-refreshes, no re-login
- **Offline:** `AuthenticateAsync` in airplane mode returns cached session (or throws cleanly) — does not crash

### In-App Ads
- AdMob and/or AppLovin installed via Integration Manager
- App IDs / Ad Unit IDs come from Remote Config — never hardcoded
- `UNITY_ADMOB` / `UNITY_APPLOVIN` defines auto-set
- Banner / interstitial / rewarded / app-open all show + dismiss correctly on device
- `OnAdNotAvailable` AND `OnAdFailedDisplayed` both reset reward-pending state
- ATT prompt appears **before** the first ad request (iOS)
- App still runs and shows ads when ATT is denied
- Test device IDs removed before release; no "Test Ad" watermark in production build

### In-App Purchase
- SKUs in Play Console + App Store Connect match the IDs in game code
- `GetProductListAsync` returns localized prices
- Purchase round-trip: `PurchaseItemAsync` → `OnPurchaseDone` fires → item delivered
- Cancellation and network failure surface user-facing messages
- iOS Restore Purchases works for non-consumables
- Noctua Gold balance displays correctly (if used)

### Event Tracking
- At least one custom event reaches **Firebase DebugView**
- Revenue events fire on purchase with correct currency
- `SetCurrentFeature` is wired in the gameplay scene scripts (if used)

### Platform Features
- `ShowAnnouncement` opens and renders content
- `ShowCustomerService` opens without errors
- `ShowReward` loads (if enabled)
- Deep links from announcements navigate to the right in-game destination

### Final submission gates
- All `Debug.Log` exposing tokens / user IDs removed or guarded
- `SetTestDeviceIds` cleared
- `noctuagg.json` has production `clientId` (not staging / sandbox)
- iOS: `NSUserTrackingUsageDescription` in `Info.plist`
- Android: `targetSdkVersion = 35`
- Tested on real Android + real iPhone (not just Editor / emulator)
- Clean install test: uninstall → reinstall → verify no first-launch crash
