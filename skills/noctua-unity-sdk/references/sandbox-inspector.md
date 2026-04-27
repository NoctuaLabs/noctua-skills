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
