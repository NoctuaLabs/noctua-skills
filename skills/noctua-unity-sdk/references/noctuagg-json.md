# `noctuagg.json` — SDK Configuration File

> **Sources** — Official: https://docs.noctua.gg/docs/installation (configuration section) · Repo schema: [Runtime/Model/DTOs/](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/tree/main/Runtime/Model/DTOs) (`GlobalConfig.cs`, `NoctuaConfig.cs`, `AdjustConfig.cs`, `FirebaseConfig.cs`, `FacebookConfig.cs`, `GameServiceModels.cs`)

**Required location:** `Assets/StreamingAssets/noctuagg.json`

Without this file `Noctua.InitAsync()` throws `NoctuaException(NoctuaErrorCode.Application, ...)`. The SDK loads it at init via `UnityWebRequest` on Android (to handle `jar:file://` StreamingAssets) and `File.ReadAllText` on iOS / editor, with a 5-second timeout.

Source of truth for this schema: `Packages/com.noctuagames.sdk/Runtime/Model/DTOs/` — `GlobalConfig.cs`, `NoctuaConfig.cs`, `AdjustConfig.cs`, `FirebaseConfig.cs`, `FacebookConfig.cs`, `GameServiceModels.cs`.

## Top-level schema

| Key | Type | Required | Purpose |
|---|---|---|---|
| `clientId` | string | **yes** | OAuth client ID from the Noctua console |
| `gameId` | long | yes | Server-side game ID (default `0`) |
| `noctua` | object | auto-created if missing | Core SDK config (see below) |
| `adjust` | object | if using Adjust | Adjust attribution config |
| `firebase` | object | if using Firebase | Firebase per-platform config |
| `facebook` | object | if using Meta | Facebook App Events config |
| `iaa` | object | if `noctua.iaaEnabled: true` | Ad mediation config |
| `copublisher` | object | optional | Co-publisher branding (all 4 string fields are `[JsonRequired]` when the block is present) |

## `noctua` (core SDK config)

From `NoctuaConfig.cs`:

| Key | Type | Default | Purpose |
|---|---|---|---|
| `sandboxEnabled` | bool | `false` | Switch to sandbox API + enables Noctua Inspector overlay |
| `offlineFirstEnabled` | bool | `false` | Allow `InitAsync` to succeed without network |
| `iaaEnabled` | bool | `false` | Enable in-app advertising |
| `iapDisabled` | bool | `false` | Disable in-app purchases entirely |
| `welcomeToastDisabled` | bool | `false` | Suppress the post-login toast |
| `trackerUrl` | string | `https://sdk-tracker.noctuaprojects.com/api/v1` | Event ingestion API |
| `baseUrl` | string | `https://sdk-api-v2.noctuaprojects.com/api/v1` | Core SDK API. **Auto-swapped** to `https://sandbox-sdk-api-v2.noctuaprojects.com/api/v1` (the `DefaultSandboxBaseUrl` constant in `NoctuaConfig.cs`) when `sandboxEnabled: true` and `baseUrl` is left at the default. |
| `announcementBaseUrl` | string | (platform default) | Announcements API |
| `rewardBaseUrl` | string | (platform default) | Rewards API |
| `socialMediaBaseUrl` | string | (platform default) | Social media API |
| `customerServiceBaseUrl` | string | (platform default) | Customer service API |
| `sentryDsnUrl` | string | `""` | Glitchtip / Sentry crash reporting DSN |
| `trackerBatchSize` | uint | `20` | Max events per HTTP flush |
| `trackerBatchPeriodMs` | uint | `60000` | Flush interval (ms) |
| `sessionHeartbeatPeriodMs` | uint | `60000` | `session_heartbeat` cadence |
| `sessionTimeoutMs` | uint | `900000` | Session idle timeout (15 min) |
| `region` | string | (device) | ISO region override ("VN", "ID") |
| `remoteFeatureFlags` | object | `{}` | Local feature-flag defaults (overridable by server) |

## `adjust`

From `AdjustConfig.cs` — `android` and `ios` are both required if the `adjust` object is present:

```json
"adjust": {
  "android": {
    "appToken": "xxxxxxxxxxxx",
    "environment": "sandbox",
    "eventMap": { "login": "1qhqus", "purchase": "qye2vk" }
  },
  "ios": {
    "appToken": "xxxxxxxxxxxx",
    "environment": "production",
    "eventMap": { "login": "1qhqus", "purchase": "qye2vk" }
  }
}
```

- `appToken` (required) — Adjust app token
- `environment` — `"sandbox"` or `"production"` (default `"sandbox"`)
- `eventMap` — map of Noctua event name → Adjust event token; events not listed are not forwarded to Adjust

## `firebase`

From `FirebaseConfig.cs`:

```json
"firebase": {
  "android": { "customEventDisabled": false },
  "ios":     { "customEventDisabled": false }
}
```

- `customEventDisabled` (required) — if `true`, `TrackCustomEvent(...)` calls are not forwarded to Firebase Analytics (session / purchase / ad revenue still forward)

Also drop `GoogleService-Info.plist` (iOS) and `google-services.json` (Android) into `Assets/StreamingAssets/`. The build post-processor copies them into the Xcode / Gradle project automatically; remove them to disable Firebase.

## `facebook`

From `FacebookConfig.cs`:

```json
"facebook": {
  "android": {
    "appId": "1234567890",
    "clientToken": "xxxxxxxxxxxxxxxx"
  },
  "ios": {
    "appId": "...",
    "clientToken": "..."
  }
}
```

