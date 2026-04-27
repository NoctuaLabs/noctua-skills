# Firebase, Adjust Attribution, and Push Notifications

> **Sources** — Official API: https://docs.noctua.gg/sdk/noctua-firebase · Tutorials: https://docs.noctua.gg/docs/advanced/firebase-utilities, /firebase-remote-configs, /push-notifications, /adjust-attribution, /pseudo-user-id · Repo: [Runtime/View/Noctua.Firebase.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/View/Noctua.Firebase.cs)

Static helpers on the `Noctua` class proxy to the underlying Firebase and Adjust native SDKs. All getters are async and safe to call on unsupported platforms — they fall back to empty / default values rather than throwing.

## Firebase IDs and tokens

```csharp
string fid     = await Noctua.GetFirebaseInstallationID();
string sid     = await Noctua.GetFirebaseAnalyticsSessionID();
string fcm     = await Noctua.GetFirebaseMessagingToken();
```

`GetFirebaseMessagingToken()` returns an empty string when:

- iOS APNs ↔ FCM handshake hasn't completed yet (typical on first cold start). Retry after a short delay (2–5 s).
- The user hasn't granted notification permission.
- The Firebase Messaging library isn't linked, or you're in the Editor.

```csharp
var token = await Noctua.GetFirebaseMessagingToken();
if (string.IsNullOrEmpty(token))
{
    await Task.Delay(3000);
    token = await Noctua.GetFirebaseMessagingToken();
}
```

### Sandbox auto-log

When `noctuagg.json → noctua.sandboxEnabled` is `true`, the SDK polls FCM up to 6 × 2 s after `InitAsync()` completes and logs the token to the Unity console (`[sandbox] FCM token: …`). Production builds (sandbox flag off) skip the log entirely — tokens never land in release logs.

## Firebase Remote Config

Typed getters; default values are used when the key is missing or Remote Config isn't initialized.

```csharp
string banner = await Noctua.GetFirebaseRemoteConfigString("welcome_banner_url");
bool   on     = await Noctua.GetFirebaseRemoteConfigBoolean("event_double_xp_enabled");
double mult   = await Noctua.GetFirebaseRemoteConfigDouble("loot_multiplier");
long   cap    = await Noctua.GetFirebaseRemoteConfigLong("daily_quest_cap");
```

Defaults: `""`, `false`, `0.0`, `0L`.

## Adjust attribution

```csharp
NoctuaAdjustAttribution attr = await Noctua.GetAdjustAttributionAsync();
Debug.Log($"Network={attr.Network} Campaign={attr.Campaign} Adid={attr.Adid}");
```

Fields: `TrackerToken`, `TrackerName`, `Network`, `Campaign`, `Adgroup` (note lowercase 'g'), `Creative`, `ClickLabel`, `Adid`, `CostType`, `CostAmount` (`double`), `CostCurrency`, `FbInstallReferrer`. Returns a default-initialized instance when Adjust isn't linked. Verified against `Runtime/Model/Entities/NoctuaAdjustAttribution.cs`.

## Push notification events

Three events on the `Noctua` facade let game code react to push lifecycle without writing native code. Today they fire reliably on iOS; on Android the FCM token getter and refresh event already work, but data-message foreground/background callbacks need a forthcoming native bridge.

```csharp
// Cold-start tap (user tapped the notification to launch the app):
//   the payload is held until subscribers attach, so subscribing in Awake/Start still fires.
// Foreground/background notifications: subscribe before they can arrive — once delivered, iOS does NOT re-deliver.

Noctua.OnRemoteNotificationReceived += payload =>
{
    NotificationCenter.Show(payload.Title, payload.Body);
};

Noctua.OnNotificationTapped += payload =>
{
    if (!string.IsNullOrEmpty(payload.Deeplink))
    {
        DeeplinkRouter.Navigate(payload.Deeplink);
        return;
    }
    var sceneId = payload.GetCustomString("scene_id");
    if (!string.IsNullOrEmpty(sceneId)) SceneRouter.Load(sceneId);
};

Noctua.OnFirebaseMessagingTokenRefresh += token =>
{
    BackendApi.RegisterPushToken(token);   // re-register on rotation
};
```

### `NoctuaNotificationPayload`

| Property | Type | Meaning |
|---|---|---|
| `RawJson` | `string` | Full serialized payload — inspect for fields not exposed as convenience getters. |
| `Aps` | `JObject` | Top-level `aps` dictionary on iOS, `null` on Android. |
| `Custom` | `JObject` | Every custom top-level field (anything outside `aps` / `notification`). |
| `Title` | `string` | APS `alert.title` (iOS) or notification title (Android). |
| `Body` | `string` | APS `alert.body` (iOS) or notification body (Android). |
| `Deeplink` | `string` | Auto-discovered from `deeplink` / `noctua_deeplink` / `route` / `link` / `url` — first non-empty match wins. |

