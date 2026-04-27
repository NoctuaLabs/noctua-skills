# `Noctua.IAA` — In-App Advertising

> **Sources** — Official API: https://docs.noctua.gg/sdk/iaa · Tutorials: https://docs.noctua.gg/docs/unity/iaa/overview, /implementing-in-app-ads, /installing-ad-network-adapters, /advanced-ad-network-adapters, /advanced-configuration, /advanced-main-thread-callbacks, /fallback-mechanism · Per-format guides: /ad-formats/banner, /ad-formats/interstitial, /ad-formats/rewarded, /ad-formats/rewarded-interstitial, /ad-formats/app-open · Event schema: [iaa-event-schema.md](iaa-event-schema.md) · Debug: https://docs.noctua.gg/docs/unity/debug-and-testing/iaa-debugging, /taichi-debugging · Repo: [Runtime/Presenter/MediationManager.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/Presenter/MediationManager.cs)

Unified mediator for AppLovin MAX and Google AdMob (GMA). Supports banner, interstitial, rewarded, rewarded-interstitial, and app-open ad formats.

## Prerequisites

1. `noctuagg.json` has `noctua.iaaEnabled: true` and an `iaa` block with ad unit IDs — see [noctuagg-json.md](noctuagg-json.md).
2. Run **`Noctua > Noctua Integration Manager > Recommended Setup`** once — installs AppLovin MAX 8.6.2 + AdMob 11.0.0 with conflict-free adapters. See [editor-tooling.md](editor-tooling.md).
3. `UNITY_APPLOVIN` and `UNITY_ADMOB` scripting defines are set automatically by Integration Manager on install.

## Initialization

`Noctua.InitAsync()` initializes mediation automatically (AppLovin + AdMob native SDKs). Subscribe to `OnInitialized` to know when ads are ready:

```csharp
Noctua.IAA.OnInitialized += () => Debug.Log("Ads ready");
```

Or call it manually after init (normally unnecessary):
```csharp
Noctua.IAA.Initialize(initCompleteAction: () => Debug.Log("Ads ready"));
```

## Common events

```csharp
Noctua.IAA.OnAdDisplayed          += () => { /* ad visible */ };
Noctua.IAA.OnAdFailedDisplayed    += () => { /* show failed */ };
Noctua.IAA.OnAdClicked            += () => { /* user clicked */ };
Noctua.IAA.OnAdImpressionRecorded += () => { /* impression counted */ };
Noctua.IAA.OnAdClosed             += () => { /* user closed ad */ };
Noctua.IAA.OnAdNotAvailable       += (string reason) => { /* no-fill / freq-cap / cooldown */ };
```

Network-specific (compile-conditional):
```csharp
#if UNITY_ADMOB
Noctua.IAA.AdmobOnUserEarnedReward += (Reward r) => GrantReward(r.Amount, r.Type);
Noctua.IAA.AdmobOnAdRevenuePaid    += (AdValue v, ResponseInfo info) => { /* impression-level revenue */ };
Noctua.IAA.OnAdsAvailable          += (PreloadConfiguration cfg) => { /* preload ready */ };
Noctua.IAA.OnAdExhausted           += (PreloadConfiguration cfg) => { /* preload empty */ };
#endif

#if UNITY_APPLOVIN
Noctua.IAA.AppLovinOnUserEarnedReward += (MaxSdk.Reward r) => GrantReward(r.Amount, r.Label);
Noctua.IAA.AppLovinOnAdRevenuePaid    += (MaxSdkBase.AdInfo info) => { /* revenue */ };
#endif
```

## Show ads

Network-agnostic — SDK routes to primary / secondary mediator based on `noctuagg.json → iaa.mediation` + `ad_format_overrides`:

```csharp
// Interstitial
Noctua.IAA.ShowInterstitial();
Noctua.IAA.ShowInterstitial(placement: "level_end");

// Rewarded
Noctua.IAA.ShowRewardedAd();
Noctua.IAA.ShowRewardedAd(placement: "double_reward");

// Rewarded interstitial (if enabled)
Noctua.IAA.ShowRewardedInterstitialAd();

// Banner
Noctua.IAA.ShowBannerAd();
Noctua.IAA.HideBannerAd();       // network-agnostic hide (routes to both primary + secondary)

// App open
Noctua.IAA.ShowAppOpenAd();
```

## Check readiness