`appId` and `clientToken` are both `[JsonRequired]` when the `facebook` block is present (`FacebookAndroidConfig` / `FacebookIosConfig`). No other fields are deserialized — `displayName`, `enableDebug`, and `customEventDisabled` are not in the DTO and will be silently ignored if you add them. The Android `BuildPostProcessor` auto-injects the Facebook `appId` as `<meta-data>` in `AndroidManifest.xml`.

## `iaa` (in-app ads)

Required only if `noctua.iaaEnabled: true`. See [iaa-ads.md](iaa-ads.md) for the full shape.

Top-level keys (from `GameServiceModels.cs` → class `IAA`):

| Key | Purpose |
|---|---|
| `mediation` | primary network (`"admob"` or `"applovin"`) |
| `secondary_mediation` | fallback network |
| `networks` | per-network ad unit IDs keyed by format and platform |
| `ad_format_overrides` | pin specific formats to a specific network (e.g. `{"banner":"admob"}`) |
| `frequency_caps` | per-format max impressions / window |
| `cooldown_seconds` | per-format cooldown |
| `enabled_formats` | bool flags per format |
| `dynamic_optimization` | bool — enable performance routing |
| `app_open_auto_show` | bool — auto-show app-open on foreground |
| `taichi` | `{ revenue_threshold, ad_count_threshold, ... }` — Taichi pipeline thresholds |
| `cpm_floors` | bidding floor config with `enabled`, `min_samples`, `floors`, `segment_overrides` |
| `ad_experiments` | A/B experiment variants |

## Full template (verbatim from sample app)

Save as `Assets/StreamingAssets/noctuagg.json` and replace the tokens:

```json
{
  "clientId": "REPLACE-WITH-YOUR-CLIENT-ID",
  "gameId": 1,
  "copublisher": {
    "companyName": "",
    "companyWebsiteUrl": "",
    "companyTermUrl": "",
    "companyPrivacyUrl": ""
  },
  "noctua": {
    "sentryDsnUrl": "",
    "sandboxEnabled": true,
    "offlineFirstEnabled": true,
    "welcomeToastDisabled": false,
    "iaaEnabled": true,
    "iapDisabled": false,
    "remoteFeatureFlags": {}
  },
  "adjust": {
    "android": {
      "environment": "sandbox",
      "appToken": "REPLACE",
      "eventMap": {
        "login": "xxxxxx",
        "purchase": "xxxxxx"
      }
    },
    "ios": {
      "environment": "sandbox",
      "appToken": "REPLACE",
      "eventMap": {
        "login": "xxxxxx",
        "purchase": "xxxxxx"
      }
    }
  },
  "firebase": {
    "android": { "customEventDisabled": false },
    "ios":     { "customEventDisabled": false }
  },
  "facebook": {
    "android": { "appId": "REPLACE", "clientToken": "REPLACE" },
    "ios":     { "appId": "REPLACE", "clientToken": "REPLACE" }
  },
  "iaa": {
    "mediation": "admob",
    "secondary_mediation": "applovin",
    "ad_format_overrides": {
      "app_open":     "admob",
      "banner":       "admob",
      "interstitial": "admob",
      "rewarded":     "admob"
    },
    "app_open_auto_show": false,
    "dynamic_optimization": false,
    "enabled_formats": {
      "interstitial": true,
      "rewarded": true,
      "rewarded_interstitial": false,
      "banner": true,
      "app_open": true
    },
    "frequency_caps": {
      "interstitial": { "max_impressions": 10, "window_seconds": 3600 },
      "app_open":     { "max_impressions": 3,  "window_seconds": 3600 }
    },
    "cooldown_seconds": {
      "interstitial": 15,
      "app_open":     30
    },
    "networks": {
      "admob": {
        "ad_formats": {
          "banner":       { "android": { "ad_unit_id": "ca-app-pub-.../..." }, "ios": { "ad_unit_id": "ca-app-pub-.../..." } },
          "interstitial": { "android": { "ad_unit_id": "ca-app-pub-.../..." }, "ios": { "ad_unit_id": "ca-app-pub-.../..." } },
          "rewarded":     { "android": { "ad_unit_id": "ca-app-pub-.../..." }, "ios": { "ad_unit_id": "ca-app-pub-.../..." } },
          "app_open":     { "android": { "ad_unit_id": "ca-app-pub-.../..." }, "ios": { "ad_unit_id": "ca-app-pub-.../..." } }
        }
      },
      "applovin": {
        "ad_formats": {
          "banner":       { "android": { "ad_unit_id": "xxxxx" }, "ios": { "ad_unit_id": "xxxxx" } },
          "interstitial": { "android": { "ad_unit_id": "xxxxx" }, "ios": { "ad_unit_id": "xxxxx" } },
          "rewarded":     { "android": { "ad_unit_id": "xxxxx" }, "ios": { "ad_unit_id": "xxxxx" } },
          "app_open":     { "android": { "ad_unit_id": "xxxxx" }, "ios": { "ad_unit_id": "xxxxx" } }
        }
      }
    }
  }
}
```

## Sandbox vs production

| Scenario | `noctua.sandboxEnabled` | `adjust.*.environment` | Ad unit IDs |
|---|---|---|---|
| Dev build | `true` | `"sandbox"` | Test IDs (AdMob `ca-app-pub-3940256099942544/*`) |
| Production | `false` | `"production"` | Real IDs from AdMob / AppLovin console |

## Server merge

At init the SDK fetches remote IAA config and merges it field-by-field with the local `iaa` block (see `IAA.MergeWith` in `GameServiceModels.cs`). Frequency caps, cooldowns, experiments, and CPM floors can all be overridden server-side without a game update.