Method: `string GetCustomString(string key)` — returns empty string when missing.

### Server-side payload shape (example)

```json
{
  "aps": {
    "alert": { "title": "Daily Reward", "body": "Claim your 100 gems" },
    "badge": 1,
    "sound": "default"
  },
  "deeplink": "noctuagame://rewards/daily",
  "reward_id": "gems_100",
  "campaign": "week_42"
}
```

Parsed result: `Title="Daily Reward"`, `Body="Claim your 100 gems"`, `Deeplink="noctuagame://rewards/daily"`, `GetCustomString("reward_id")="gems_100"`.

## Token rotation

FCM may rotate the token when a user reinstalls, clears app data, or restores their device. On iOS the SDK's `CustomAppController` broadcasts an `FCMToken` `NSNotification` each time the delegate receives a new token; `GetFirebaseMessagingToken()` always returns the latest value. Cache server-side per user/device and re-fetch on every cold start, plus react to `OnFirebaseMessagingTokenRefresh` for in-session rotations.

## Implementation guide — Push setup

### iOS

1. Xcode target → **Signing & Capabilities → + Capability → Push Notifications**.
2. Drop `GoogleService-Info.plist` into `Assets/StreamingAssets/` — the build post-processor copies it into the exported Xcode project.
3. No Unity Mobile Notifications package required. If your game already imports `com.unity.mobile.notifications`, the SDK auto-detects it and chains `CustomAppController → LocalNotificationAppController` so push and local notifications coexist.

### Android

1. Drop `google-services.json` into `Assets/StreamingAssets/` — the build post-processor copies it into the Android launcher module and injects the Google Services Gradle plugin.
2. On Android 13+, request the runtime `POST_NOTIFICATIONS` permission before expecting deliveries:
   ```csharp
   #if UNITY_ANDROID
   UnityEngine.Android.Permission.RequestUserPermission("android.permission.POST_NOTIFICATIONS");
   #endif
   ```

### Opt-out for games with their own `UnityAppController` (iOS)

Add `NOCTUA_DISABLE_CUSTOM_APP_CONTROLLER` to *Player Settings → iOS → Other Settings → Scripting Define Symbols*. Noctua's Objective-C bridge compiles to empty; you take responsibility for the APNs ↔ FIRMessaging hand-off (mirror `Runtime/Plugins/iOS/CustomAppController.mm` in your custom controller).

## Implementation guide — Push subscription pattern

Subscribe in `Awake` / `Start`, or immediately after `Noctua.InitAsync()`. The native side buffers the most recent cold-start tap so late subscribers still receive the launching notification:

```csharp
using com.noctuagames.sdk;
using UnityEngine;

public class PushRouter : MonoBehaviour
{
    private void Start()
    {
        Noctua.OnNotificationTapped            += HandleTap;
        Noctua.OnRemoteNotificationReceived    += HandleForeground;
        Noctua.OnFirebaseMessagingTokenRefresh += HandleTokenRotation;
    }

    private void OnDestroy()
    {
        Noctua.OnNotificationTapped            -= HandleTap;
        Noctua.OnRemoteNotificationReceived    -= HandleForeground;
        Noctua.OnFirebaseMessagingTokenRefresh -= HandleTokenRotation;
    }

    private static void HandleTap(NoctuaNotificationPayload payload)
    {
        if (!string.IsNullOrEmpty(payload.Deeplink))
        {
            DeeplinkRouter.Navigate(payload.Deeplink);
            return;
        }
        var sceneId = payload.GetCustomString("scene_id");
        if (!string.IsNullOrEmpty(sceneId)) SceneRouter.Load(sceneId);
    }

    private static void HandleForeground(NoctuaNotificationPayload payload)
        => UIBanner.Show(payload.Title, payload.Body);

    private static void HandleTokenRotation(string token)
        => BackendApi.RegisterPushToken(token);
}
```

iOS is the supported surface today (delivery callbacks fully wired). On Android the FCM token getter and refresh callback work; remote-message and tap callbacks wait on a forthcoming native `FirebaseMessagingService` subclass.

## Implementation guide — sending a test push from Firebase Console

Per https://docs.noctua.gg/docs/advanced/push-notifications:

