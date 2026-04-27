# Session & Engagement Tracking

> **Sources** — Official tutorials: https://docs.noctua.gg/docs/unity/tracking/overview, /built-in-analytics, /feature-engagement-tracking · Repo: [Runtime/Presenter/NativeSessionTracker.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/Presenter/NativeSessionTracker.cs), [Runtime/Presenter/NoctuaEventService.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/Presenter/NoctuaEventService.cs)

The SDK automatically tracks session lifecycle and engagement time. Game code does not need to emit these events — and **must not** (double-counting).

Source: `Packages/com.noctuagames.sdk/Runtime/Presenter/SessionTracker.cs`, `Runtime/Infrastructure/EventSender.cs`.

## Automatic events

| Event | Trigger | Cadence |
|---|---|---|
| `session_start` | `InitAsync` complete | Once per session |
| `session_heartbeat` | App foregrounded | Every 60 s (default — `sessionHeartbeatPeriodMs`) |
| `session_pause` | App backgrounded | On pause |
| `session_continue` | App returns within timeout window | On resume |
| `session_end` | Graceful quit | On `OnApplicationQuit` |
| `noctua_user_engagement` | Paired with every session event above | Always fires BEFORE its session partner |
| `native_user_engagement` | OS-level callback (iOS `UIApplication`, Android `Activity`) | ~5 ms ahead of Unity pause — cross-validation only |
| `noctua_user_engagement_per_session` | Session timeout resume OR graceful quit | Cumulative foreground time |
| `feature_engagement` | `SetCurrentFeature()` called or session end | Per feature transition |

## `noctua_user_engagement` payload

```json
{
  "event_name": "noctua_user_engagement",
  "engagement_time_msec": 58649,
  "lifecycle": "pause"
}
```

- `engagement_time_msec` is **incremental** (time since last send), not cumulative — mirrors Firebase's `user_engagement` behavior.
- `lifecycle` ∈ `{"start", "foreground", "pause", "end"}`.
- Backed by `System.Diagnostics.Stopwatch` (monotonic clock, unaffected by wall clock changes).

## Session timeout

Default **15 minutes** (`noctua.sessionTimeoutMs: 900000`). When the app is backgrounded longer than `sessionTimeoutMs`:

- The old session is considered closed (no `session_end` event — force-kill limitation)
- A new session begins on foreground with a new `session_id`
- `noctua_user_engagement_per_session` fires with cumulative time of the closed session

## Experiment tag

Session events receive a `tag` property from `ExperimentManager.GetSessionTag()`. Control via:

```csharp
Noctua.SetExperiment("tutorial_v3");
```

All session events emitted afterward carry `tag: "tutorial_v3"`.

## Feature engagement

Track time spent in named game features:

```csharp
Noctua.Event.SetCurrentFeature("shop");
// ... later ...
Noctua.Event.SetCurrentFeature("battle");
// Emits: { event_name: "feature_engagement", feature_name: "shop", time_msec: ... }
```

## What the SDK auto-emits (don't touch)

**Do not manually emit these — the SDK does it:**

- Session: `session_start/pause/continue/heartbeat/end`
- Engagement: `noctua_user_engagement`, `native_user_engagement`, `noctua_user_engagement_per_session`
- Ad watch milestones: `watch_ads_0`, `watch_ads_1x`, `watch_ads_5x`, `watch_ads_10x`, `watch_ads_25x`, `watch_ads_50x`
- Taichi pipeline: all `taichi_*` events
- First purchase (per device): `first_purchase`
- SDK lifecycle: `sdk_init_start`, `game_platform_type`

Manual emission causes **double-counting** across Noctua Analytics, Adjust, Firebase, and Facebook dashboards.

## Offline behavior

Session events respect offline-first:
- Persisted to local storage immediately
- Flushed in batches of 20 (default — `trackerBatchSize`) every 60 s (default — `trackerBatchPeriodMs`)
- Survive app restart — on next init, unflushed events are loaded and sent

## Cross-validation (`native_user_engagement`)

OS-driven parallel signal for engagement time validation. Server-side only — not for product dashboards. It fires before Unity's `OnApplicationPause` (~5 ms ahead) because the OS callback arrives on the UI thread before Unity's main thread wakes. If you see divergence between `noctua_user_engagement` and `native_user_engagement`, the native one is closer to ground truth.

## Server-side session tag HashSet

Per `EventSender.cs`, these events receive the experiment `tag`:
`session_start`, `session_pause`, `session_continue`, `session_heartbeat`, `session_end`, `noctua_user_engagement`, `noctua_user_engagement_per_session`, `native_user_engagement`.
