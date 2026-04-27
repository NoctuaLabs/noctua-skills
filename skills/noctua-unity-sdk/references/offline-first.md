# Offline-First Mode

> **Sources** — Tutorial: https://docs.noctua.gg/docs/unity/offline-first-guide · API: https://docs.noctua.gg/sdk/noctua · Repo: [Runtime/View/Noctua.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/View/Noctua.cs), [Runtime/View/Noctua.Initialization.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/View/Noctua.Initialization.cs)

Lets `Noctua.InitAsync()` succeed without a network connection and degrades only the features that genuinely need the backend.

## Enable

Set `noctua.offlineFirstEnabled: true` in `noctuagg.json`:

```json
"noctua": {
  "offlineFirstEnabled": true
}
```

When enabled, `InitAsync` automatically retries every 5 seconds while the device is offline (per https://docs.noctua.gg/docs/installation#sdk-init-success-handler). Use `Noctua.OnInitSuccess` to react when init eventually succeeds:

```csharp
Noctua.OnInitSuccess += () =>
{
    Debug.Log("SDK initialized");
    RefreshOnlineFeatures();
};
```

## Behaviour matrix

| Surface | Behaviour offline | Game code requirement |
|---|---|---|
| `Noctua.InitAsync()` | Succeeds. Session marked offline. Any thrown exception is a non-network error. | Treat exceptions as real errors; don't swallow |
| `Noctua.Auth.AuthenticateAsync()` | **Throws** networking exception | Catch, check `Message.Contains("Networking")`, continue |
| `Noctua.IAP.*` | Blocked — SDK shows its own reconnect dialog | Nothing — dialog is automatic |
| `Noctua.Platform.Content.Show*` (announcement, customer service, reward, social) | Blocked — SDK shows reconnect dialog | Nothing — dialog is automatic |
| `Noctua.Event.TrackCustomEvent()` etc. | Buffered locally, flushed on reconnect | Nothing |
| `Noctua.IAA.*` | Caches load on previous session apply; new fills require network | Guard UI on `IsRewardedAdReady()` etc. |
| `Noctua.IsOfflineAsync()` / `IsOfflineMode()` | Always available | See [Connectivity API](#connectivity-api) below |

## Implementation guide — handling offline auth

```csharp
try
{
    var bundle = await Noctua.Auth.AuthenticateAsync();
    // Player.Id may be 0 / null in the offline-first recovery path — intentional.
    // Skip server-side pairing (UpdatePlayerAccountAsync, etc.) when that happens.
    var playerId = bundle?.Player?.Id ?? 0;
    if (playerId != 0) await Noctua.Auth.UpdatePlayerAccountAsync(myAccountData);
}
catch (Exception e)
{
    if (e.Message.Contains("Networking"))
    {
        Noctua.Event.TrackCustomEvent("login");   // buffered + flushed on reconnect
        // Continue into gameplay
    }
    else
    {
        throw;   // Real error — do NOT swallow
    }
}
```

The "skip server-side pairing when `Player.Id == 0`" pattern matters because in offline-recovery mode the SDK returns a placeholder bundle so gameplay can proceed. Once connectivity returns and `OnInitSuccess` fires, re-authenticate and pair.

## Connectivity API

| Method | Returns | Use case |
|---|---|---|
| `Noctua.IsOfflineAsync()` | `Task<bool>` | One-shot async check — runs a lightweight reachability probe |
| `Noctua.IsOfflineMode()` | `bool` | Hot-path / per-frame — returns the SDK's cached offline state, no network call |
| `Noctua.OnOnline()` / `Noctua.OnOffline()` | — | Notify the SDK from your own connectivity watcher (optional) |

```csharp
// Cheap sync check — safe inside Update() / UI handlers
if (Noctua.IsOfflineMode())
{
    offlineBadge.SetActive(true);
}

// Async probe — useful when entering a feature that needs the network
if (await Noctua.IsOfflineAsync())
{
    ShowReconnectDialog();
    return;
}

// If your game has its own connectivity manager, push transitions to the SDK:
ConnectivityWatcher.OnOnline  += () => Noctua.OnOnline();
ConnectivityWatcher.OnOffline += () => Noctua.OnOffline();
```

## Implementation guide — testing offline mode

1. Build a sandbox build (`sandboxEnabled: true`) with `offlineFirstEnabled: true`.
2. Enable airplane mode on the device.
3. Cold-start the app — `Noctua.InitAsync()` should succeed.
4. Try an IAP — confirm the SDK shows its reconnect dialog automatically.
5. Try the customer service screen — same reconnect dialog.
6. Fire a custom event (`Noctua.Event.TrackCustomEvent`) — open the Inspector → Trackers tab; the row should sit at `Queued`.
7. Disable airplane mode — within ~5 s, `OnInitSuccess` should fire and queued events should progress to `Acknowledged`.

## Common pitfalls

- **Treating every `AuthenticateAsync` exception as fatal** — the offline path is expected; only abort flow on non-networking exceptions.
- **Manually buffering events** — pointless duplication; the SDK already persists events to local storage and flushes them.
- **Calling `IAP` / `Platform.Content` from custom code paths that bypass the SDK dialog** — don't try to "do it yourself" while offline; let the SDK's reconnect UI handle it.
- **Not handling `Player.Id == 0`** — game-side code that assumes a non-zero player ID will fail in offline-recovery; guard with the `if (playerId != 0)` pattern.
- **Shipping `offlineFirstEnabled: true` to a server-authoritative game** — if your game cannot meaningfully run without your backend, leave the flag off so init fails loudly rather than entering a degraded state.
