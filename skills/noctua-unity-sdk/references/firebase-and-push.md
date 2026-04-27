# Firebase, Adjust Attribution, and Push Notifications

> **Sources** — Official API: https://docs.noctua.gg/sdk/noctua-firebase · Tutorials: https://docs.noctua.gg/docs/advanced/firebase-utilities, /firebase-remote-configs, /push-notifications, /adjust-attribution · Repo: [Runtime/View/Noctua.Firebase.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/View/Noctua.Firebase.cs)

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

Fields: `TrackerToken`, `TrackerName`, `Network`, `Campaign`, `AdGroup`, `Creative`, `ClickLabel`, `Adid`. Returns a default-initialized instance when Adjust isn't linked.

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
