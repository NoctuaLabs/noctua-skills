# Android Setup

> **Sources** — Official: https://docs.noctua.gg/docs/installation, https://docs.noctua.gg/docs/android-native, /android-native/custom-event-tracking, /android-native/tracking-revenue · Repo: [Editor/Build/BuildPostProcessor.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Editor/Build/BuildPostProcessor.cs), [Editor/Dependencies/NativePluginDependencies.xml](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Editor/Dependencies/NativePluginDependencies.xml)

Noctua SDK manages most Android configuration automatically via EDM4U and `BuildPostProcessor`. Game-side changes are minimal.

Source: `Packages/com.noctuagames.sdk/Editor/Build/BuildPostProcessor.cs`, `Editor/Dependencies/NativePluginDependencies.xml`.

## Minimum Player Settings

In **`Project Settings > Player > Android`**:

| Setting | Value |
|---|---|
| Minimum API Level | 24 (Android 7.0) |
| Target API Level | 34+ (required by Play Store) |
| Scripting Backend | **IL2CPP** (for ARM64 release) |
| Target Architectures | ARMv7 + ARM64 |
| Internet Access | Require |

## Custom Gradle templates

Enable under **`Project Settings > Player > Android > Publishing Settings`**:

- ✅ **Custom Main Gradle Template** — EDM4U writes native SDK deps here
- ✅ **Custom Launcher Gradle Template** — needed for IAA app-open auto-show
- ✅ **Custom Gradle Properties Template** — AndroidX + multidex
- ✅ **Custom Main Manifest** (optional — SDK can inject into default)

## Native dependencies (EDM4U injects)

From `NativePluginDependencies.xml`:

```gradle
dependencies {
    implementation 'com.noctuagames.sdk:noctua-android-sdk:0.31.0'
    implementation 'com.google.guava:guava:31.1-android'
}
```

Resolved by **`Assets > External Dependency Manager > Android Resolver > Force Resolve`** (or automatically on build).

## `gradle.properties`

Enable AndroidX and multidex:
```properties
android.useAndroidX=true
android.enableJetifier=true
android.enableMultidex=true
```

## Permissions (auto-injected)

The Noctua Android native SDK requests:
- `android.permission.INTERNET`
- `android.permission.ACCESS_NETWORK_STATE`
- `com.android.vending.BILLING` (Play Billing)
- Firebase Messaging permissions (if Firebase is configured)

Add these to your manifest only if Unity's auto-merge doesn't include them — usually unnecessary.

## `AndroidManifest.xml` auto-injection

`BuildPostProcessor.ModifyAndroidManifest` injects **Facebook App ID `<meta-data>`** when `facebook.android.appId` is set in `noctuagg.json`:

```xml
<meta-data
    android:name="com.facebook.sdk.ApplicationId"
    android:value="@string/facebook_app_id" />
<meta-data
    android:name="com.facebook.sdk.ClientToken"
    android:value="@string/facebook_client_token" />
```

Do not add these manually — the post-processor handles it.

## Firebase

Place `google-services.json` at `Assets/StreamingAssets/google-services.json`. EDM4U + Unity's Firebase integration copies it to the Gradle project at build time. Removing the file disables Firebase on Android.

## ProGuard / R8

The SDK ships consumer ProGuard rules via the AAR — no manual additions required for baseline integration. If you enable custom ProGuard, keep:

```
-keep class com.noctuagames.sdk.** { *; }
-keep class com.adjust.sdk.** { *; }
-keep class com.facebook.** { *; }
-keepattributes *Annotation*
```

## Play Billing library version

`com.noctuagames.sdk:noctua-android-sdk:0.31.0` targets Play Billing Library 7. If your project already declares a different billing version, remove it — let the SDK own this.

## Notifications / FCM

If using Firebase Cloud Messaging, add to `AndroidManifest.xml`:
```xml
<service
    android:name="com.noctuagames.sdk.MessagingService"
    android:exported="false">
    <intent-filter>
        <action android:name="com.google.firebase.MESSAGING_EVENT" />
    </intent-filter>
</service>
```

## Debugging builds

For sandbox / dev builds:
- Keep `noctuagg.json → noctua.sandboxEnabled: true` — spawns Noctua Inspector
- Use `adb logcat -s Unity:V Noctua:V` to see SDK logs (`NoctuaLogger` prefixes `[Noctua]`)
- Enable `Development Build` + `Script Debugging` in Build Settings

## Common build errors

| Error | Cause | Fix |
|---|---|---|
| `Duplicate class com.google.**` | Conflicting native deps | Let EDM4U own resolution — don't declare Play Services manually in custom gradle |
| `Manifest merger failed` on Facebook meta-data | `facebook.android.appId` missing | Add it to `noctuagg.json`, or remove the `facebook` block entirely |
| `INSTALL_FAILED_UPDATE_INCOMPATIBLE` | Signing mismatch | Standard Android — not SDK-related |
| `ClassNotFoundException: ...MessagingService` | FCM service declared but Firebase deps missing | Ensure `google-services.json` is present |
| Billing crash `BillingClient.newBuilder` | `com.android.billingclient` conflict | Remove manual billing dep — SDK provides it |
