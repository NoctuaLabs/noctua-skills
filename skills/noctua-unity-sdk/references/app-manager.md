# `Noctua.App` — In-App Review & App Update

> **Sources** — Official API: https://docs.noctua.gg/sdk/app · Tutorial: https://docs.noctua.gg/docs/unity/app-management · Repo: [Runtime/View/NoctuaAppManager.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/View/NoctuaAppManager.cs), [Runtime/Model/DTOs/AppUpdateInfo.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/Model/DTOs/AppUpdateInfo.cs)

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

iOS handles app updates via the App Store; these APIs are **no-ops on iOS** and in the Unity Editor (`CheckForUpdate` returns `IsUpdateAvailable=false`; `StartImmediate/FlexibleUpdate` return `AppUpdateResult.NotAvailable`).

### Check for update
```csharp
AppUpdateInfo info = await Noctua.App.CheckForUpdate();

if (info.IsUpdateAvailable)
{
    if (info.IsImmediateAllowed)    { /* block and force update */ }
    else if (info.IsFlexibleAllowed) { /* download in background */ }
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

if (result == AppUpdateResult.Success)
{
    // Binary downloaded and ready; ask the user before restarting.
    Noctua.App.CompleteUpdate();   // triggers install + restart
}
```

## Update result states

`AppUpdateResult` is an **enum** (`Runtime/Model/DTOs/AppUpdateInfo.cs`). Compare with `==`.

| Value | Meaning |
|---|---|
| `Success` | Update downloaded / installed successfully. For flexible updates this means the binary is ready — call `CompleteUpdate()` to apply. |
| `UserCancelled` | User canceled the update flow. |
| `Failed` | Download or install failed. |
| `NotAvailable` | No update flow ran (unsupported platform, or `CheckForUpdate` returned `IsUpdateAvailable=false`). |

## `AppUpdateInfo` fields

| Field | Type | Description |
|---|---|---|
| `IsUpdateAvailable` | `bool` | `true` if an update is available on the store |
| `IsImmediateAllowed` | `bool` | `true` if an immediate update is allowed |
| `IsFlexibleAllowed` | `bool` | `true` if a flexible update is allowed |
| `AvailableVersionCode` | `int` | Version code of the available update |
| `StalenessDays` | `int` | Days since the update became available |

## Implementation guide — full pattern

Recommended app-update flow on `Start()`:

```csharp
using com.noctuagames.sdk;
using Cysharp.Threading.Tasks;
using UnityEngine;

public class AppUpdateManager : MonoBehaviour
{
    private async void Start()
    {
        await CheckAndHandleUpdate();
    }

    private async UniTask CheckAndHandleUpdate()
    {
        var info = await Noctua.App.CheckForUpdate();
        if (!info.IsUpdateAvailable) return;

        // Force update once the available version is at least a week old
        if (info.StalenessDays >= 7 && info.IsImmediateAllowed)
        {
            var result = await Noctua.App.StartImmediateUpdate();
            if (result == AppUpdateResult.UserCancelled)
            {
                Application.Quit();   // or block gameplay
            }
        }
        else if (info.IsFlexibleAllowed)
        {
            var result = await Noctua.App.StartFlexibleUpdate(p =>
                Debug.Log($"Downloading update: {p * 100:F0}%"));

            if (result == AppUpdateResult.Success)
            {
                // Show toast/banner, then install+restart
                Noctua.App.CompleteUpdate();
            }
        }
    }
}
```

## Recommended timing for `RequestInAppReview`

- After completing a milestone (level clear, quest done)
- After a positive moment (winning a match, earning a reward)
- **Never** on app launch, during active gameplay, or on every session

```csharp
private async UniTask OnLevelComplete()
{
    if (ShouldAskForReview())   // your own throttle/cohort logic
    {
        await Noctua.App.RequestInAppReview();
    }
}
```

## iOS fallback

On iOS `CheckForUpdate` returns `AppUpdateInfo` with `IsUpdateAvailable=false`; `StartImmediateUpdate` / `StartFlexibleUpdate` return `AppUpdateResult.NotAvailable`. Use your own App Store version check + `Application.OpenURL("itms-apps://...")` if needed.

## Types

- `AppUpdateInfo` — `{ IsUpdateAvailable, IsImmediateAllowed, IsFlexibleAllowed, AvailableVersionCode, StalenessDays }`
- `AppUpdateResult` — enum: `Success`, `UserCancelled`, `Failed`, `NotAvailable`