```csharp
if (Noctua.IAA.IsRewardedAdReady())    Noctua.IAA.ShowRewardedAd();
if (Noctua.IAA.IsInterstitialReady())  Noctua.IAA.ShowInterstitial();
if (Noctua.IAA.IsAppOpenAdReady())     Noctua.IAA.ShowAppOpenAd();
```

## Preload (manual)

Mediation preloads on init, but you can force:
```csharp
Noctua.IAA.LoadInterstitialAd();
Noctua.IAA.LoadRewardedAd();
```

## Banner configuration

```csharp
// AdMob banner — specify size + position
Noctua.IAA.CreateBannerViewAdAdmob(AdSize.Banner, AdPosition.Bottom);

// AppLovin banner — specify color + position
Noctua.IAA.CreateBannerViewAdAppLovin(Color.black, MaxSdkBase.BannerPosition.BottomCenter);
// or
Noctua.IAA.CreateBannerViewAdAppLovin(Color.black, MaxSdkBase.AdViewPosition.BottomCenter);

// Tweaks
Noctua.IAA.SetBannerWidth(320);
Noctua.IAA.SetBannerRefreshInterval(30);     // seconds
Noctua.IAA.SetBannerPlacement("home_bottom");
Noctua.IAA.StopBannerAutoRefresh();
Noctua.IAA.StartBannerAutoRefresh();

// Hide (AppLovin-specific — prefer HideBannerAd() for network-agnostic)
Noctua.IAA.HideAppLovinBanner();
Noctua.IAA.DestroyBannerAppLovin();
```

## App-open auto-show

Set `iaa.app_open_auto_show: true` in `noctuagg.json`. SDK watches foreground transitions and shows the app-open ad automatically via `AppOpenManager`:

```csharp
Noctua.IAA.AppOpenManager.Enable();
Noctua.IAA.AppOpenManager.Disable();
```

## Mute

```csharp
Noctua.IAA.SetMuted(true);
```

## Ad unit IDs at runtime

```csharp
string interstitial = Noctua.IAA.InterstitialAdUnitID;
string rewarded     = Noctua.IAA.RewardedAdUnitID;
string rewardedInt  = Noctua.IAA.RewardedInterstitialAdUnitID;
string banner       = Noctua.IAA.BannerAdUnitID;
```

Also `Noctua.IAA.SetupAdUnitID(iaaResponse)` to reload ad units after a server config change.

## Diagnostics (sandbox)

```csharp
Noctua.IAA.ShowMediationDebugger();            // overlay
Noctua.IAA.ShowMediationDebugger("admob");     // network-specific
Noctua.IAA.ShowCreativeDebugger();
Noctua.IAA.SetTestDeviceIds(new List<string> { "YOUR_DEVICE_ID" });

Noctua.IAA.ShowAdPlaceholder(AdPlaceholderType.Interstitial);  // fake placeholder for layout testing
Noctua.IAA.CloseAdPlaceholder();
```

## Segmentation / experiments / CPM diagnostics (read-only)

```csharp
string segmentKey = Noctua.IAA.GetSegmentKey();        // e.g. "t1_nonpayer_loyal_d30plus" or "not initialized"
string mediator   = Noctua.IAA.MediationType;          // "admob" or "applovin"
bool   hybrid     = Noctua.IAA.IsHybridMode;           // primary + secondary active

// Active A/B variants per experiment ID, persisted in PlayerPrefs (stable across sessions)
Dictionary<string,string> variants = Noctua.IAA.GetExperimentAssignments();

// Per-format / per-network CPM floor evaluation result (or "CPM floors disabled")
Dictionary<string,string> floors  = Noctua.IAA.GetCpmFloorStatus();

// AppLovin banner geometry on screen
Rect bannerRect = Noctua.IAA.GetBannerPosition();
```

> The merged runtime IAA config (`Noctua.IAA.IAAResponse`) is `internal` and cannot be read from game code. Use the sandbox **Inspector → Config tab** to view it during development. See [experiments.md](experiments.md) for the full segmentation / floor / experiment story.

## Frequency caps & cooldowns

Configured entirely in `noctuagg.json → iaa.frequency_caps` and `iaa.cooldown_seconds`. When a cap/cooldown blocks a show call, the SDK fires `OnAdNotAvailable(reason)` instead of displaying — game code should have fallback UX.

Server config merge (since 0.98.0) is **field-by-field** for `frequency_caps` and `cooldown_seconds`: a remote override that only specifies `interstitial.max_impressions` keeps the local `interstitial.window_seconds` and the entire local `app_open` block. Don't assume the remote payload is a full replacement — partial overrides are first-class.

