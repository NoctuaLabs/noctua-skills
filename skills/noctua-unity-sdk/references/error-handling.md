# Error Handling

All SDK errors surface as `NoctuaException` with a typed `ErrorCode`.

Source: `Packages/com.noctuagames.sdk/Runtime/Core/NoctuaException.cs`, `NoctuaErrorCode.cs`.

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

| Code | When |
|---|---|
| `Application` | `noctuagg.json` missing / invalid / parse failure; init timeout |
| `Authentication` | Auth call while offline; invalid credentials; token expired; UI canceled |
| `UserBanned` | User account is banned — show "contact support" dialog |
| `Payment` | IAP-level failure (see numeric codes below for specifics) |
| `Networking` | HTTP / connectivity failure outside offline-first scope |

## IAP numeric error codes

Returned by `Noctua.IAP.*` methods. Handle specific codes for better UX:

| Code | Meaning | UX |
|---|---|---|
| 2043 | Pending verification | Show "verifying…" spinner; wait for `OnPurchaseDone` |
| 2044 | Verification failed | Error dialog, offer retry |
| 2045 | Delivery callback failed | Server granted content but your delivery callback errored — re-run delivery |
| 2046 | User canceled | Dismiss silently |
| 2047 | Refunded | Revoke content on next eligibility check |
| 2048 | Voided | Revoke content |

```csharp
try
{
    await Noctua.IAP.PurchaseItemAsync(req);
}
catch (NoctuaException nex) when (nex.ErrorCode == 2046)
{
    // User canceled — no UI
}
catch (NoctuaException nex) when (nex.ErrorCode == 2043)
{
    ShowVerifyingSpinner();
    // OnPurchaseDone will fire later
}
catch (NoctuaException nex)
{
    ShowIapError(nex.Message);
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
catch (NoctuaException nex) when (nex.ErrorCode == NoctuaErrorCode.Application)
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
- Editor: Unity console with SDK log level controlled by `noctuagg.json → noctua.logLevel` (if present)

## Exception inspection cheatsheet

```csharp
catch (NoctuaException nex)
{
    Debug.LogError($"code={nex.ErrorCode}");   // NoctuaErrorCode enum OR numeric int
    Debug.LogError($"msg={nex.Message}");
    Debug.LogError($"inner={nex.InnerException?.Message}");
}
```

## Common error patterns

| Symptom | Likely cause |
|---|---|
| `Application: noctuagg.json not found` | File missing from `Assets/StreamingAssets/` |
| `Application: clientId missing` | `clientId` empty in `noctuagg.json` |
| `Authentication: token expired` | Access token refresh failed — call `ResetAccounts()` and re-authenticate |
| `UserBanned` | Server flagged user — inform user to contact support, do not retry |
| IAP code 2044 on every purchase | Server signature verification failing — check `clientId` / `gameId` match the Noctua console |
| `Payment: pending` (no numeric code) | Purchase is still mid-flow; `OnPurchaseDone` will fire later |
