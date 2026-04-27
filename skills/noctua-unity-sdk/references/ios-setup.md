# iOS Setup

> **Sources** — Official: https://docs.noctua.gg/docs/installation, https://docs.noctua.gg/docs/ios-native, /ios-native/custom-event-tracking, /ios-native/tracking-revenue · Repo: [Editor/Build/BuildPostProcessor.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Editor/Build/BuildPostProcessor.cs), [Editor/Build/CocoaPodsConflictFixer.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Editor/Build/CocoaPodsConflictFixer.cs), [Editor/Dependencies/NativePluginDependencies.xml](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Editor/Dependencies/NativePluginDependencies.xml)

iOS integration is handled almost entirely by `BuildPostProcessor`. Game-side changes: a Player Settings tweak and optional ATT handling.

Source: `Packages/com.noctuagames.sdk/Editor/Build/BuildPostProcessor.cs`, `Editor/Build/CocoaPodsConflictFixer.cs`, `Editor/Dependencies/NativePluginDependencies.xml`.

## Minimum Player Settings

In **`Project Settings > Player > iOS`**:

| Setting | Value |
|---|---|
| Target minimum iOS | **15.0** (pod spec requirement) |
| Architecture | ARM64 |
| Target Device | iPhone + iPad (or your preference) |
| Bundle Identifier | (from Apple Developer) |

## CocoaPods

Pod `NoctuaSDK` 0.35.0 with sub-specs is declared via EDM4U. Pod install runs automatically on build. Sub-specs pulled:

- `NoctuaSDK` (base + internal SDK)
- `NoctuaSDK/Adjust`
- `NoctuaSDK/FirebaseAnalytics`
- `NoctuaSDK/FirebaseMessaging`
- `NoctuaSDK/FirebaseCrashlytics`
- `NoctuaSDK/FirebaseRemoteConfig`
- `NoctuaSDK/FacebookSDK`

## `Info.plist` auto-injection

`BuildPostProcessor.ExposeLogFiles` writes:

```xml
<key>UIFileSharingEnabled</key>                 <true/>
<key>LSSupportsOpeningDocumentsInPlace</key>    <true/>
<key>NSAdvertisingAttributionReportEndpoint</key>
<string>https://adjust-skadnetwork.com</string>
```

### SKAdNetwork identifiers

Auto-injects **~42 `SKAdNetworkItems`** (verified count from `Editor/Build/BuildPostProcessor.cs` at v0.109.0; partial list):

| Network | ID |
|---|---|
| Facebook (Meta) | `4fzdc2evr5.skadnetwork` |
| Google | `cstr6suwn9.skadnetwork` |
| AppLovin | `v9wttpbfk9.skadnetwork` |
| Unity Ads | `7ug5zh24hu.skadnetwork` |
| Vungle | `n6fk4nfna4.skadnetwork` |
| IronSource, Chartboost, Mintegral, Fyber, BidMachine, InMobi, Smaato, TapJoy, … | (see `BuildPostProcessor.cs:30-73`) |

Do not hand-edit — the post-processor overwrites on each build.

## Firebase (`GoogleService-Info.plist`)

Place at `Assets/StreamingAssets/GoogleService-Info.plist`. `BuildPostProcessor.IntegrateGoogleServices` copies it into the Xcode project at post-process. Remove the file from `StreamingAssets/` to disable Firebase on iOS (the post-processor will remove it from the Xcode project next build).

## AppTrackingTransparency (ATT)

Required for IDFA-based attribution (Adjust, AdMob personalized ads). Add usage description to your **iOS Player Settings → Other Settings → Tracking Description**:

```
This identifier will be used to deliver personalized ads to you.
```

The SDK does **not** auto-present the ATT prompt — call it yourself at a natural moment (after onboarding, before first ad):

```csharp
#if UNITY_IOS
using Unity.Advertisement.IosSupport; // or your own P/Invoke wrapper

if (ATTrackingStatusBinding.GetAuthorizationTrackingStatus()
    == ATTrackingStatusBinding.AuthorizationTrackingStatus.NOT_DETERMINED)
{
    ATTrackingStatusBinding.RequestAuthorizationTracking();
}
#endif
```

## App Transport Security

The SDK uses HTTPS endpoints only — default ATS is fine. If you add custom HTTP endpoints, declare exceptions in Player Settings rather than disabling ATS globally.

## Push notifications

If using FCM, enable in Xcode capabilities:
- Push Notifications
- Background Modes → Remote notifications

`NoctuaSDK/FirebaseMessaging` sub-spec provides the iOS-side handler.

## Universal Links / deep links

If you rely on Noctua's web-to-app handoff (password reset, social login return), configure Associated Domains in Xcode capabilities with your Noctua-provided domain.

## CocoaPods conflict fixer

**`Noctua > iOS > Fix CocoaPods Conflicts`** (menu greyed-out unless build target is iOS):

- Patches `GoogleMobileAdsDependencies.xml` in `Library/PackageCache` to align GMA constraint with installed adapter version
- Removes duplicate `~/.cocoapods/repos/cocoapods` repo (a frequent source of pod install failures)
- Detects 7+ cross-catalog conflicts (AppLovin, BidMachine, Vungle, Mintegral, UnityAds, Fyber, Verve)
- Fires a warning at Editor startup when iOS is active and conflicts are detected

### Maio is mutually exclusive

`com.applovin.mediation.adapters.maio.ios 2.1.6.0` pins `MaioSDK-v2 = 2.1.6`.
`com.google.ads.mobile.mediation.maio 3.1.6`  pins `MaioSDK-v2 = 2.2.1`.

These **cannot coexist**. If both are installed, `Fix CocoaPods Conflicts` reports `⚠ MUTUALLY EXCLUSIVE — remove one` and intentionally skips auto-patch. Uninstall one in Integration Manager. **Recommendation:** keep Maio only under AppLovin MAX (the primary mediator) — Maio demand still serves without the AdMob adapter.

See [editor-tooling.md](editor-tooling.md) for the full Integration Manager reference.

## Common build errors

| Error | Cause | Fix |
|---|---|---|
| `pod install` fails with `MaioSDK-v2` conflict | Both AppLovin Maio and AdMob Maio installed | Uninstall one via Integration Manager |
| `Google-Mobile-Ads-SDK` version mismatch | Adapter requires newer GMA than installed | Integration Manager → Recommended Setup (installs conflict-free combo) or run Fix CocoaPods Conflicts |
| Xcode: missing `FirebaseCore` | `GoogleService-Info.plist` missing from StreamingAssets | Add it and rebuild |
| Adjust not tracking installs | `NSAdvertisingAttributionReportEndpoint` missing | Update to SDK 0.109.0+ (auto-injected) |
| ATT prompt never appears | Tracking Description missing in Player Settings | Add under Player Settings → iOS → Other Settings |
| Ad fills in debug but not release | IDFA unavailable because ATT denied | Add ATT prompt call; test on a fresh device |

## iOS app release checklist

Before App Store submission:
- [ ] `noctuagg.json → noctua.sandboxEnabled: false`
- [ ] `noctuagg.json → adjust.ios.environment: "production"`
- [ ] Replace test ad unit IDs with production IDs in `iaa.networks.*.ad_formats.*.ios.ad_unit_id`
- [ ] Verify `GoogleService-Info.plist` is the production Firebase project
- [ ] Tracking Description set; ATT prompt tested on-device
- [ ] `NSPrivacyAccessedAPITypes` declared (iOS 17.4+) — SDK 0.109.0 includes the required manifest
