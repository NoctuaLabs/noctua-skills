# `Noctua.Platform` — Locale & Web Content

> **Sources** — Official APIs: https://docs.noctua.gg/sdk/platform-content, https://docs.noctua.gg/sdk/platform-locale · Tutorials: https://docs.noctua.gg/docs/unity/platform/overview, /content-announcement, /content-customer-service, /content-reward, /content-social-media, /locale · Repo: [Runtime/View/NoctuaPlatform.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/View/NoctuaPlatform.cs), [Runtime/View/NoctuaWebContent.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/View/NoctuaWebContent.cs), [Runtime/View/NoctuaLocale.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/View/NoctuaLocale.cs)

Source: `Runtime/View/NoctuaPlatform.cs` → exposes two sub-facades:
- `Noctua.Platform.Locale` → `NoctuaLocale` (`Runtime/View/NoctuaLocale.cs`)
- `Noctua.Platform.Content` → `NoctuaWebContent` (`Runtime/View/NoctuaWebContent.cs`)

## Locale — `Noctua.Platform.Locale`

Resolves player language / country / currency from `noctuagg.json → noctua.region` (explicit override) or device locale.

```csharp
string lang     = Noctua.Platform.Locale.GetLanguage();    // "en", "id", "vi"
string country  = Noctua.Platform.Locale.GetCountry();     // "ID", "VN", "US"
string currency = Noctua.Platform.Locale.GetCurrency();    // "USD", "IDR", "VND"
```

### Runtime overrides

```csharp
Noctua.Platform.Locale.SetCountry("VN");
Noctua.Platform.Locale.SetCurrency("VND");
Noctua.Platform.Locale.SetUserPrefsLanguage("vi");   // persists across sessions
```

### Translations

SDK ships built-in UI strings (login, IAP dialog, etc.) — access them for your own UI alignment:

```csharp
string text = Noctua.Platform.Locale.GetTranslation("login_title");

// Or by enum (type-safe) — see api-reference.md → Locale for the full LocaleTextKey list
string text2 = Noctua.Platform.Locale.GetTranslation(LocaleTextKey.OfflineModeMessage);

// Pull the full dictionary for the active language (e.g. to mirror it into your own UI table)
Dictionary<string,string> all = Noctua.Platform.Locale.GetTranslations();
```

### Reacting to language changes

```csharp
Noctua.Platform.Locale.OnLanguageChanged += newLang =>
{
    Debug.Log($"UI language changed to {newLang}");
    RefreshAllLocalizedText();
};

Noctua.Platform.Locale.SetUserPrefsLanguage("vi"); // raises OnLanguageChanged if it actually changed
```

## Web Content — `Noctua.Platform.Content`

Opens embedded WebViews for announcements, rewards, customer service, social media. Content URLs are configured via `noctuagg.json → noctua.*BaseUrl`.

### Announcement
```csharp
bool shown = await Noctua.Platform.Content.ShowAnnouncement();
if (!shown) Debug.Log("Announcement skipped (24-h cooldown or no content)");
```

### Customer service
```csharp
// Both params have defaults: reason = "general", context = ""
await Noctua.Platform.Content.ShowCustomerService();
await Noctua.Platform.Content.ShowCustomerService(reason: "iap_failed", context: "{\"orderId\":42}");
```

### Reward / Redemption center
```csharp
await Noctua.Platform.Content.ShowReward();
```

### Social media hub
```csharp
bool shown = await Noctua.Platform.Content.ShowSocialMedia();
if (!shown) Debug.Log("No social media page configured for this game/region");
```

All four:
- Require `Noctua.Auth.IsAuthenticated == true` (most endpoints need an access token)
- Open an internal WebView — no scene transition
- Emit analytics events (`announcement_open`, etc.)
- Throw `NoctuaException(Application)` if the corresponding `*BaseUrl` is missing in `noctuagg.json`

## Canonical try/catch

```csharp
try
{
    await Noctua.Platform.Content.ShowAnnouncement();
}
catch (NoctuaException nex)
{
    Debug.LogError($"Announcement {nex.ErrorCode}: {nex.Message}");
}
```

## Observing ShowAnnouncement exceptions

In the sample app, `ShowAnnouncement` wraps its own event handlers — wire your own observer if you need to react to WebView lifecycle:

```csharp
// HomeScreen.cs pattern: observe lifecycle & log any exception
Noctua.Platform.Content.ShowAnnouncement().AsTask().ContinueWith(t =>
{
    if (t.IsFaulted) Debug.LogError(t.Exception?.InnerException);
});
```

(See `Assets/HomeScreen.cs` for the full sample pattern.)

## Announcement / Reward base URLs

If your game uses a custom deployment, override per-endpoint URLs in `noctuagg.json`:

```json
"noctua": {
  "announcementBaseUrl":    "https://...",
  "rewardBaseUrl":          "https://...",
  "customerServiceBaseUrl": "https://...",
  "socialMediaBaseUrl":     "https://..."
}
```

When omitted, the SDK uses region-appropriate defaults.

## Implementation guide — Announcement at app entry

