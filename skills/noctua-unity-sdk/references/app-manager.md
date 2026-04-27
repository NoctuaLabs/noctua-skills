# `Noctua.App` — In-App Review & App Update

> **Sources** — Official API: https://docs.noctua.gg/sdk/app · Tutorial: https://docs.noctua.gg/docs/unity/app-management · Repo: [Runtime/View/NoctuaAppManager.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/View/NoctuaAppManager.cs)

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

if (result == AppUpdateResult.Completed)
{
    // Binary downloaded and ready; ask the user before restarting.
    Noctua.App.CompleteUpdate();   // triggers install + restart
}
```

## Update result states

`AppUpdateResult` is an **enum** (not a struct — see https://docs.noctua.gg/sdk/types). Compare with `==`.

| Value | Meaning |
|---|---|
| `NotAvailable` | No update flow ran (unsupported platform, or `CheckForUpdate` returned `IsUpdateAvailable=false`). |
| `Completed` | Update downloaded / installed successfully. For flexible updates this means the binary is ready — call `CompleteUpdate()` to apply. |
| `Canceled` | User canceled the update flow. |
| `Failed` | Download or install failed. |
| `InProgress` | Returned while a flow is still running (rare in awaited paths). |

## Combined pattern

```csharp
var info = await Noctua.App.CheckForUpdate();

if (!info.IsUpdateAvailable) return;

if (info.UpdatePriority >= 4 && info.IsImmediateUpdateAllowed)
{
    var r = await Noctua.App.StartImmediateUpdate();   // force critical updates
    if (r == AppUpdateResult.Failed) ShowFatalDialog("Update failed");
}
else if (info.IsFlexibleUpdateAllowed)
{
    var r = await Noctua.App.StartFlexibleUpdate(p => UpdateUI(p));
    if (r == AppUpdateResult.Completed && UserAcceptedRestart())
    {
        Noctua.App.CompleteUpdate();
    }
}
```

## iOS fallback

On iOS `CheckForUpdate` returns `AppUpdateInfo` with `IsUpdateAvailable=false`; `StartImmediateUpdate` / `StartFlexibleUpdate` return `AppUpdateResult.NotAvailable`. Use your own App Store version check + `Application.OpenURL("itms-apps://...")` if needed.

## Types

- `AppUpdateInfo` — `{ IsUpdateAvailable, IsImmediateUpdateAllowed, IsFlexibleUpdateAllowed, UpdatePriority (0–5), AvailableVersionCode }`
- `AppUpdateResult` — enum: `NotAvailable`, `Completed`, `Canceled`, `Failed`, `InProgress`
