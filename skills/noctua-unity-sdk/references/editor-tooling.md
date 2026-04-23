# Editor Tooling

The SDK ships two Unity Editor menu items under **`Noctua > ...`**.

Source: `Packages/com.noctuagames.sdk/Editor/Menu/NoctuaSDKMenu.cs`, `Editor/Build/CocoaPodsConflictFixer.cs`.

## `Noctua > Noctua Integration Manager`

Window for managing ad mediation SDK UPM packages. Writes directly to `Packages/manifest.json` and calls `UnityEditor.PackageManager.Client.Resolve()` — no manual refresh needed.

### Sections

#### Recommended Setup
One-click install of a pre-validated combo that runs AppLovin MAX + AdMob demand on both platforms without version conflicts:

| Package | Version | Role |
|---|---|---|
| `com.applovin.max.sdk` | 8.6.2 | AppLovin MAX SDK (wraps MAX 13.6.2) |
| `com.google.ads.mobile` | 11.0.0 | AdMob / GMA SDK |
| `com.applovin.mediation.adapters.google` (Android) | 25010000.0.0 | Routes AdMob demand via AppLovin (Android) |
| `com.applovin.mediation.adapters.google.ios` | 13020000.0.0 | Routes AdMob demand via AppLovin (iOS) |
| `com.applovin.mediation.adapters.ad-manager` (Android) | 25010000.0.0 | Google Ad Manager demand (Android) |
| `com.applovin.mediation.adapters.ad-manager.ios` | 13020000.0.0 | Google Ad Manager demand (iOS) |

**Why it's conflict-free:**
- `com.google.ads.mobile` 11.0.0 pins GMA iOS `~> 13.0.0` — satisfies AppLovin adapter's required 13.2.0
- GMA Android: AdMob 11.0.0 declares 25.0.0; Gradle resolves to 25.1.0 via the adapter target — same major series, backward-compatible

#### IAA Providers
Standalone toggle for AppLovin MAX SDK and AdMob SDK.

#### AppLovin MAX — Ad Network Adapters
22 adapters from `unity.packages.applovin.com`:
Facebook, Google AdMob, Google Ad Manager, Unity Ads, Vungle (Liftoff), Mintegral, ironSource, Chartboost, AdColor, BidMachine, Bigo, CriteoPublisher, Fyber (DT Exchange), HyBid (Verve), InMobi, LINE, Maio, Mobfox, Pangle, Smaato, TapJoy, Yandex.

#### AdMob — Mediation Adapters
17 adapters from `package.openupm.com`:
AppLovin, ChartboostSDK, Criteo, DTExchange, InMobi, ironSource, LINE, Maio, Meta, Mintegral, Pangle, Smaato, Tapjoy, UnityAds, Verve, Vungle, Yandex.

### How it works

Every install/update/remove action:
1. Edits `Packages/manifest.json` (adds/updates/removes dependency entry)
2. Calls `Client.Resolve()` — UPM re-resolves immediately
3. Refreshes scripting define symbols — `UNITY_APPLOVIN` and `UNITY_ADMOB` auto-toggled based on installed packages (fixed in SDK 0.96.0)

Version color coding: **green** = at Recommended Setup version, **amber** = newer version available. Click **→ Stable** to update.

### Adapter version encoding (AppLovin)

AppLovin UPM adapter versions encode the underlying native adapter version. Example: `25010000.0.0` wraps AppLovin's Android adapter `25.1.0.0` which wraps GMA Android 25.1.0. First segment = underlying SDK version.

### Adding a new adapter to the catalog

Edit `NoctuaSDKMenu.cs`:
1. Add entry to `maxAdapterPackages` (Android + iOS tuple) **or** `admobAdapterPackages`
2. Verify compatibility against the current Recommended Setup mediator version
3. AppLovin versions from `unity.packages.applovin.com/-/all`; AdMob from `package.openupm.com`

### Mutual exclusion detection

`NoctuaSDKMenu` marks mutually exclusive adapter pairs in the UI. The prime example:

| AppLovin adapter | AdMob adapter | Shared pod | AppLovin pins | AdMob pins |
|---|---|---|---|---|
| `com.applovin.mediation.adapters.maio.ios 2.1.6.0` | `com.google.ads.mobile.mediation.maio 3.1.6` | `MaioSDK-v2` | `= 2.1.6` | `= 2.2.1` |

Cannot coexist at any version. Install from one mediator only.

## `Noctua > iOS > Fix CocoaPods Conflicts`

Greyed-out unless build target is iOS.

### What it does

- Patches `GoogleMobileAdsDependencies.xml` in `Library/PackageCache` to align the GMA constraint with the installed adapter version
- Removes duplicate `~/.cocoapods/repos/cocoapods` repo (frequent root cause of pod install failures)
- Dynamically reads adapter versions from `Library/PackageCache` — no hardcoded versions
- Reports via dialog:
  - `✓ PATCHED` — conflict auto-fixed
  - `⚠ MUTUALLY EXCLUSIVE — remove one` — cannot be auto-patched (Maio scenario); user must uninstall one adapter
  - `ℹ NO CONFLICT` — current state is consistent

### Editor startup warning

When iOS is the active build target and a conflict is detected, an Editor startup warning fires automatically — run the menu item to inspect.

### Cache ephemeral warning

`Library/PackageCache` patches are **ephemeral** — reset when UPM refreshes the cache. The durable fix: upgrade `com.google.ads.mobile` via Integration Manager (Recommended Setup uses 11.0.0, which avoids most conflicts).

## Running from code (automation)

If you need to call Integration Manager logic from a build script:

```csharp
using com.noctuagames.sdk.Editor;   // internal; available in Editor assembly

// Reflection or direct call depending on SDK version — inspect NoctuaSDKMenu.cs
```

Typically, manual Integration Manager action is sufficient — CI should commit the resulting `manifest.json` changes and let subsequent builds use them.