1. Firebase Console → **Engage → Cloud Messaging → New campaign → Notifications**.
2. **Notification:** Title (`payload.Title`), Text (`payload.Body`).
3. **Target:** Single device — paste the FCM token (sandbox builds auto-log it; see below).
4. **Schedule:** Now.
5. **Additional options → Custom data:** add rows for the deeplink + arbitrary fields:

   | Key | Value | Read via |
   |---|---|---|
   | `deeplink` | `noctuagame://rewards/gems_100` | `payload.Deeplink` |
   | `reward_id` | `gems_100` | `payload.GetCustomString("reward_id")` |
   | `campaign` | `daily_reward_week_42` | `payload.GetCustomString("campaign")` |

6. **iOS extras** (for silent / background pushes): set Sound `default`, Badge `1`, Content-available `true`.
7. **Review → Publish.**

Equivalent FCM v1 REST payload (for `curl` / Postman):

```json
{
  "message": {
    "token": "<FCM-TOKEN>",
    "notification": { "title": "Daily Reward", "body": "Claim your 100 gems" },
    "data": {
      "deeplink": "noctuagame://rewards/gems_100",
      "reward_id": "gems_100"
    },
    "apns": { "payload": { "aps": { "sound": "default", "badge": 1, "content-available": 1 } } },
    "android": { "priority": "high" }
  }
}
```

## Implementation guide — sandbox FCM token auto-log

When `noctuagg.json → noctua.sandboxEnabled` is `true`, the SDK polls FCM after `InitAsync` (6 × 2 s to cover the iOS APNs handshake) and prints:

```
[Noctua] [sandbox] FCM token: fCzG0yA...<rest>
```

QA can copy the token from Xcode / logcat and paste it directly into Firebase Console's Single-Device target. Production builds skip this log entirely — tokens never land in release logs.

## Implementation guide — Adjust attribution data

Available **only on Android and iOS**; on Editor / Standalone the call returns a default-initialised struct.

```csharp
NoctuaAdjustAttribution attr = await Noctua.GetAdjustAttributionAsync();
Debug.Log($"Network={attr.Network} Campaign={attr.Campaign} Adgroup={attr.Adgroup}");
```

Full surface (per https://docs.noctua.gg/docs/advanced/adjust-attribution):

| Field | Type | Meaning |
|---|---|---|
| `TrackerToken` | `string` | Adjust tracker token |
| `TrackerName` | `string` | Adjust tracker name |
| `Network` | `string` | Ad network (e.g. "Google Ads", "Facebook") |
| `Campaign` | `string` | Campaign name |
| `Adgroup` | `string` | Ad group |
| `Creative` | `string` | Creative name |
| `ClickLabel` | `string` | Click label |
| `Adid` | `string` | Adjust device ID |
| `CostType` | `string` | "CPI", "CPC", etc. |
| `CostAmount` | `double` | Cost amount |
| `CostCurrency` | `string` | ISO-4217 |
| `FbInstallReferrer` | `string` | Facebook install referrer |

Use this for cohort segmentation, UA dashboards, and campaign-attribution analytics.

## Implementation guide — pseudo user ID

`Noctua.GetPseudoUserId()` returns a deterministic 32-char lowercase hex string derived from device identity + bundle ID. The SDK **automatically attaches it as `pseudo_user_id` to every event** sent to Noctua analytics — no manual instrumentation needed.

```csharp
string pseudoId = Noctua.GetPseudoUserId();
// "a3f92c1e4b8d07650e21a934cf1b8e5d"
```

Use it when a third-party SDK or attribution service needs a stable device-scoped ID. It survives reinstalls, is stable across sessions, and is scoped per app bundle (different apps on the same device produce different IDs).

**Not** a substitute for `Player.Id` — that identifies the authenticated player; the pseudo ID identifies the device install. Call only after `InitAsync` completes.

## Implementation guide — payload deeplink discovery

`payload.Deeplink` auto-resolves the first non-empty value from `deeplink`, `noctua_deeplink`, `route`, `link`, or `url` — server-side teams can pick whichever field name fits their backend without changing client code. Read arbitrary other fields via `payload.GetCustomString("your_key")` (returns empty string if missing).

## Verification checklist (push)

| State | Expected behaviour |
|---|---|
| App foreground | `OnRemoteNotificationReceived` fires immediately |
| App background / killed | OS shows banner; tapping launches and fires `OnNotificationTapped` |
| Cold-start tap | Late subscribers still receive the buffered tap once registration runs |
| FCM token rotation | Reinstall or clear data → `OnFirebaseMessagingTokenRefresh` fires with new value |
| ATT denied | Notifications still deliver (ATT controls attribution, not push) |