## Secondary network fallback

If `iaa.secondary_mediation` is set, the SDK transparently falls back when the primary network returns no fill for `banner` / `interstitial` / `rewarded`. Game code does not need to retry — `OnAdNotAvailable` only fires after **both** networks have been tried. Inspect `Noctua.IAA.IsHybridMode` to confirm the fallback path is wired.

## "Remove ads" IAP and `IAdNetwork` no-ops

If your game ships an IAP that disables ads, you may try to compile out one mediator (`UNITY_APPLOVIN` off, `UNITY_ADMOB` on, or vice versa). Older SDK versions threw `NotImplementedException` from the disabled adapter's interface methods. The 0.109.0 fix makes those default-method implementations safe no-ops, so the IAP "remove ads" flow no longer needs to also strip the cross-network call sites — keep your code path single and let the inactive adapter quietly do nothing.

## Sample app reference

`Assets/MediationScript.cs` in the sample project wires a complete IAA test UI (ready checks, placement buttons, banner size controls) — copy patterns from there.

## Common pitfalls

| Symptom | Cause |
|---|---|
| `OnAdNotAvailable("no_fill")` in debug | Test device not registered / ad unit has no fill. Register via `SetTestDeviceIds` |
| Banner doesn't appear on iOS | App-open ad auto-show covering banner; or banner created before `OnInitialized` |
| `MaxSdk` / `MobileAds` undefined | `UNITY_APPLOVIN` / `UNITY_ADMOB` defines missing — re-run Integration Manager |
| `NotImplementedException` from an AppLovin method when AdMob is primary | Fixed in SDK 0.109.0 — cross-network default methods are now safe no-ops |
| CocoaPods install fails on Maio | Maio is mutually exclusive across mediators — install from only one. Run **Noctua > iOS > Fix CocoaPods Conflicts** |

See [ios-setup.md](ios-setup.md) for iOS-specific ad caveats (SKAdNetworks, ATT).

## Implementation guide — `Noctua.IAA` is null when ads disabled

When `noctuagg.json → noctua.iaaEnabled` is `false` (or set false via remote config), `Noctua.IAA` returns **null**. Always guard with `?.`:

```csharp
Noctua.IAA?.ShowInterstitial();
Noctua.IAA?.ShowRewardedAd("daily_reward");

// UNSAFE — throws NullReferenceException when ads are off
Noctua.IAA.ShowInterstitial();
```

This pattern lets the same source compile with or without ads.

## Implementation guide — installation modes

Whichever ad SDKs you install via Noctua Integration Manager determines runtime behaviour:

| Installed | Mode | Defines |
|---|---|---|
| AdMob + AppLovin | Hybrid-capable (controlled by Remote Config) | `UNITY_ADMOB` + `UNITY_APPLOVIN` |
| AdMob only | Single-network on AdMob | `UNITY_ADMOB` |
| AppLovin only | Single-network on AppLovin | `UNITY_APPLOVIN` |
| Neither | Same as `iaaEnabled: false` | (none) |

In single-network mode, `iaa.secondary_mediation` is ignored. **Rewarded Interstitial is AdMob-only** — `ShowRewardedInterstitialAd()` is a no-op when only AppLovin is installed.

`UNITY_ADMOB` / `UNITY_APPLOVIN` defines are managed automatically by the Integration Manager — do not toggle them by hand.

## Implementation guide — installing ad network adapters

Use **Noctua → Noctua Integration Manager** for the curated catalog (22 AppLovin MAX + 17 AdMob mediation adapters from `unity.packages.applovin.com` / `package.openupm.com`). The window has four sections: Recommended Setup, IAA Providers, AppLovin MAX adapters, AdMob adapters.

For each adapter row: **Installed** (Android + iOS versions), **Rec (Android/iOS)** (recommended stable), **Action** (Install / →Stable / Remove). UPM resolves immediately on click — no manual refresh.

**Cross-catalog installs** (e.g. Pangle in both AppLovin and AdMob for hybrid mediation) trigger amber `⚠ Also in AdMob` / `⚠ Also in AppLovin MAX` warnings — these are informational. The SDK auto-fixes the resulting Android / iOS conflicts:

