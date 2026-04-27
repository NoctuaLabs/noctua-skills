# IAA Event Tracking — Canonical Schema

> **Sources** — Official: https://docs.noctua.gg/sdk/iaa-event-tracking · Debugging: https://docs.noctua.gg/docs/unity/debug-and-testing/iaa-debugging, /taichi-debugging, /event-tracking-debugging · API: [iaa-ads.md](iaa-ads.md) · Repo: [Runtime/Presenter/MediationManager.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/Presenter/MediationManager.cs), [Runtime/AdsManager/](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/tree/main/Runtime/AdsManager)

The Noctua IAA layer auto-emits analytics events for every ad lifecycle step. **No manual tracking calls are needed in game code** — subscribe to `Noctua.IAA` events for state changes; the SDK handles analytics. All events are sent via `Noctua.Event.TrackCustomEvent` with the same payload schema regardless of which mediator is active.

## Mediation coverage

| Format | AppLovin MAX | AdMob |
|---|---|---|
| Banner | ✅ | ✅ |
| Interstitial | ✅ | ✅ |
| Rewarded | ✅ | ✅ |
| Rewarded Interstitial | — not supported | ✅ |
| App Open | ✅ | ✅ |

## Canonical lifecycle events

Common payload shape (used by `ad_loaded`, `ad_shown`, `ad_clicked`, `ad_expanded`, `ad_collapsed`):

| Key | Type | Notes |
|---|---|---|
| `placement` | string | Caller-supplied placement, or `"unknown"`. |
| `ad_type` | string | `banner` / `interstitial` / `rewarded` / `rewarded_interstitial` / `app_open`. |
| `ad_unit_id` | string | Network ad unit ID. |
| `ad_unit_name` | string | Same as `ad_unit_id`. |
| `ad_format` | string | Same as `ad_type` (back-compat). |
| `ad_size` | string | `320x50` for banners, `fullscreen` otherwise. |
| `ad_source` | string | Winning network reported by the mediator (e.g. `"Meta Audience Network"`). |
| `ad_platform` | string | Top-level mediator — `applovin` or `admob`. |

| Event | Trigger |
|---|---|
| `ad_loaded` | Ad fetched and cached, ready to show. |
| `ad_shown` | Full-screen content opened (or banner view loaded). |
| `ad_clicked` | User tapped any ad. |
| `ad_expanded` / `ad_collapsed` | Banner opens / closes a full-screen overlay. |

`ad_load_failed` and `ad_show_failed` carry: `ad_format`, `ad_platform`, `ad_unit_name`, `error` (combined string — `"[code] message (domain=…)"` for AdMob; `"[code] message | mediator [code] message"` for AppLovin). Interstitial and rewarded retry automatically with exponential back-off; `ad_load_failed` fires per attempt.

> **Deprecated alias:** `ad_shown_failed` is still emitted alongside the canonical `ad_show_failed` for one release. Move dashboards to `ad_show_failed`.

`ad_impression` adds revenue to the common shape:

| Key | Type | Notes |
|---|---|---|
| `value` | double | Revenue in original currency. |
| `currency` | string | Always `"USD"`. |
| `value_usd` | double | Normalized USD. AppLovin already in USD; AdMob micro-units divided by 1,000,000. |
| `engagement_time` | long | Milliseconds between `Show()` and the impression callback. |

## Watch-count milestones (`watch_ads_*`)

Fires **exactly once per install per ad type**. Only **rewarded** and **interstitial** ads count; banner / rewarded interstitial / app open are excluded. State persisted in `PlayerPrefs`.

| Event | Threshold |
|---|---|
| `watch_ads_5x` | 5 ads of that type watched |
| `watch_ads_10x` | 10 |
| `watch_ads_25x` | 25 |
| `watch_ads_50x` | 50 |

Trigger: rewarded fires inside the reward callback (watched to completion); interstitial fires on ad close. Payload: `ad_type` (`rewarded` / `interstitial`), `count` (cumulative count when the milestone was crossed).

Do **not** manually emit these — game code calling `TrackCustomEvent("watch_ads_5x", …)` will double-count.

## Taichi tROAS thresholds

