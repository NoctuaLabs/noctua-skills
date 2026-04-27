# Installation

> **Sources** — Official: https://docs.noctua.gg/docs/installation · https://docs.noctua.gg/docs/usage-requirements · https://docs.noctua.gg/docs/integration-checklist · https://docs.noctua.gg/docs/introduction · Repo: [package.json](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/package.json), [Editor/Dependencies/NativePluginDependencies.xml](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Editor/Dependencies/NativePluginDependencies.xml)

Noctua SDK is a Unity Package Manager (UPM) git package. No .unitypackage download.

## Prerequisites

- **Unity 2022.3.62f2 or newer** (LTS — team-supported floor). The repo's `package.json` declares `"unity": "2021.3"` because UPM only supports a major-version minimum, and the README mirrors that as `2021.3+`. For production support use 2022.3.62f2 or later.
- **Android:** Gradle template + Android Resolver (EDM4U) — SDK pulls in EDM4U automatically.
- **iOS:** Xcode 15+, CocoaPods. Minimum iOS deployment target **15.0**.
- Git installed (UPM resolves git packages).

> **Repo URL note:** the canonical public mirror is `github.com/NoctuaLabs/noctua-unity-sdk-upm`. The repo's own `README.md` (which still pins `#0.101.0`) and `CLAUDE.md` reference older URLs (`noctuagames/noctua-sdk-unity-upm`, `gitlab.com/evosverse/...`) — do not copy those install lines verbatim.

## Step 1 — add to `Packages/manifest.json`

```json
{
  "dependencies": {
    "com.noctuagames.sdk": "https://github.com/NoctuaLabs/noctua-unity-sdk-upm.git#0.109.0"
  }
}
```

The fragment (`#0.109.0`) is a git tag. For a specific commit use `#<sha>`; for "always latest" omit the fragment (not recommended for production).

Unity resolves on next focus. UPM pulls two managed dependencies transitively:

| Package | Version | Purpose |
|---|---|---|
| `com.google.external-dependency-manager` | `v1.2.183` (git UPM) | EDM4U — resolves native Android / iOS dependencies |
| `com.unity.nuget.newtonsoft-json` | `3.2.1` | `noctuagg.json` parsing |

(Source: `Packages/com.noctuagames.sdk/package.json`)

## Step 2 — resolve native dependencies

Native SDKs are declared in `Packages/com.noctuagames.sdk/Editor/Dependencies/NativePluginDependencies.xml` and resolved by EDM4U.

### Android (Gradle)
- `com.noctuagames.sdk:noctua-android-sdk:0.31.0`
- `com.google.guava:guava:31.1-android`

Run **`Assets > External Dependency Manager > Android Resolver > Force Resolve`** after install (or enable auto-resolve). This writes `Assets/Plugins/Android/mainTemplate.gradle` entries.

**Requires** custom Gradle templates — enable in `Project Settings > Player > Android > Publishing Settings`:
- `Custom Main Gradle Template`
- `Custom Gradle Properties Template`
- `Custom Launcher Gradle Template` (for IAA app-open auto-show)

### iOS (CocoaPods)
- `NoctuaSDK` **0.35.0** with sub-specs (verified against `Editor/Dependencies/NativePluginDependencies.xml`):
  - `/NoctuaInternalSDK` — internal core (always installed)
  - `/Adjust` — Adjust attribution
  - `/FirebaseAnalytics` — Firebase Analytics
  - `/FirebaseMessaging` — Firebase Cloud Messaging
  - `/FirebaseCrashlytics` — Firebase Crashlytics
  - `/FirebaseRemoteConfig` — Firebase Remote Config
  - `/FacebookSDK` — Meta App Events

Cocoapods min deployment target: **iOS 15.0**. Pods resolve when you **Build** from Unity (post-process step).

## Step 3 — add third-party assets the sample uses

The SDK itself does not require these, but the reference sample app uses them:

- **UniTask** (`com.cysharp.unitask`) — the SDK public API returns `UniTask`. Add via UPM:
  ```json
  "com.cysharp.unitask": "https://github.com/Cysharp/UniTask.git?path=src/UniTask/Assets/Plugins/UniTask"
  ```
- **TextMesh Pro** (`com.unity.textmeshpro`) — for UI.

## Step 4 — create `Assets/StreamingAssets/noctuagg.json`

This is **required** — `Noctua.InitAsync()` throws if the file is missing. See [noctuagg-json.md](noctuagg-json.md).

## Step 5 — Integration Manager (ads only)

If the game uses ads (`noctua.iaaEnabled: true` in `noctuagg.json`), open **`Noctua > Noctua Integration Manager`** and click **Recommended Setup**. This installs:

| Package | Version | Role |
|---|---|---|
| AppLovin MAX SDK | 8.6.2 | Primary mediation |
| AdMob (GMA) SDK | 11.0.0 | Secondary / cross-network demand |
| AppLovin → Google Android adapter | 25010000.0.0 | Routes AdMob demand on Android |
| AppLovin → Google iOS adapter | 13020000.0.0 | Routes AdMob demand on iOS |
| AppLovin → Ad Manager Android | 25010000.0.0 | Ad Manager demand (Android) |
| AppLovin → Ad Manager iOS | 13020000.0.0 | Ad Manager demand (iOS) |