| Issue | Auto-fix |
|---|---|
| Android Gradle duplicate-class (e.g. Maio aar+jar) | **Noctua → Android → Fix Gradle Duplicate Dependencies** — patches `mainTemplate.gradle`. Also injected on every Android build. |
| iOS CocoaPods version conflicts (e.g. ByteDance, BidMachine, PubMatic, IronSource, Mintegral, DT Exchange, Moloco) | **Noctua → iOS → Fix CocoaPods Conflicts** — patches `Library/PackageCache` XML + `manifest.json`, removes duplicate cocoapods repo. **Check CocoaPods Versions** menu inspects without modifying. |
| Yandex iOS linker error (`AppMetricaLibraryAdapter.shared.unsafeMutableAddressor`) | Auto-applied at iOS build |
| Dynamic XCFramework missing (e.g. BigO Ads) | Auto-embedded at iOS build |

**Adapters NOT in the Integration Manager** (no UPM package) require manual install:

- **AppLovin MAX:** VK Ad Network, Amazon Publisher Services, YSO Network → use **AppLovin → Integration Manager** (Unity menu) to download as native plugin files. Noctua cannot detect / update / remove these.
- **AdMob:** any adapter not on OpenUPM — use Google's External Dependency Manager or import the `.unitypackage` from the [AdMob mediation guides](https://developers.google.com/admob/unity/mediation).

For custom / proprietary networks: follow the network's own integration docs. Noctua still applies Android duplicate-class detection and runtime tracking, but does not validate version compatibility for unlisted adapters.

## Implementation guide — event subscription pattern

Subscribe in `OnEnable` and unsubscribe in `OnDisable`. Use **named methods** (not lambdas) so `+=` and `-=` reference the same delegate. Always guard `Noctua.IAA == null`:

```csharp
using UnityEngine;
using com.noctuagames.sdk;
#if UNITY_ADMOB
using GoogleMobileAds.Api;
#endif

public class AdManager : MonoBehaviour
{
    private void OnEnable()
    {
        if (Noctua.IAA == null) return;

        Noctua.IAA.OnAdDisplayed          += HandleAdDisplayed;
        Noctua.IAA.OnAdClosed             += HandleAdClosed;
        Noctua.IAA.OnAdFailedDisplayed    += HandleAdFailed;
        Noctua.IAA.OnAdNotAvailable       += HandleAdNotAvailable;
        Noctua.IAA.OnAdClicked            += HandleAdClicked;
        Noctua.IAA.OnAdImpressionRecorded += HandleAdImpression;

        // Subscribe to BOTH reward events — see "Reward callbacks in hybrid mode" below.
#if UNITY_ADMOB
        Noctua.IAA.AdmobOnUserEarnedReward    += HandleAdmobReward;
#endif
#if UNITY_APPLOVIN
        Noctua.IAA.AppLovinOnUserEarnedReward += HandleAppLovinReward;
#endif
    }

    private void OnDisable()
    {
        if (Noctua.IAA == null) return;

        Noctua.IAA.OnAdDisplayed          -= HandleAdDisplayed;
        Noctua.IAA.OnAdClosed             -= HandleAdClosed;
        Noctua.IAA.OnAdFailedDisplayed    -= HandleAdFailed;
        Noctua.IAA.OnAdNotAvailable       -= HandleAdNotAvailable;
        Noctua.IAA.OnAdClicked            -= HandleAdClicked;
        Noctua.IAA.OnAdImpressionRecorded -= HandleAdImpression;

#if UNITY_ADMOB
        Noctua.IAA.AdmobOnUserEarnedReward    -= HandleAdmobReward;
#endif
#if UNITY_APPLOVIN
        Noctua.IAA.AppLovinOnUserEarnedReward -= HandleAppLovinReward;
#endif
    }

    private void HandleAdDisplayed()         { /* pause game audio, freeze time */ }
    private void HandleAdClosed()            { Time.timeScale = 1f; }
    private void HandleAdFailed()            { /* native render error */ }
    private void HandleAdNotAvailable(string format) { /* cap / cooldown / no-fill */ }
    private void HandleAdClicked()           { }
    private void HandleAdImpression()        { }

#if UNITY_ADMOB
    private void HandleAdmobReward(Reward r)         { GrantReward(r.Amount); }
#endif
#if UNITY_APPLOVIN
    private void HandleAppLovinReward(MaxSdk.Reward r) { GrantReward(r.Amount); }
#endif
}
```

## Implementation guide — Reward callbacks in hybrid mode

In hybrid mode the SDK falls back to the secondary network on no-fill. **Whichever network actually serves the rewarded ad is the one whose reward callback fires.** Always subscribe to both with `#if` guards — single-subscription games miss rewards on fallback.

`Noctua.IAA.OnUserEarnedReward` (network-agnostic) does **not** exist in the public surface; use the per-network events.

