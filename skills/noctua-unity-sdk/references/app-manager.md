# `Noctua.App` — In-App Review & App Update

Source: `Packages/com.noctuagames.sdk/Runtime/View/NoctuaAppManager.cs`.

Wraps **Google Play In-App Review**, **Google Play In-App Update** (Android), and native review request (iOS).

## In-app review

Shows the OS-native review prompt. iOS limits frequency automatically (Apple caps at 3/year); Play has its own throttling.

```csharp
try
{
    await Noctua.App.RequestInAppReview();
}
catch (NoctuaException nex)
{
    Debug.LogError($"Review {nex.ErrorCode}: {nex.Message}");
}
```

Best called after a positive milestone (level complete, high score, boss defeated) — not on first launch.

## App update (Android only)

iOS handles app updates via the App Store; these APIs are **no-ops on iOS**.

### Check for update
```csharp
AppUpdateInfo info = await Noctua.App.CheckForUpdate();

if (info.IsUpdateAvailable)
{
    if (info.IsImmediateUpdateAllowed)    { /* block and force update */ }
    else if (info.IsFlexibleUpdateAllowed) { /* download in background */ }
}
```

### Immediate (blocking) update

Full-screen update UI; user can't use the app until update completes:
```csharp
AppUpdateResult result = await Noctua.App.StartImmediateUpdate();
// Process restarts automatically on success; this coroutine likely never resumes
```

### Flexible (background) update

Download in background, prompt user to restart when ready:
```csharp
AppUpdateResult result = await Noctua.App.StartFlexibleUpdate(onProgress: (float p) =>
{
    UpdateProgressBar(p);   // 0.0 → 1.0
});

if (result.IsDownloaded)
{
    // Offer user a "Restart now" prompt
    Noctua.App.CompleteUpdate();   // triggers install + restart
}
```

## Update result states

`AppUpdateResult.Status` / `.IsDownloaded` indicate:

| State | Meaning |
|---|---|
| Downloaded | Binary ready; call `CompleteUpdate()` to install |
| Installing | Install in progress |
| Failed | Download/install failed — check `Message` |
| Canceled | User canceled the update flow |

## Combined pattern

```csharp
var info = await Noctua.App.CheckForUpdate();

if (!info.IsUpdateAvailable) return;

if (info.UpdatePriority >= 4 && info.IsImmediateUpdateAllowed)
{
    await Noctua.App.StartImmediateUpdate();   // force critical updates
}
else if (info.IsFlexibleUpdateAllowed)
{
    var result = await Noctua.App.StartFlexibleUpdate(p => UpdateUI(p));
    if (result.IsDownloaded && UserAcceptedRestart())
    {
        Noctua.App.CompleteUpdate();
    }
}
```

## iOS fallback

On iOS `CheckForUpdate`, `StartImmediateUpdate`, `StartFlexibleUpdate` return `AppUpdateResult` with `IsUpdateAvailable = false`. Use your own App Store version check + `Application.OpenURL("itms-apps://...")` if needed.

## Types

- `AppUpdateInfo` — `{ IsUpdateAvailable, IsImmediateUpdateAllowed, IsFlexibleUpdateAllowed, UpdatePriority, AvailableVersionCode, ... }`
- `AppUpdateResult` — `{ Status, IsDownloaded, IsInstalled, Message, ... }`

See `Runtime/Model/Entities/` for exact field layouts.
