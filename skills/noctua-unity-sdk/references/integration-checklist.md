# Pre-launch Integration Checklist

> **Sources** — Tutorials: https://docs.noctua.gg/docs/integration-checklist · https://docs.noctua.gg/docs/usage-requirements · https://docs.noctua.gg/docs/installation · Repo: [package.json](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/package.json), [Editor/Build/BuildPostProcessor.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Editor/Build/BuildPostProcessor.cs)

Use this single page to verify a Noctua SDK integration is production-ready. **Run every step on a real device — Unity Editor and emulators are not sufficient.**

## Required platform versions

| Slot | Floor | Notes |
|---|---|---|
| Unity | 2022.3.62f2 LTS / 6000.3.6f1 LTS | Team policy. `package.json` declares `2021.3` only because UPM enforces a major-version minimum. |
| Android | OS 9 (Pie), `minSdkVersion ≥ 28`, `targetSdkVersion = 35` | `targetSdkVersion = 35` is mandatory for Play Console submissions from August 2025. |
| iOS | Deployment target 15.0, Xcode 16.0+ | iOS 15+ is the SDK floor for both Cocoapods + Swift bridge. |
| Gradle | 8.6.0+, JDK 17+, AGP 8.4.0+ | See https://docs.noctua.gg/troubleshoot/gradle-update for stepwise upgrade. |

Bundled iOS native dependency versions (must match if your game pulls these directly):

| iOS SDK | Version |
|---|---|
| Adjust | 5.4.4 |
| Firebase | 12.2.0 (Unity Firebase 13.2.0) |
| Facebook | 18.0.0 (Unity Facebook 18.0.0) |

Android allows version mismatch with the bundled SDKs.

## Required `noctuagg.json` keys

Place at `Assets/StreamingAssets/noctuagg.json`. The minimum viable file:

```json
{
  "clientId": "<from-Noctua-team>",
  "noctua": {
    "gameId": "<from-Noctua-team>",
    "iaaEnabled": true,
    "sandboxEnabled": false,
    "offlineFirstEnabled": true
  }
}
```

`Noctua.InitAsync()` throws `NoctuaException(Application)` if the file is missing, malformed, or `clientId` is empty. Full schema in [noctuagg-json.md](noctuagg-json.md).

## Mandatory Unity Player settings

- **Edit → Project Settings → Player → Version** — set to a SemVer string (e.g. `1.4.2`). The SDK requires `Application.version` for analytics tagging and version-gated remote config.
- **Android → Publishing Settings:** enable
  - Custom Main Manifest
  - Custom Main Gradle Template
  - Custom Gradle Properties Template
  - Custom Gradle Settings Template (Unity 2022.3+ only)
- **Android → Other Settings:** Minimum API Level **28**, Target API Level **35**.
- **iOS → Other Settings:** Target minimum iOS Version **15.0**.

## Mandatory Info.plist keys (iOS)

- `NSUserTrackingUsageDescription` — required for ATT prompt; ad attribution depends on it.
- `NSCameraUsageDescription` — required to prevent crashes when the customer-service screenshot flow accesses the camera (even if the user never invokes it).
- `NSPhotoLibraryUsageDescription` (if your bug-reporter screenshots include the photo library).

The build post-processor injects defaults if these keys are missing, but explicit values give you control over the prompt copy.

## Mandatory Android Manifest keys

The post-processor adds these automatically when needed (Facebook, Firebase, Adjust). Don't remove them:

- Internet permission
- `<receiver>` registrations for Firebase Cloud Messaging
- `<meta-data>` blocks for Facebook App ID and Client Token (when Facebook SDK is present)

## Store-side prerequisites

### App Store Connect
- App identifier registered, bundle ID matches the build
- In-App Purchases created with **Product IDs** matching the strings used by `Noctua.IAP.PurchaseItemAsync`
- Sandbox tester accounts created and signed in to a test device
- ATT prompt copy reviewed (`NSUserTrackingUsageDescription`)

