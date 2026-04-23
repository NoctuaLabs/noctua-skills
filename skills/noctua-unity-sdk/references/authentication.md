# `Noctua.Auth` — Authentication

Source: `Packages/com.noctuagames.sdk/Runtime/View/NoctuaAuthentication.cs`.

The SDK supports: guest login, email register/login (with verification codes), password reset, social login (Google / Facebook / Apple / etc.), account switching, account deletion, cloud save (`GameState`).

## Properties & events

```csharp
// Cached list of local accounts (useful for "Switch Account" UI)
IReadOnlyList<UserBundle> list = Noctua.Auth.AccountList;

// True once a user is signed in
bool signedIn = Noctua.Auth.IsAuthenticated;

// Most recent account (null if none)
UserBundle recent = Noctua.Auth.RecentAccount;

// Events — wire BEFORE InitAsync
Noctua.Auth.OnAccountChanged += (UserBundle u) => { /* login / logout / switch */ };
Noctua.Auth.OnAccountDeleted += (Player p)     => { /* user deleted account */ };
```

## Common flows

### Authenticate (auto or UI)
Picks an existing account or presents login UI:
```csharp
UserBundle account = await Noctua.Auth.AuthenticateAsync();
```

### Guest login
```csharp
UserBundle guest = await Noctua.Auth.LoginAsGuest();
```

### Get access token (for your own backend calls)
```csharp
string token = Noctua.Auth.GetAccessToken();
```

### Show the built-in User Center UI
```csharp
await Noctua.Auth.ShowUserCenter();
```

### Switch account
```csharp
// Show account picker UI
Noctua.Auth.SwitchAccount();

// Or switch to a specific cached account
Noctua.Auth.SwitchAccount(someUserBundle);
```

### Logout
```csharp
UserBundle nextActive = await Noctua.Auth.LogoutAsync();
```

### Clear all cached local accounts
```csharp
Noctua.Auth.ResetAccounts();
```

## Email register & login

### Register (with verification code)
```csharp
CredentialVerification pending =
    await Noctua.Auth.RegisterWithEmailAsync(
        email: "player@example.com",
        password: "secret",
        regExtra: new Dictionary<string, string> { { "nickname", "Ace" } });

// User receives email with a code
UserBundle account =
    await Noctua.Auth.VerifyEmailRegistrationAsync(pending.Id, code: "123456");
```

### Login
```csharp
UserBundle account = await Noctua.Auth.LoginWithEmailAsync("player@example.com", "secret");
```

### Link email to an existing (e.g. guest) account
```csharp
CredentialVerification pending =
    await Noctua.Auth.LinkWithEmailAsync("player@example.com", "secret");
Credential linked =
    await Noctua.Auth.VerifyEmailLinkingAsync(pending.Id, "123456");
```

### Reset password
```csharp
CredentialVerification request = await Noctua.Auth.RequestResetPasswordAsync("player@example.com");
PlayerToken token = await Noctua.Auth.ConfirmResetPasswordAsync(request.Id, "123456", "newPass");
```

## Social login

```csharp
// UI-driven (opens WebView)
UserBundle account = await Noctua.Auth.SocialLoginAsync("google");

// Manual — get redirect URL for your own WebView
string redirectUrl = await Noctua.Auth.GetSocialLoginRedirectURL("google");
// ...user completes login, redirect returns payload...
UserBundle account = await Noctua.Auth.SocialLoginAsync("google", socialLoginRequest);

// Link a social account to the current player
Credential linked = await Noctua.Auth.SocialLinkAsync("google", socialLinkRequest);
```

Provider names: `"google"`, `"facebook"`, `"apple"`, `"twitter"`, etc. (server-configured).

## Token exchange (custom auth handoff)

```csharp
UserBundle account = await Noctua.Auth.ExchangeToken(yourCustomAccessToken);
```

Used when your backend mints a Noctua-compatible token via its own login flow.

## Update player profile

```csharp
await Noctua.Auth.UpdatePlayerAccountAsync(new PlayerAccountData
{
    Nickname = "NewName",
    // avatar, bio, ...
});
```

## GameState — cloud save

Per-key blob storage (string values) tied to the current player.

```csharp
// Key must match  ^[a-zA-Z0-9_\-\.]{1,128}$
await Noctua.Auth.SaveGameState("slot.main", JsonUtility.ToJson(saveData));

string raw = await Noctua.Auth.LoadGameState("slot.main");

List<string> keys = await Noctua.Auth.GetGameStateKeys();

await Noctua.Auth.DeleteGameState("slot.main");
```

## Feature flags (set by server)

```csharp
Noctua.Auth.SetFlag(new Dictionary<string, bool>
{
    { "show_email_link", true },
    { "show_social_apple", false },
});
```
Applied to the Auth UI; typically called by `NoctuaGameService` after remote config.

## Full canonical try/catch

```csharp
try
{
    var account = await Noctua.Auth.LoginAsGuest();
    Debug.Log($"Logged in as {account.Player.Nickname}");
}
catch (NoctuaException nex)
{
    switch (nex.ErrorCode)
    {
        case NoctuaErrorCode.UserBanned:
            ShowBannedDialog(nex.Message); break;
        case NoctuaErrorCode.Authentication:
            ShowLoginError(nex.Message); break;
        default:
            Debug.LogError($"Auth {nex.ErrorCode}: {nex.Message}"); break;
    }
}
catch (Exception e)
{
    Debug.LogError($"Unexpected: {e.Message}");
}
```

## Types referenced

- `UserBundle` — `{ Player, Credential, AccessToken, ... }`
- `Player` — `{ Id, Nickname, Picture, ... }`
- `Credential` — linked credential descriptor
- `CredentialVerification` — `{ Id, Method }` returned by email registration/linking/reset
- `PlayerToken` — short-lived token returned after password reset
- `SocialLoginRequest` / `SocialLinkRequest` — provider-specific auth payloads
- `PlayerAccountData` — updatable profile fields

See `Runtime/Model/Entities/` in the SDK source for full field lists.

## Offline behavior

When `Noctua.IsOfflineMode()` is `true`:

- `AuthenticateAsync()` returns the cached `RecentAccount` if available
- `ShowUserCenter()` shows a retry dialog instead of opening the UI
- All calls that require server verification throw `NoctuaException(Authentication)`