Show an announcement on the home / launcher screen. The "Don't show again today" checkbox suppresses re-display until the next calendar day:

```csharp
public class HomeScreen : MonoBehaviour
{
    private async void Start()
    {
        try
        {
            await Noctua.Platform.Content.ShowAnnouncement();
        }
        catch (NoctuaException nex)
        {
            Debug.LogError($"Announcement {nex.ErrorCode}: {nex.Message}");
        }
    }
}
```

## Implementation guide — Customer Service trigger

The customer service flow is bundled into the User Center, but you can expose it as a standalone button (e.g. on a settings screen or in a pause menu):

```csharp
public async void OnSupportTapped()
{
    try { await Noctua.Platform.Content.ShowCustomerService(); }
    catch (NoctuaException nex) { Debug.LogError($"CS {nex.ErrorCode}: {nex.Message}"); }
}
```

Pass `reason` / `context` when the support flow needs game-side state:
```csharp
await Noctua.Platform.Content.ShowCustomerService(
    reason: "iap_failed",
    context: $"{{\"orderId\":{orderId}}}");
```

## Implementation guide — Rewards & Social Media buttons

Mirror the announcement / CS pattern. Best UX is a dedicated button on the home / launcher:

```csharp
public async void OnRewardTapped()      => await Noctua.Platform.Content.ShowReward();
public async void OnSocialTapped()
{
    bool shown = await Noctua.Platform.Content.ShowSocialMedia();
    if (!shown) Debug.Log("No social media page configured for this region");
}
```

`ShowAnnouncement` and `ShowSocialMedia` return `bool` — `false` means the WebView did not open (cooldown active for announcement; missing `socialMediaBaseUrl` for social). `ShowCustomerService` and `ShowReward` always return `UniTask` (no skip indicator).

## Implementation guide — Locale change synchronisation

If your game has its own language picker, sync changes to the SDK so SDK UI (User Center, IAP dialogs, locale-text) follows:

```csharp
// User changes language in the game's settings menu
public void OnLanguageDropdownChanged(string newLang)
{
    Noctua.Platform.Locale.SetUserPrefsLanguage(newLang);
    // OnLanguageChanged event fires automatically if the value actually changed
}

// Conversely, listen for SDK-side language changes (User Center settings)
private void Awake()
{
    Noctua.Platform.Locale.OnLanguageChanged += newLang =>
    {
        Debug.Log($"SDK language changed to {newLang}");
        RefreshAllLocalizedText();
    };
}
```

`SetUserPrefsLanguage` persists across sessions (PlayerPrefs key `NoctuaLocaleUserPrefsLanguage` — see [installation.md](installation.md#playerprefs-keys-reserved-by-the-sdk)).

## Implementation guide — Receiving in-game rewards via webhook

Noctua's reward system delivers items via **server-to-server webhook** — the game client never receives reward grants directly. Implement an endpoint registered in the Noctua Developer Dashboard that accepts:

**Headers:** `X-CALLBACK-TOKEN: <your_secret_token>` — compare with the dashboard secret, reject 403 on mismatch.

**Body:**
```json
{
  "data": {
    "reward_id":        12345678,
    "player_id":        485934,
    "ingame_role_id":   "gmu8950",
    "ingame_server_id": "srv8976",
    "reward_time":      "2024-01-01T12:00:00Z",
    "title":            "Birthday Reward",
    "body":             "This is our gift to you.",
    "type":             "ingame_item",
    "items": [
      {
        "id":         "ingame_reward_id_123",
        "product_id": "foobar.pack1",
        "image_url":  "https://...",
        "quantity":   1
      }
    ]
  },
  "signed_data": "eyJhbGciOiJFUzI1NiIs..."
}
```

`signed_data` is a JWS signed with the same JWKS as the user access token (`https://sdk-api-v2.noctuaprojects.com/api/v1/auth/jwks`, ES256). Cache the JWKS and verify `signed_data` rather than reading `data` directly. Idempotency is mandatory — Noctua retries failed callbacks. Sample PHP / Node.js verifiers are at https://docs.noctua.gg/docs/unity/platform/receiving-in-game-rewards.

After verification your game server pushes the reward to the player's inventory; how the client surfaces it (toast, login bonus, mailbox) is out of scope for the SDK.

## Implementation guide — Providing in-game rewards (publisher API)

Reward providers (publishers / external sites) push rewards to a player by calling Noctua REST endpoints. **Do not call these from the game client** — they require a publisher-issued `X-API-KEY`.

```
GET  https://sdk-api-v2.noctuaprojects.com/api/v1/players/{game-id}/{user-id}
POST https://sdk-api-v2.noctuaprojects.com/api/v1/rewards
```

Headers: `X-API-KEY: <your-API-KEY>`. Use the player listing endpoint to discover `{ player_id, ingame_server_id, ingame_role_id, ingame_username }` for a game/user pair, then POST to `/rewards` with `{ reference_id, game_id, user_id, player_id, role_id, server_id, title, body, type, items }`. Full schema at https://docs.noctua.gg/docs/unity/platform/providing-in-game-rewards.
