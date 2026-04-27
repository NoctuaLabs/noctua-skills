# Error Handling

> **Sources** — Official API references mention `NoctuaException` throughout (https://docs.noctua.gg/sdk/auth, /iap, /iaa, /event); no dedicated page yet · Debug guides: https://docs.noctua.gg/docs/unity/debug-and-testing/retrieve-sdk-logs, /noctua-inspector, /event-tracking-debugging · Repo: [Runtime/Model/Entities/NoctuaException.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/Model/Entities/NoctuaException.cs), [Runtime/View/Noctua.Initialization.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/View/Noctua.Initialization.cs) (GlobalExceptionLogger), [Runtime/Presenter/NativeCrashForwarder.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/Presenter/NativeCrashForwarder.cs)

All SDK errors surface as `NoctuaException` with a numeric `ErrorCode` whose values come from the `NoctuaErrorCode` enum.

## Canonical try/catch

```csharp
try
{
    await Noctua.Auth.LoginAsGuest();
}
catch (NoctuaException nex)
{
    Debug.LogError($"Noctua {nex.ErrorCode}: {nex.Message}");
}
catch (Exception e)
{
    Debug.LogError($"Unexpected: {e.Message}");
}
```

## Category error codes (`NoctuaErrorCode`)

Verified against [`Runtime/Model/Entities/NoctuaException.cs`](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/Model/Entities/NoctuaException.cs). `NoctuaException.ErrorCode` is `int` (the constructor casts the enum to `int` on the way in), so when comparing in a `catch` filter you can either compare the int directly or cast: `nex.ErrorCode == (int)NoctuaErrorCode.PaymentStatusCanceled`.

| Code | Numeric | When |
|---|---|---|
| `Unknown` | `3000` | Catch-all when the SDK couldn't classify the failure. |
| `Networking` | `3001` | HTTP / connectivity failure outside offline-first scope. |
| `Application` | `3002` | `noctuagg.json` missing / invalid / parse failure; init timeout. |
| `Authentication` | `3003` | Auth call while offline; invalid credentials; token expired; UI canceled. |
| `ActiveCurrencyFailure` | `3004` | Currency lookup failed (see `Noctua.IAP.GetActiveCurrencyAsync`). |
| `MissingCompletionHandler` | `3005` | Internal: a UI flow finished without a registered completion. |
| `Payment` | `3006` | General IAP-level failure (server verification, native billing). |
| `AccountStorage` | `3007` | Local account database read/write error. |
| `PaymentStatusCanceled` | `3008` | Purchase canceled by the user (StoreKit / Play Billing). |
| `PaymentStatusItemAlreadyOwned` | `3009` | Non-consumable already owned — restore instead of repurchase. |
| `PaymentStatusIapNotReady` | `3010` | Native IAP store not initialized yet — retry after `IsReady` flips true. |
| `UserBanned` | `2202` | User account is banned — show "contact support" dialog. |

## IAP numeric error codes

The canonical numeric codes are the `NoctuaErrorCode` values in the table above (`PaymentStatusCanceled=3008`, `PaymentStatusItemAlreadyOwned=3009`, `PaymentStatusIapNotReady=3010`, plus `ActiveCurrencyFailure=3004` and `Payment` itself).

> Earlier drafts of this skill listed numeric codes 2043–2048 (pending/verification/delivery/canceled/refunded/voided). Those are **not** present in the `NoctuaErrorCode` enum at the time of writing. If your server contract uses those numbers, treat them as server-side response codes (read `nex.Payload`, not `nex.ErrorCode`) and confirm against the live API before relying on them.

```csharp
try
{
    await Noctua.IAP.PurchaseItemAsync(req);
}
catch (NoctuaException nex) when (nex.ErrorCode == (int)NoctuaErrorCode.PaymentStatusCanceled)
{
    // User canceled — no UI
}
catch (NoctuaException nex) when (nex.ErrorCode == (int)NoctuaErrorCode.PaymentStatusItemAlreadyOwned)
{
    // Restore instead of repurchase
    await Noctua.IAP.RestorePurchasedProducts(new List<string> { req.ProductId });
}
catch (NoctuaException nex) when (nex.ErrorCode == (int)NoctuaErrorCode.PaymentStatusIapNotReady)
{
    // Native store not ready yet — back off and retry
}
catch (NoctuaException nex)
{
    ShowIapError($"{nex.ErrorCode}: {nex.Message}");
}
```

## Offline handling

When `Noctua.IsOfflineMode()` is `true` (only possible if `offlineFirstEnabled: true` and network was down at init):

| Call | Behavior |
|---|---|
| `Noctua.Event.TrackCustomEvent` | Queued locally, flushes on reconnect — no throw |
| `Noctua.Auth.AuthenticateAsync` | Returns cached account if available; else throws `Authentication` |
| `Noctua.Auth.ShowUserCenter` | Shows "retry" dialog instead of opening UI |
| `Noctua.IAP.PurchaseItemAsync` | Throws — purchases require network |
| `Noctua.Platform.Content.ShowAnnouncement` | Throws — content requires network |

Always guard network-bound UI with:
```csharp
if (Noctua.IsOfflineMode())
{
    ShowOfflineBanner();
    return;
}
```

## Init failures

```csharp
try
{
    await Noctua.InitAsync();
}
catch (NoctuaException nex) when (nex.ErrorCode == (int)NoctuaErrorCode.Application)
{
    // Config missing or invalid — recoverable only by fixing noctuagg.json
    ShowFatalDialog("Game configuration error. Please reinstall.");
}
catch (Exception e)
{
    ShowFatalDialog($"Init failed: {e.Message}");
}
```

## Logging

The SDK uses `NoctuaLogger` internally (Serilog-backed). Game code can use `Debug.Log` as usual, but SDK log output is prefixed `[Noctua]` and filterable:

- Android: `adb logcat -s Unity:V Noctua:V`
- iOS: Xcode console filter on `Noctua`
- Editor: Unity console. SDK verbosity is gated by `noctuagg.json → noctua.sandboxEnabled` (no separate `logLevel` field exists in `NoctuaConfig.cs`).

## Exception inspection cheatsheet

```csharp
catch (NoctuaException nex)
{
    Debug.LogError($"code={nex.ErrorCode}");   // int — values from NoctuaErrorCode enum
    Debug.LogError($"msg={nex.Message}");
    Debug.LogError($"payload={nex.Payload}");  // server-provided extra data (may be JSON); see NoctuaException.cs:50
}
```

> The SDK does not populate `InnerException` — read `Payload` instead.

## `client_error` event (auto-emitted)

Since 0.109.0 the `GlobalExceptionLogger` (`Runtime/View/Noctua.Initialization.cs:208`) automatically forwards `Debug.LogWarning` / `LogError` / `LogException` calls as a `client_error` event with these dimensions:

- `severity` — `warning` / `error` / `exception`
- `error_type` — typically the exception class name
- `message` — truncated
- `stack` — truncated
- `source` — `managed` (Unity-side) or `native` (see below)

Throttle is **30 events/min** with a **60s dedup window** keyed on `error_type + message`. PII risk: do not put user emails or tokens into `Debug.LogError` strings — they will be forwarded.

There is no public `Noctua.SetEventSender(null)` kill-switch on the static facade; if you need to silence the forwarder, gate the underlying `Debug.Log*` calls on the game side.

## Native crash forwarding

The SDK reads platform crash registries on startup and emits a `client_error` with `source=native` for crashes that occurred during the previous launch:

- **iOS:** MetricKit `MXMetricPayload` / `MXDiagnosticPayload`.
- **Android:** `ActivityManager.getHistoricalProcessExitReasons()`.

Test the pipeline with `Noctua.DebugInjectFakeNativeCrash()` (`Runtime/View/Noctua.cs:96`) — fires a synthetic native-source `client_error` on the next launch, no actual crash needed.

## Common error patterns

| Symptom | Likely cause |
|---|---|
| `Application: noctuagg.json not found` | File missing from `Assets/StreamingAssets/` |
| `Application: clientId missing` | `clientId` empty in `noctuagg.json` |
| `Authentication: token expired` | Access token refresh failed — call `ResetAccounts()` and re-authenticate |
| `UserBanned` | Server flagged user — inform user to contact support, do not retry |
| IAP code 2044 on every purchase | Server signature verification failing — check `clientId` / `gameId` match the Noctua console |
| `Payment: pending` (no numeric code) | Purchase is still mid-flow; `OnPurchaseDone` will fire later |
