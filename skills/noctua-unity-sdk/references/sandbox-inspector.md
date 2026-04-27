# Noctua Inspector (Sandbox Debug Overlay)

> **Sources** — Official tutorial: https://docs.noctua.gg/docs/unity/debug-and-testing/noctua-inspector · Companion debug pages: /retrieve-sdk-logs, /event-tracking-debugging, /iaa-debugging, /taichi-debugging · Repo: [Runtime/Inspector/NoctuaInspectorController.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/Inspector/NoctuaInspectorController.cs), [Runtime/Infrastructure/Network/HttpInspectorLog.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/Infrastructure/Network/HttpInspectorLog.cs), [Runtime/Presenter/TrackerDebugMonitor.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/Presenter/TrackerDebugMonitor.cs)

In-app debug overlay that surfaces SDK HTTP requests, tracker events, and Firebase/Adjust/Facebook lifecycle on-device — no `adb logcat` or Xcode needed.

Introduced in SDK 0.109.0 (Beta). Source: `Runtime/View/Noctua.Initialization.cs` (overlay spawn), `Runtime/Inspector/NoctuaInspectorController.cs` (UI), `Runtime/Infrastructure/Network/HttpInspectorLog.cs` (HTTP capture), `Runtime/Presenter/TrackerDebugMonitor.cs` (tracker capture).

## Enable

Set `noctua.sandboxEnabled: true` in `noctuagg.json`. The inspector auto-spawns during `Noctua.InitAsync()`.

In production (`sandboxEnabled: false`), `Noctua.Inspector`, `Noctua.HttpLog`, and `Noctua.DebugMonitor` are `null` — **zero runtime cost**.

## Open the overlay

Any of:

- **3× device shake** (mobile)
- **4-finger tap** (mobile)
- Code:
  ```csharp
  Noctua.ShowInspector();
  Noctua.HideInspector();
  Noctua.ToggleInspector();
  ```
- A debug button in your game's dev menu:
  ```csharp
  Noctua.Inspector?.Show();
  ```

## What it shows

Four tabs:

1. **HTTP** — recent SDK HTTP requests (URL, method, status, body). Source: `Noctua.HttpLog` (ring-buffered).
2. **Tracker events** — every tracker emission with state transitions:
   - `Queued` → persisted locally
   - `Emitted` → sent to wire
   - `Acknowledged` → confirmed by server
   Source: `Noctua.DebugMonitor`.
3. **Firebase / Adjust / Facebook lifecycle** — per-event status for each external tracker.
4. **Config** — loaded `GlobalConfig` (inspect `noctuagg.json` as parsed).

## Programmatic inspection

```csharp
if (Noctua.IsSandbox())
{
    // Dump recent HTTP — actual API is Snapshot(), not .Entries
    // (Runtime/Infrastructure/Network/HttpInspectorLog.cs → IReadOnlyList<HttpExchange>)
    foreach (var entry in Noctua.HttpLog.Snapshot())
    {
        Debug.Log($"{entry.Method} {entry.Url} → {entry.Status}");
    }

    // Dump recent tracker events — Snapshot accepts an optional provider filter
    // (Runtime/Presenter/TrackerDebugMonitor.cs)
    foreach (var ev in Noctua.DebugMonitor.Snapshot())
    {
        Debug.Log($"{ev.EventName} → {ev.State}");
    }

    // Filter to a single provider:
    var adjustOnly = Noctua.DebugMonitor.Snapshot(providerFilter: "adjust");
}
```

> Earlier drafts referenced `Noctua.HttpLog.Entries` and `Noctua.DebugMonitor.Entries`. Those properties do not exist — the inspector exposes immutable snapshots via `Snapshot()` so concurrent writes from the SDK background thread can't tear the read.

## Typical uses

- **Verify event firing** — click a button that should emit `button_click`, switch to Tracker tab, confirm it appears with state `Emitted`
- **Debug Adjust attribution** — see whether `purchase` forwarded to Adjust (requires `eventMap` entry) and the Adjust token returned
- **Validate offline-first** — toggle airplane mode, see events queue, re-enable, see them flush
- **Check remote config** — after `InitAsync`, verify merged `iaa` config in the Config tab

## Disabling in a shipping build

```json
"noctua": {
  "sandboxEnabled": false
}
```

Alternatively, gate with `#if DEVELOPMENT_BUILD` in your build script and rewrite `noctuagg.json` before a release build.

## Caveat