### Google Play Console
- App created, package name matches the build
- In-app products created in **Monetize → Products** with matching Product IDs
- Closed testing track set up if testing IAPs (Play won't allow IAP tests on internal testing without a license-tester license)
- Target API level alert dismissed (set `targetSdkVersion = 35`)

## Test-account setup

- **Sandbox tester** in App Store Connect for iOS IAPs
- **License tester** in Google Play Console for Android IAPs (Settings → License testing)
- Test device IDs registered for AppLovin / AdMob during dev (`Noctua.IAA.SetTestDeviceIds(...)`) — **remove or empty the list before release**

## Sandbox flag — never ship `sandboxEnabled: true`

`noctua.sandboxEnabled` gates more than the in-app Inspector overlay — it also switches API base URLs to staging. Production builds **must** ship with `sandboxEnabled: false`. Either edit `noctuagg.json` directly before each release build, or guard with `#if DEVELOPMENT_BUILD` in a build pre-processor.

## Build-time auto-patches (verify by reading the build log)

The SDK post-processor patches these automatically — verify they fire on a clean build:

| Platform | Patch | Log signal |
|---|---|---|
| Android | Inject Gradle duplicate-class fix when overlapping ad adapters detected | `[NoctuaSDK] Injected Gradle duplicate dependency fix for: …` |
| iOS | Embed dynamic XCFrameworks (e.g. BigO Ads) | `[NoctuaSDK] Embedded XCFramework …` |
| iOS | Inject SKAdNetwork identifiers into Info.plist | `[NoctuaSDK] Wrote N SKAdNetworkItems` |
| iOS | Inject Adjust attribution + Facebook init keys | `[NoctuaSDK] Patched Info.plist for Adjust/Facebook` |
| iOS | Inject `-FIRDebugEnabled` when sandbox build | `[NoctuaSDK] Enabled Firebase debug` |

Number of SKAdNetwork identifiers depends on installed networks — grep `Editor/Build/BuildPostProcessor.cs` for `skadnetwork` to see the canonical list.

## Code-level checklist

- `Noctua.IAP.OnPurchaseDone` and `OnPurchasePending` wired BEFORE `Noctua.InitAsync()` in the same execution flow (per [iap.md](iap.md#implementation-guide--purchase-flow-with-onpurchasedone-wiring))
- `OnAccountChanged` / `OnAccountDeleted` wired before `InitAsync`
- All async SDK calls in `try { } catch (NoctuaException) { } catch (Exception) { }` — never silent
- `Noctua.IAA?.` (null-conditional) used everywhere — covers the case where ads are disabled at the dashboard
- Both `OnAdNotAvailable` AND `OnAdFailedDisplayed` reset reward-pending flags
- Both `AdmobOnUserEarnedReward` AND `AppLovinOnUserEarnedReward` subscribed (with `#if` guards) — required for hybrid mediation fallback
- `OnApplicationForeground()` called from `OnApplicationPause(false)` if `app_open_auto_show` is on
- Test device IDs / `SetTestDeviceIds` calls removed before the production build
- No `Debug.Log` statements expose access tokens or user IDs in production
- `noctuagg.json → noctua.sandboxEnabled = false` for the production build

## Verification on real device

1. **Clean install:** uninstall → install → first launch should not crash.
2. **Authentication:** guest auto-login on a fresh install returns a valid `UserBundle`.
3. **IAP round-trip:** purchase → `OnPurchaseDone` → grant content. Test cancel and a slow-payment / pending purchase path.
4. **Ad formats:** banner / interstitial / rewarded / app-open all show on a registered test device. Real ads load without the "Test Ad" watermark on a non-test device.
5. **Event reach:** at least one custom event reaches **Firebase DebugView** (Android: `adb shell setprop debug.firebase.analytics.app <pkg>`; iOS: add `-FIRDebugEnabled` scheme arg).
6. **Restore (iOS):** Restore Purchases button re-grants non-consumables.
7. **Offline:** airplane mode → SDK initializes, events buffer, IAP shows reconnect dialog, customer service shows reconnect dialog.
8. **ATT denied path (iOS):** install on a fresh device, deny ATT prompt, confirm ads still show and game still functions.
9. **Backgrounding:** app → background → foreground; auth still valid, app-open ad shows (if enabled), state restored.
10. **Inspector check (sandbox build only):** shake / 4-finger tap opens the overlay, events progress to `Acknowledged`, HTTP traffic appears clean.

## Final submission gate

- [ ] `noctuagg.json` has production `clientId` and `gameId` (NOT sandbox)
- [ ] `sandboxEnabled = false`
- [ ] `Application.version` matches the SemVer in app stores
- [ ] Android `targetSdkVersion = 35`
- [ ] iOS `NSUserTrackingUsageDescription` + `NSCameraUsageDescription` present
- [ ] No test device IDs registered
- [ ] No `Debug.Log` statements expose secrets
- [ ] Tested on **physical Android device** + **physical iPhone**
- [ ] Clean-install smoke test passed on both platforms
