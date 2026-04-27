# `Noctua.Event` — Analytics

> **Sources** — Official API: https://docs.noctua.gg/sdk/event · Tutorials: https://docs.noctua.gg/docs/unity/tracking/overview, /built-in-analytics, /custom-events-tracking, /tracking-revenue, /feature-engagement-tracking, /game-stage-tracking · IAA event schema: [iaa-event-schema.md](iaa-event-schema.md) · Repo: [Runtime/Presenter/NoctuaEventService.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/Presenter/NoctuaEventService.cs)

Tracks custom events, purchase revenue, ad revenue, and feature engagement. Routes events to Noctua tracker API, Adjust, Firebase, and Facebook based on `noctuagg.json`.

## ⚠️ Events the SDK auto-emits

**Do not manually emit these — the SDK handles them and manual calls double-count across all dashboards:**

- `watch_ads_0`, `watch_ads_1x`, `watch_ads_5x`, `watch_ads_10x`, `watch_ads_25x`, `watch_ads_50x` (milestones, driven by `AdWatchMilestoneTracker`)
- All `taichi_*` events (`taichi_total_ad_impression`, `taichi_interstitial_ad_impression`, `taichi_rewarded_ad_impression`, `taichi_rewarded_ad_revenue`, …)
- `first_purchase` (per-device, PlayerPrefs-guarded)
- Session events: `session_start`, `session_pause`, `session_continue`, `session_heartbeat`, `session_end`, `noctua_user_engagement`, `native_user_engagement`, `noctua_user_engagement_per_session`
- `sdk_init_start`, `game_platform_type`

## Custom events

```csharp
Noctua.Event.TrackCustomEvent("level_complete", new Dictionary<string, IConvertible>
{
    { "level",       5           },
    { "stage_mode",  "campaign"  },
    { "duration_ms", 42300       },
    { "hero_class",  "warrior"   }
});
```

- Name: snake_case recommended. Auto-forwarded to Firebase, Adjust (if mapped in `noctuagg.json`), and Facebook.
- Payload values must be `IConvertible` (primitives, strings, numbers, bools). Nested objects are **not** supported.
- Adjust only receives events listed in `adjust.<platform>.eventMap` — unmapped events go to Firebase + Facebook + Noctua only.

### With revenue
```csharp
Noctua.Event.TrackCustomEventWithRevenue(
    name: "booster_activated",
    revenue: 0.99,
    currency: "USD",
    extraPayload: new Dictionary<string, IConvertible> { { "booster_id", "x2_xp" } });
```

## Purchase tracking

Usually you don't call this — the IAP service emits `purchase` automatically on `OnPurchaseDone`. Call manually only for server-side / non-IAP purchases:

```csharp
Noctua.Event.TrackPurchase(
    orderId: "order_abc123",
    amount: 4.99,
    currency: "USD",
    extraPayload: new Dictionary<string, IConvertible>
    {
        { "product_id", "gem_pack_m" },
        { "payment_method", "noctua_gold" }
    });
```

## Ad revenue

`Noctua.IAA` auto-tracks mediated ad revenue. Call `TrackAdRevenue` manually only for ad networks you mediate outside of AppLovin MAX / AdMob:

```csharp
Noctua.Event.TrackAdRevenue(
    source: "custom_offerwall",
    revenue: 0.012,
    currency: "USD",
    extraPayload: new Dictionary<string, IConvertible>
    {
        { "ad_unit_id", "offerwall_home" },
        { "placement", "home_screen" }
    });
```

## Feature engagement

Call `SetCurrentFeature` when the player enters a game feature. The SDK auto-emits `feature_engagement` with time spent when a new feature is set or the session ends.

```csharp
Noctua.Event.SetCurrentFeature("shop_gem");
// ... player browses shop ...

Noctua.Event.SetCurrentFeature("battle_pve");
// Previous "shop_gem" feature engagement event emitted automatically

string current = Noctua.Event.GetCurrentFeature(); // "battle_pve"
```

You can also manually bracket with `feature_engagement_start` / `feature_engagement_end` custom events — the SDK computes `time_msec` and attaches a shared `visit_id`:
```csharp
Noctua.Event.TrackCustomEvent("feature_engagement_start", new Dictionary<string, IConvertible>
{
    { "feature_name", "tutorial_step_3" }
});
// ...
Noctua.Event.TrackCustomEvent("feature_engagement_end", new Dictionary<string, IConvertible>
{
    { "feature_name", "tutorial_step_3" }
});
```

## Global properties

Set once, attached to every subsequent event:

```csharp
Noctua.Event.SetProperties(
    country: "ID",
    ipAddress: "",          // usually resolved server-side
    isSandbox: Noctua.IsSandbox()
);
```

## Auto-emitted error events

Since 0.109.0 the `GlobalExceptionLogger` forwards `Debug.LogWarning` / `LogError` / `LogException` as `client_error` events (`source=managed`), and reads platform crash registries on startup to emit `client_error` (`source=native`) for last-launch crashes (iOS MetricKit, Android historical exit reasons). Throttled at 30/min with 60s dedup. **Don't put PII in `Debug.Log` strings.** See [error-handling.md](error-handling.md#client_error-event-auto-emitted).