Inspector only observes the SDK's own HTTP client and tracker pipeline. Game-level `UnityWebRequest` calls and your own analytics are not captured.

## Implementation guide — open the overlay

Three triggers, whichever is convenient:

| Trigger | Where it works |
|---|---|
| Shake device 3× within ~1 s | Real Android / iOS |
| 4-finger tap anywhere on screen | Mobile, Android emulator |
| **Ctrl + Shift + D** (⌘ + Shift + D on macOS) | Unity Editor, desktop |

Programmatic:
```csharp
if (Noctua.IsSandbox())
{
    Noctua.ShowInspector();
    Noctua.HideInspector();
    Noctua.ToggleInspector();
}
```

All three are safe no-ops when `sandboxEnabled` is `false`, so leaving the calls in shipping code costs nothing.

## Implementation guide — tabs and lifecycle

Three primary tabs (per https://docs.noctua.gg/docs/unity/debug-and-testing/noctua-inspector):

### Timeline
Merged feed of HTTP requests + tracker events, newest first. Tap any row to expand. Use as the starting point.

### HTTP
Every Noctua-SDK HTTP request: method, URL, status, elapsed time, request/response body, headers. Each row exposes:

- **Copy as cURL** — recreate outside the game
- **Copy JSON** — full snapshot for archives
- Sensitive headers (`Authorization`, `X-Access-Token`, `Cookie`) auto-redacted as `••••`

Only Noctua SDK traffic is captured. Firebase / Adjust / Facebook / ad-network HTTP runs through their own stacks — they show up on the **Trackers** tab instead.

### Trackers
Every event the game forwards to Firebase / Adjust / Facebook / Noctua. Lifecycle phases:

| Phase | Meaning |
|---|---|
| Queued | Event handed to native SDK |
| Sending | Native SDK calling into 3rd-party SDK |
| Emitted | 3rd-party SDK accepted (log line detected) |
| Uploading | 3rd-party SDK started batch flush |
| Acknowledged | Server 200 OK — landed in provider dashboard |
| Failed | Server error or local rejection |
| TimedOut | No confirmation within 30 s — usually means verbose logs disabled |

Tap any row for the payload, provider-specific extras (Adjust attaches the matched `adjustToken`), and per-phase timestamps. Filter chips at the top scope to All / Noctua / Firebase / Adjust / Facebook.

**Toolbar buttons (Trackers tab):**
- **Clear** — wipe rows (ring buffer cap: 100 HTTP + 200 Tracker entries)
- **Export** — copy full capture as JSON to clipboard (for bug reports)
- **Copy adb debug cmd** (Android) — clipboards `setprop log.tag.FA VERBOSE` + `setprop debug.firebase.analytics.app <pkg>` so you can run them in a terminal to enable Firebase DebugView

## Implementation guide — typical workflows

- **Verify event firing** — emit `button_click`, switch to Trackers tab, confirm the row reaches `Emitted`
- **Debug Adjust attribution** — see whether `purchase` forwarded (requires `eventMap` entry) and inspect the matched `adjustToken`
- **Validate offline-first** — toggle airplane mode → events queue → re-enable → see them flush (with `Acknowledged` rows)
- **Check remote config** — after `InitAsync`, inspect the Config tab for the merged `iaa` block

## Troubleshooting

- **Shake doesn't open** — confirm `sandboxEnabled: true`, look for `[Noctua] Inspector enabled` in logs during `InitAsync`. Fallback: 4-finger tap or `Noctua.ShowInspector()`.
- **Firebase rows stuck at Queued (iOS)** — `-FIRDebugEnabled` not set. The `BuildPostProcessor` injects it when `sandboxEnabled: true`; if running via Xcode directly, add it under *Product → Scheme → Edit Scheme → Run → Arguments*.
- **Firebase rows stuck at Queued (Android)** — run before launch:
  ```bash
  adb shell setprop log.tag.FA VERBOSE
  adb shell setprop log.tag.FA-SVC VERBOSE
  ```
  The Trackers toolbar's **Copy adb debug cmd** button puts this on your clipboard.
- **Adjust rows never advance** — Adjust only emits confirmation logs in sandbox mode. Confirm `AdjustConfig.environment` is `"sandbox"` in dev builds.
- **Facebook rows never advance** — verbose logging gated by the native SDK; only fires in sandbox / development builds.

## Implementation guide — manual log filters (when Inspector isn't enough)

Per https://docs.noctua.gg/docs/unity/debug-and-testing/event-tracking-debugging:

| Provider | Platform | Tag / prefix | Filter |
|---|---|---|---|
| Noctua SDK | Android | `NoctuaSDK` | `adb logcat \| grep "Event Sender"` |
| Noctua SDK | iOS | `NoctuaSDK` | Xcode Console: filter `Event Sender` |
| Firebase Analytics | Android | `FA`, `FA-SVC` | `adb logcat -s FA FA-SVC` |
| Firebase Analytics | iOS | `[Firebase/Analytics]` | Xcode Console: filter `Firebase/Analytics` |
| Adjust | Android | `Adjust` | `adb logcat Adjust:V *:S` |
| Adjust | iOS | `[Adjust]` | Xcode Console: filter `[Adjust]` |
| Facebook App Events | Android | `FacebookSDK.AppEvents` | `adb logcat FacebookSDK.AppEvents:D *:S` |
| Facebook App Events | iOS | `FBSDKLog` | Xcode Console: filter `FBSDKLog` |

**Noctua SDK event-sender lines** look like:
```
[Event Sender] Event 'level_complete' enqueued, current queue length: 1
[Event Sender] sending batch: 3 events (batchFull=False, periodElapsed=True)
[Event Sender] sent 3 events, deleted 3. 0 remaining.
```

**Firebase Android DebugView** — enable real-time streaming:
```bash
adb shell setprop debug.firebase.analytics.app com.your.package.name
```
Disable with `.none.` instead of the package name.

**Firebase iOS DebugView** — add `-FIRAnalyticsDebugEnabled` to the Xcode scheme's launch arguments.

**Adjust** only logs detailed tracking lines in sandbox mode. Production builds log at Info level only and won't progress past `Queued` in the Inspector.

## Implementation guide — Taichi tROAS milestone verification

Taichi is fully managed by the SDK + Noctua team — game code does **not** instrument, wire, or test Taichi. If ads are showing and revenue is reporting, Taichi is already running. Verification (per https://docs.noctua.gg/docs/unity/debug-and-testing/taichi-debugging) is purely log-reading:

```bash
# All Taichi lines
adb logcat -s Unity | grep -i "Taichi"

# Only milestone firings (ignore progress noise)
adb logcat -s Unity | grep -E "Taichi Step [1-6]"
```

Six one-shot milestones — defaults configurable remotely:

| # | Event Name | Threshold |
|---|---|---|
| 1 | `Total_Ads_Revenue_001` | 0.01 USD total ad revenue |
| 2 | `TenAdsShown` | 10 impressions any format |
| 3 | `taichi_total_ad_impression` | 10 (interstitial + rewarded) |
| 4 | `taichi_interstitial_ad_impression` | 10 interstitials |
| 5 | `taichi_rewarded_ad_impression` | 10 rewarded |
| 6 | `taichi_rewarded_ad_revenue` | 0.01 USD rewarded revenue |

| Log Line | Meaning | Action |
|---|---|---|
| `TaichiConfig is null` | Taichi disabled server-side | Report — testing impossible |
| `Taichi Step N: … progress` | Counter incremented | Normal — keep testing |
| `Taichi Step N: … crossed` | Milestone fired | Expected once |
| `[REVENUE LOST #N]` | Ad revenue dropped before tracker ready | **File a bug with full log** |

File a bug also if a milestone fires more than once without reinstall, ad impressions occur but no `Taichi Step … progress` appears (and `TaichiConfig is null` is **not** logged), or a milestone fires in logs but never reaches the Noctua dashboard.

## Implementation guide — retrieving SDK log files for support

The SDK writes a per-day log file to device storage: `{game-name}-noctua-log{YYYYMMDD}.txt` (e.g. `noctua-sdk-unity-noctua-log20241125.txt`).

**Android** (Android 11+ blocks direct `Android/data` access from most file managers):
1. Install **Total Commander** from Play Store.
2. Navigate **Internal Storage → Android → data**.
3. On *Access denied!* tap **Yes** to redirect to the system Files app.
4. Navigate to `Android/data/com.noctuagames.<your-game>/files/`.
5. Long-press the matching log file → **Share**.

**iOS:**
1. Open **Files** app → **On My iPhone**.
2. Open the folder named after your game.
3. Tap the dated log → share via the share icon.

When reporting include: log files for the affected day(s), device model + OS version, app version + SDK version (from `Packages/com.noctuagames.sdk/package.json`), and reproduction steps.

These are **Noctua SDK logs only** — for Unity engine logs use the [Unity Player Log](https://docs.unity3d.com/Manual/LogFiles.html) instead.
