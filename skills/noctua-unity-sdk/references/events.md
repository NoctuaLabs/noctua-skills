# `Noctua.Event` — Analytics

Source: `Packages/com.noctuagames.sdk/Runtime/Presenter/NoctuaEventService.cs`.

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

List<NativeEvent> batch = await Noctua.GetEventsBatchAsync(limit: 100, offset: 0);

int deleted = await Noctua.DeleteEventsByIdsAsync(new long[] { 1, 2, 3 });

// Debug-only: dump raw storage
List<NativeEvent> all = await Noctua.GetEventsAsync();
Noctua.DeleteEvents();                    // clear all — destructive, debug only
Noctua.InsertEvent(customJsonString);     // inject a raw event row
Noctua.SaveEvents(jsonArrayString);       // replace storage from JSON
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
