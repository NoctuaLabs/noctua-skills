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
