# Installation

Noctua SDK is a Unity Package Manager (UPM) git package. No .unitypackage download.

## Prerequisites

- **Unity 2021.3+** (specified in `Packages/com.noctuagames.sdk/package.json`)
- **Android:** Gradle template + Android Resolver (EDM4U) — SDK pulls in EDM4U automatically.
- **iOS:** Xcode 15+, CocoaPods. Minimum iOS deployment target **15.0**.
- Git installed (UPM resolves git packages).

## Step 1 — add to `Packages/manifest.json`

```json
{
  "dependencies": {
    "com.noctuagames.sdk": "https://github.com/noctuagames/noctua-sdk-unity-upm.git#0.109.0"
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
- `NoctuaSDK` **0.35.0** with sub-specs:
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

If the game uses ads (`iaa.enabled: true` in `noctuagg.json`), open **`Noctua > Noctua Integration Manager`** and click **Recommended Setup**. This installs:

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