## Experiments / A-B tags

```csharp
Noctua.SetExperiment("tutorial_v3");            // active experiment name
string current = Noctua.GetActiveExperiment();

Noctua.SetGeneralExperiment("loot_drop", "2x"); // arbitrary key/value flag
string flag = Noctua.GetGeneralExperiment("loot_drop");
```

`tag` is attached to all session events (`session_*`, `noctua_user_engagement*`, `native_user_engagement`) via `ExperimentManager`.

## Event storage inspection

Events are persisted locally before HTTP flush (offline-first). Static helpers on `Noctua`:

```csharp
int total = await Noctua.GetEventCountAsync();

// Per-row reader: returns typed NativeEvent { Id, EventJson, Timestamp }
List<NativeEvent> batch = await Noctua.GetEventsBatchAsync(limit: 100, offset: 0);

int deleted = await Noctua.DeleteEventsByIdsAsync(new long[] { 1, 2, 3 });

// Debug-only: dump raw storage as JSON strings (no typed wrapper)
List<string> all = await Noctua.GetEventsAsync();
Noctua.DeleteEvents();                              // clear all — destructive, debug only
Noctua.InsertEvent(customJsonString);               // inject a raw event row
Noctua.SaveEvents(jsonArrayString);                 // replace storage from JSON
```

## Pseudo-user ID

```csharp
string id = Noctua.GetPseudoUserId();   // 32-char hex, stable per device
```

Used for anonymous tracking before login. Persists across sessions (not across reinstalls).

## Common recipes

### Tutorial funnel
```csharp
Noctua.Event.TrackCustomEvent("tutorial_start", new() { { "variant", "v3" } });
// ...
Noctua.Event.TrackCustomEvent("tutorial_complete",
    new() { { "variant", "v3" }, { "duration_sec", 127 } });
```

### Level progress
```csharp
Noctua.Event.TrackCustomEvent("level_start", new() { { "level", 12 } });
Noctua.Event.TrackCustomEvent("level_fail",  new() { { "level", 12 }, { "reason", "died" } });
Noctua.Event.TrackCustomEvent("level_win",   new() { { "level", 12 }, { "stars", 3 } });
```

### Currency sink/source (soft currency)
```csharp
Noctua.Event.TrackCustomEvent("currency_earn",
    new() { { "currency", "gold" }, { "amount", 500 }, { "source", "quest" } });
Noctua.Event.TrackCustomEvent("currency_spend",
    new() { { "currency", "gold" }, { "amount", 200 }, { "sink", "equipment" } });
```

## Naming conventions

- **snake_case** for event names and keys
- Keep names short but specific: `level_start` > `start`, `shop_open` > `ui_open`
- Use **numeric** values when you want to compute sums / averages server-side (`duration_ms`, `gold_spent`)
- Use **strings** only for categorical dimensions (`hero_class`, `stage_mode`)
- Reuse the same property key across related events to keep dashboards clean

## Implementation guide — `eventMap` and the unified tracker

`Noctua.Event.TrackCustomEvent` fans out to **Noctua + Firebase + Facebook + Adjust** in a single call. The wrinkle is Adjust: every event needs a pre-registered token. Map them in `noctuagg.json → adjust.<platform>.eventMap`:

```json
"adjust": {
  "android": {
    "eventMap": { "purchase": "qye2vk", "level_up": "xoizir" }
  }
}
```

Unmapped events **still reach Firebase + Facebook + Noctua** — they just skip Adjust. The Noctua team usually provides an "Integration Manifest Document" listing the events your title should track, with the matching Adjust tokens.

## Implementation guide — dynamic event names with `suffix`