## Implementation guide — Rewarded ad failure handling

Reset your reward-pending flag in **both** `OnAdNotAvailable` AND `OnAdFailedDisplayed`. Missing either one leaves the flag set and grants an unearned reward when the next ad completes.

```csharp
private bool _rewardPending;

public void OnExtraLifeRequested()
{
    _rewardPending = true;
    Noctua.IAA?.ShowRewardedAd("extra_life");
}

private void HandleAdNotAvailable(string format)
{
    if (format == AdFormatKey.Rewarded) _rewardPending = false;
}

private void HandleAdFailed()
{
    _rewardPending = false;
}

#if UNITY_ADMOB
private void HandleAdmobReward(Reward r)         { GrantIfPending(); }
#endif
#if UNITY_APPLOVIN
private void HandleAppLovinReward(MaxSdk.Reward r) { GrantIfPending(); }
#endif

private void GrantIfPending()
{
    if (!_rewardPending) return;
    _rewardPending = false;
    GiveExtraLife();
}
```

`AdFormatKey.Rewarded` / `Interstitial` / `Banner` / `AppOpen` / `RewardedInterstitial` are SDK-defined constants you compare against the `format` argument.

## Implementation guide — Banner creation order

`CreateBannerViewAdAdmob` / `CreateBannerViewAdAppLovin` must run **after** `Noctua.InitAsync()`. Creating early can cause Remote Config IAA settings to rebuild `AdmobManager` and reset the banner position to the default `Top` — your configured `Bottom` would silently disappear.

```csharp
private async void Start()
{
    await Noctua.InitAsync();

#if UNITY_ADMOB
    Noctua.IAA?.CreateBannerViewAdAdmob(AdSize.Banner, AdPosition.Bottom);
#endif
#if UNITY_APPLOVIN
    Noctua.IAA?.CreateBannerViewAdAppLovin(Color.white, MaxSdkBase.AdViewPosition.BottomCenter);
#endif

    Noctua.IAA?.ShowBannerAd();
}
```

In hybrid mode both creation calls run, but only the network selected by `ad_format_overrides[banner]` actually displays — the unused network's banner is a no-op.

Use `HideBannerAd()` (network-agnostic) over `HideAppLovinBanner()` / `DestroyBannerAppLovin()` in any cross-mediation code (e.g. an IAP "remove ads" path) — it routes to whichever network actually shows the banner and is a safe no-op otherwise.

## Implementation guide — App Open auto-show hook

When the Noctua team enables `app_open_auto_show` in remote config, the SDK shows an app-open ad on every foreground transition. **You must call `OnApplicationForeground()` from `OnApplicationPause`**:

```csharp
void OnApplicationPause(bool paused)
{
    if (!paused)
        Noctua.IAA?.OnApplicationForeground();
}
```

The SDK handles cooldown, frequency cap, and 4-hour expiry (AdMob) internally. To show manually instead:

```csharp
if (Noctua.IAA?.IsAppOpenAdReady() == true)
    Noctua.IAA?.ShowAppOpenAd();
```

## Implementation guide — frequency caps & cooldowns

All managed by the Noctua team via remote config. The schema for reference:

```json
"iaa": {
  "frequency_caps": {
    "interstitial":          { "max_impressions": 5,  "window_seconds": 3600 },
    "rewarded":              { "max_impressions": 10, "window_seconds": 3600 },
    "rewarded_interstitial": { "max_impressions": 3,  "window_seconds": 3600 },
    "app_open":              { "max_impressions": 3,  "window_seconds": 3600 }
  },
  "cooldown_seconds": {
    "interstitial": 30,
    "rewarded":      0,
    "app_open":     60
  }
}
```

Window is rolling. `0` = unlimited. Caps and cooldowns are evaluated independently — both must pass for an ad to display. `frequency_caps` and `cooldown_seconds` merge **field-by-field** between local config and the server response: a partial server payload that only overrides `interstitial.max_impressions` keeps the local `interstitial.window_seconds` and the entire local `app_open` block.

When a cap or cooldown blocks a show call, the SDK fires `OnAdNotAvailable(format)` instead of displaying.

## Implementation guide — Hybrid fallback flow

Every show call is **stateless** — the primary network is always tried first. Order:

1. Frequency cap / cooldown blocked? → `OnAdNotAvailable` fires immediately, no network contacted.
2. Network selection → `ad_format_overrides` (highest priority) → dynamic optimization (if enabled and no override) → primary by default.
3. CPM floor check on selected network → HardFail skips to the other network.
4. Ad availability → if selected has no fill, fall back to the other network. If both fail, `OnAdNotAvailable(format)` fires.

`IsInterstitialReady()` / `IsRewardedAdReady()` check **both** networks in hybrid mode and return `true` if either has a loaded ad and frequency/cooldown allows showing — useful for greying out buttons.

## Implementation guide — main-thread safety with raw AdMob events

`Noctua.IAA.*` events are already main-thread-safe (`MediationManager` uses `PostToMainThread` internally). **You only need to worry about thread safety when subscribing to raw `GoogleMobileAds.Api` events directly** — those fire on a background thread and crash with `UnityException: get_transform can only be called from the main thread`.

Wrap UnityEngine code in `MobileAdsEventExecutor.ExecuteInUpdate`; keep telemetry / `Noctua.Event.Track*` outside the wrap so impression-level data records synchronously even if the user kills the app before the next frame:

```csharp
using GoogleMobileAds.Api;
using GoogleMobileAds.Common;

interstitialAd.OnAdFullScreenContentClosed += () =>
{
    AnalyticsBackend.OnAdClosed("interstitial");   // safe off-thread

    MobileAdsEventExecutor.ExecuteInUpdate(() =>
    {
        Time.timeScale = 1f;
        _hudCanvas.SetActive(true);
    });
};
```

For hybrid (AppLovin + AdMob) projects, guard with `#if UNITY_ADMOB` so AppLovin-only builds compile — `MobileAdsEventExecutor` lives in `GoogleMobileAds.Common`. AppLovin MAX delivers callbacks on the main thread already; no wrap needed.

**Do NOT use the global switch** `MobileAds.RaiseAdEventsOnUnityMainThread = true` — Google documents up to a 30 % revenue-reporting discrepancy when the app pauses or backgrounds because deferred callbacks drop on close. Per-callback `ExecuteInUpdate` keeps revenue accurate because Noctua records revenue synchronously before the hop.

## Implementation guide — debugging tools

```csharp
// Mediation-aware status
string mediator = Noctua.IAA.MediationType;          // "admob" or "applovin"
bool   hybrid   = Noctua.IAA.IsHybridMode;           // both networks active
bool   ready    = Noctua.IAA.IsAppOpenAdReady();

// Mediation Debugger — full waterfall + adapter list
Noctua.IAA?.ShowMediationDebugger("admob");      // AdMob Ad Inspector (real device only)
Noctua.IAA?.ShowMediationDebugger("applovin");   // AppLovin Mediation Debugger (device + emulator)
Noctua.IAA?.ShowMediationDebugger();             // defaults to primary

// Creative Debugger — AppLovin only
Noctua.IAA?.ShowCreativeDebugger();

// Test devices — register before any ads load
Noctua.IAA?.SetTestDeviceIds(new List<string>
{
    "ADMOB_TEST_DEVICE_ID",
    "APPLOVIN_ADVERTISING_ID"
});
```

**AppLovin Mediation Debugger adapter statuses:** `Verified` (green) / `Initialized` / `Missing` / `SDK Version Mismatch` / `No Ads`. Tap a row for SDK + adapter version + per-format readiness. Install missing adapters via Noctua Integration Manager.

**AdMob Ad Inspector** requires a real device + real AdMob account + `UNITY_ADMOB` defined. Cross-reference with AppLovin's Mediation Debugger to find adapter gaps.

**Test device IDs**: get the AdMob ID from logcat `I/Ads: Use RequestConfiguration.Builder.setTestDeviceIds(...)`. AppLovin uses the device's GAID (Android) / IDFA (iOS).

## Implementation guide — log-pattern reference for adapter debugging

Filter device logs to identify the winning adapter and timeouts:

```bash
# Winning adapter (AdMob) + AppLovin waterfall
adb logcat -s Unity | grep -iE "ad loaded|ad failed|AdSourceName|WaterfallInfo"

# Failures + timeouts only
adb logcat -s Unity | grep -iE "failed|timeout|no fill"
```

| Pattern | Meaning |
|---|---|
| `AdSourceName` | AdMob: which mediation adapter won |
| `WaterfallInfo` | AppLovin: full waterfall dump per format |
| `LatencyMillis` > ~5000 | Adapter timed out |
| `wf_*_request_adunit_timeout` | One adapter timed out, waterfall moved on |
| `wf_*_request_finished_failed` | All adapters exhausted, no fill |