Threshold-based milestone events for the **Taichi tROAS** optimization pipeline. Fires once when its accumulator crosses the threshold; the accumulator is reset to zero on fire. Counters and revenue accumulators are persisted in `PlayerPrefs`. All thresholds are driven by remote `TaichiConfig` — no hardcoded values.

| Step | Event | Counter scope | Default threshold |
|---|---|---|---|
| 1 | `Total_Ads_Revenue_001` | Cumulative revenue across **all** ad formats | `revenue_threshold` — 0.01 USD |
| 2 | `TenAdsShown` | Cumulative impression count across **all** ad formats | `ad_count_threshold` — 10 |
| 3 | `taichi_total_ad_impression` | Impressions — **interstitial + rewarded only** | `total_impression_threshold` — 10 |
| 4 | `taichi_interstitial_ad_impression` | Impressions — **interstitial only** | `interstitial_count_threshold` — 10 |
| 5 | `taichi_rewarded_ad_impression` | Impressions — **rewarded only** | `rewarded_count_threshold` — 10 |
| 6 | `taichi_rewarded_ad_revenue` | Cumulative revenue — **rewarded only** | `rewarded_revenue_threshold` — 0.01 USD |

Payload: `value` (revenue or impression-count revenue), `currency` (always `"USD"`).

### Why `TenAdsShown` usually fires first (and sometimes alone)

- **Banner impressions** count toward `TenAdsShown` but **not** toward any `taichi_*` count event. Auto-refreshing banners (~30 s) accumulate 10 impressions in ~5 min of gameplay.
- **App Open** impressions count only toward `TenAdsShown`.
- **Interstitial** and **rewarded** are user-triggered and far less frequent.

If a session has no rewarded/interstitial views, `TenAdsShown` may be the only Taichi event that fires.

### Test mode caveat

In test mode AdMob and AppLovin report `0.00 USD` per impression, so `Total_Ads_Revenue_001` (Step 1) and `taichi_rewarded_ad_revenue` (Step 6) **never fire** even after many impressions. They fire correctly in production with real revenue.

### Disabling Taichi

When remote `TaichiConfig` is `null`, the SDK early-returns from all `Process*Thresholds` paths and emits no threshold events.

## Waterfall (`wf_*`) events

Internal funnel-analysis events. Do not follow the canonical payload schema. `<format>` ∈ `banner` / `interstitial` / `rewarded` / `ri` / `app_open`.

| Event | Meaning |
|---|---|
| `wf_<format>_request_start` | Ad request initiated. |
| `wf_<format>_request_adunit_success` | Ad unit returned a fill. |
| `wf_<format>_request_adunit_failed` | Ad unit returned an error. |
| `wf_<format>_request_adunit_timeout` | Latency > 5000 ms. |
| `wf_<format>_request_finished_success` | Load cycle finished OK. |
| `wf_<format>_request_finished_failed` | Load cycle finished with failure. |
| `wf_<format>_started_playing` | Show requested. |
| `wf_<format>_show_sdk` | Full-screen content opened. |
| `wf_<format>_show_sdk_failed` | Full-screen content failed to open. |
| `wf_<format>_show_not_ready` | Show called but no ad was ready. |
| `wf_<format>_show_failed_null` | Ad object was null at show time. |
| `wf_<format>_clicked` | Ad clicked. |
| `wf_<format>_closed` | Ad closed. |
| `wf_banner_hidden` | Banner hidden (not destroyed). |
| `ad_impression_<format>` | Legacy per-format impression marker (kept for back-compat). |

Common fields: `ad_format`, `mediation_service` (`applovin` / `admob`), `ad_unit_id`, `ad_network`, `ntw` (adapter class name), `latency_millis`.

## Implementation notes

- Emission lives in `BannerAppLovin` / `InterstitialAppLovin` / `RewardedAppLovin` / `AppOpenAppLovin` (AppLovin) and `BannerAdmob` / `InterstitialAdmob` / `RewardedAdmob` / `RewardedInterstitialAdmob` / `AppOpenAdmob` (AdMob).
- All emission is wrapped in `try/catch` — analytics failures never interrupt ad delivery.
- Names are constants in `IAAEventNames`; payload keys in `IAAPayloadKey`. The shared `IAAPayloadBuilder` builds every canonical payload, guaranteeing key-set parity across mediators.