Pass a `"suffix"` key to append a runtime-computed segment to the event name (per https://docs.noctua.gg/docs/unity/tracking/custom-events-tracking):

```csharp
// Dispatched as "level_99"
Noctua.Event.TrackCustomEvent("level", new Dictionary<string, IConvertible>
{
    { "suffix", "99" }
});
```

Suffixed names reach Firebase + Facebook only. **Adjust ignores the suffix** because tokens must be pre-registered — the unsuffixed base name (`level`) is what hits Adjust via `eventMap`.

## Implementation guide — Game stage tracking

Bracket each level with `game_stage_start` / `game_stage_complete`. The SDK auto-attaches `current_stage_level` and `current_stage_mode` to **every other custom event** while a stage is active, so you can filter `item_purchased`, `ad_watched`, etc. by level without adding extra fields.

```csharp
// On level enter
Noctua.Event.TrackCustomEvent("game_stage_start", new()
{
    { "level",      "5"    },
    { "stage_mode", "hard" }   // optional
});

// On level clear — SDK adds stage_time_msec automatically
Noctua.Event.TrackCustomEvent("game_stage_complete", new()
{
    { "level", "5" }
});
```

**Behaviours**
- `stage_time_msec` only attaches if `game_stage_start` ran in the same session (no cross-session timing).
- `current_stage_level` / `current_stage_mode` persist across app restarts (PlayerPrefs-backed) — they remain attached to **all events** until the next `game_stage_start` with a different level.
- Do **not** pass `stage_time_msec` manually — the SDK computes it.

## Implementation guide — Feature engagement (per-screen time)

`SetCurrentFeature` records time spent on a screen and emits `feature_engagement` **when the player leaves**. Add two lines to every scene script:

```csharp
public class ShopScene : MonoBehaviour
{
    private void Start()     => Noctua.Event.SetCurrentFeature("Shop");
    private void OnDestroy() => Noctua.Event.SetCurrentFeature(string.Empty);
}
```

Unity calls outgoing scene `OnDestroy` before incoming `Start`, so `feature_engagement` fires automatically on every transition.

**Behaviour table**

| Action | Fires `feature_engagement`? |
|---|---|
| `SetCurrentFeature("B")` while on `"A"` | Yes — for `A` |
| `SetCurrentFeature(string.Empty)` while on `"A"` | Yes — for `A` |
| `SetCurrentFeature("A")` with no previous feature | No |
| `SetCurrentFeature("A")` while already on `"A"` | Yes — closes current visit, opens new one |
| App killed mid-session | No — always clear in `OnDestroy` |

**Event payload:** `{ feature_tag, feature_time_msec, feature_visit_id }`. Each visit gets a unique `feature_visit_id` so repeat visits to the same screen analyse as distinct rows. Use PascalCase names matching scene names (`MainMenu`, `Battle`, `Shop`, `Inventory`) — not `scr1` / `screen_3`.

## Implementation guide — Tracking ad revenue from a raw mediator

The Noctua IAA module already auto-tracks AppLovin MAX + AdMob revenue. Call `TrackAdRevenue` only when you mediate **outside** Noctua's pipeline — e.g. a custom offerwall, a house-ads SDK, or a network not on Noctua's adapter list.

`source` argument:
- `"applovin_max_sdk"` — for AppLovin's `OnAdRevenuePaidEvent`
- `"admob_sdk"` — for AdMob's `OnPaidEvent`
- Free-form for custom networks (e.g. `"custom_offerwall"`)

```csharp
// AppLovin MAX raw subscription
MaxSdkCallbacks.Rewarded.OnAdRevenuePaidEvent += (adUnitId, info) =>
{
    Noctua.Event.TrackAdRevenue("applovin_max_sdk", info.Revenue, "USD",
        new Dictionary<string, object>
        {
            { "platform", "AppLovin" },
            { "networkSource", info.NetworkName },
            { "adFormat", info.Placement }
        });
};

// AdMob raw subscription
private void HandleAdPaidEvent(AdValue adValue)
{
    double revenue = adValue.Value / 1_000_000.0;   // micros → units
    var resp = rewardedAd.GetResponseInfo();
    var loaded = resp.GetLoadedAdapterResponseInfo();

    Noctua.Event.TrackAdRevenue("admob_sdk", revenue, adValue.CurrencyCode,
        new Dictionary<string, object>
        {
            { "latencyMillis", loaded.LatencyMillis },
            { "adSourceName",  loaded.AdSourceName }
        });
}
```

`TrackCustomEventWithRevenue` is the same idea but lets you choose any event name (`ad_impression`, `ad_revenue`, etc.) and ensures the revenue surfaces in Adjust as well as Firebase + Facebook.

## Reference — built-in analytics emitted automatically

The SDK auto-emits a comprehensive analytics surface once `InitAsync` succeeds. Full schema at https://docs.noctua.gg/docs/unity/tracking/built-in-analytics. **Never re-emit any of these manually** — duplicate counts cause dashboard skew across Firebase / Adjust / Facebook / Noctua simultaneously:

| Category | Events |
|---|---|
| **Init / session** | `sdk_init_start`, `game_platform_type`, `session_start`, `session_pause`, `session_continue`, `session_heartbeat`, `session_end`, `noctua_user_engagement`, `noctua_user_engagement_per_session`, `native_user_engagement` |
| **Auth** | `login`, `logout`, account state transitions |
| **IAP** | `purchase`, `first_purchase` (per-device once) |
| **IAA load / show / revenue** | `wf_<format>_request_*`, `ad_loaded`, `ad_load_failed`, `ad_shown`, `ad_shown_failed`, `ad_clicked`, `ad_closed`, `ad_impression`, `ad_impression_<format>`, `reward_earned`, banner-specific `wf_banner_*` / `ad_expanded` / `ad_collapsed` (see [iaa-event-schema.md](iaa-event-schema.md)) |
| **Ad-watch milestones** | `watch_ads_0`, `watch_ads_1x`, `watch_ads_5x`, `watch_ads_10x`, `watch_ads_25x`, `watch_ads_50x` |
| **Taichi tROAS** | `taichi_total_ad_impression`, `taichi_interstitial_ad_impression`, `taichi_rewarded_ad_impression`, `taichi_rewarded_ad_revenue`, `Total_Ads_Revenue_001`, `TenAdsShown` |
| **Errors** (since 0.109.0) | `client_error` (managed + native) — see [error-handling.md](error-handling.md#client_error-event-auto-emitted) |
| **Game stage / engagement** | `feature_engagement` (from `SetCurrentFeature`) |
