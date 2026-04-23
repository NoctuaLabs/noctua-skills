# `Noctua.Platform` — Locale & Web Content

Source: `Packages/com.noctuagames.sdk/Runtime/View/NoctuaPlatform.cs` → exposes two sub-facades:
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

// Or by enum (type-safe)
string text2 = Noctua.Platform.Locale.GetTranslation(LocaleTextKey.LoginTitle);
```

## Web Content — `Noctua.Platform.Content`

Opens embedded WebViews for announcements, rewards, customer service, social media. Content URLs are configured via `noctuagg.json → noctua.*BaseUrl`.

### Announcement
```csharp
await Noctua.Platform.Content.ShowAnnouncement();
```

### Customer service
```csharp
await Noctua.Platform.Content.ShowCustomerService();
```

### Reward / Redemption center
```csharp
await Noctua.Platform.Content.ShowReward();
```

### Social media hub
```csharp
await Noctua.Platform.Content.ShowSocialMedia();
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