This combo is **conflict-free** — `com.google.ads.mobile` 11.0.0 pins GMA iOS `~> 13.0.0` which satisfies the 13.2.0 required by the AppLovin adapter. See [editor-tooling.md](editor-tooling.md).

## Verify

After `Noctua.InitAsync()` succeeds, log console should show (with `sandboxEnabled: true`):

```
Noctua SDK initialized successfully
```

If init fails, check `Assets/StreamingAssets/noctuagg.json` exists and is valid JSON.

## Upgrading

Bump the fragment in `manifest.json` to the new tag (`#0.110.0` etc.), then `Packages > UnityEditor.PackageManager > Refresh`. Re-run `Force Resolve` (Android) / next build (iOS). Check `Packages/com.noctuagames.sdk/CHANGELOG.md` for breaking changes.

## Implementation guide — Unity Package Manager (recommended)

Per the official tutorial, the canonical end-user flow is:

1. **Window → Package Manager** in Unity.
2. Click the **`+`** button → **Add package from git URL…**.
3. (Skip if EDM4U is already installed) Add Google's External Dependency Manager:
   ```
   https://github.com/googlesamples/unity-jar-resolver.git?path=upm
   ```
4. Add the Noctua SDK:
   ```
   https://github.com/NoctuaLabs/noctua-unity-sdk-upm.git
   ```
   Append `#x.y.z` to pin a version (e.g. `#0.109.0`). Omitting the fragment resolves to the default branch — not recommended for production.

The Noctua team provides `noctuagg.json` plus any third-party config (`google-services.json`, `GoogleService-Info.plist`) — drop them into `Assets/StreamingAssets/`.

### iOS Resolver settings

Open **Assets → External Dependency Manager → iOS Resolver → Settings** and confirm **Cocoapods Integration** is set to add the iOS dependencies on build. The resolver runs `pod install` automatically when you Build from Unity.

## Implementation guide — App Tracking Transparency (iOS)

The Noctua SDK requires the ATT permission flow on iOS for ad attribution. Add `NSUserTrackingUsageDescription` to `Info.plist` (the SDK injects a default at build time but you can override) and prompt the user via Unity's `iOSDevice.RequestATTAuthorization` (or any equivalent native bridge) **before** the first ad request:

> Reference: https://docs.unity.com/en-us/grow/ads/ios-sdk/ios14/att-compliance

The game must continue to load and serve ads even when the ATT prompt is denied — the SDK degrades attribution but does not refuse to show ads.

## Implementation guide — `NSCameraUsageDescription` (iOS)

The customer-service / bug-report flow can ask for a screenshot, which on iOS triggers a camera permission check. Add to `Info.plist`:

```xml
<key>NSCameraUsageDescription</key>
<string>The camera is used to capture screenshots for bug reports and customer support.</string>
```

iOS will crash the app on access if this key is missing, even when the user never invokes the screenshot path. Include it on every build.

## Platform versions and dependencies (verified Apr 2026)

From https://docs.noctua.gg/docs/usage-requirements:

- **Unity:** 2022.3.62f2 LTS or 6000.3.6f1 LTS (team-supported floor; `package.json` declares `2021.3` because UPM only enforces a major-version minimum).
- **Android:** OS 9 (Pie) minimum; `targetSdkVersion = 35` (mandatory for Play Console submissions from August 2025); `minSdkVersion ≥ 28` for new submissions.
- **iOS:** deployment target 15.0; Xcode 16.0+.
- **Gradle:** 8.6.0+, JDK 17+, Android Gradle Plugin 8.4.0+.
- **`Application.version`:** mandatory — must be a SemVer string (Edit → Project Settings → Player → Version).

### Native iOS dependency versions (Noctua-bundled)

The SDK already bundles Firebase / Adjust / Facebook on iOS. If your game also pulls these in directly, **versions must match exactly** — mismatches cause symbol/linker conflicts. Android has no such restriction.

| iOS SDK | Version |
|---|---|
| Adjust | 5.4.4 |
| Firebase | 12.2.0 (Unity Firebase SDK 13.2.0) |
| Facebook | 18.0.0 (Unity Facebook SDK 18.0.0) |

## PlayerPrefs keys reserved by the SDK

The SDK persists state in PlayerPrefs. **Do not delete these keys** in a "reset save" flow — the list is from https://docs.noctua.gg/docs/usage-requirements:

- `NoctuaFirstOpen`
- `NoctuaAccountContainer.UseFallback`
- `NativeGalleryPermission`
- `NoctuaWebContent.Announcement.LastShown`
- `NoctuaAccountContainer`
- `NoctuaPendingPurchases`
- `NoctuaLocaleCountry`
- `NoctuaLocaleCurrency`
- `NoctuaLocaleUserPrefsLanguage`
- `NoctuaUnpairedOrders`
- `NoctuaPurchaseHistory`
- `NoctuaEvents`
- `NoctuaAccessToken`
- `NoctuaCurrentStageLevel`
- `NoctuaCurrentStageMode`

If your game wipes PlayerPrefs, exclude every key matching the `Noctua*` prefix and `NativeGalleryPermission`.
