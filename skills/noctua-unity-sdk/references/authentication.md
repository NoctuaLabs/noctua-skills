# `Noctua.Auth` — Authentication

> **Sources** — Official API: https://docs.noctua.gg/sdk/auth · Tutorials: https://docs.noctua.gg/docs/unity/authentication/overview, /integrate-noctua-account, /integrate-authentication-features, /cloud-game-state, /updating-player-account · Repo: [Runtime/View/NoctuaAuthentication.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/View/NoctuaAuthentication.cs)

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
    switch ((NoctuaErrorCode)nex.ErrorCode)
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
- `Player` — `{ Id, UserId, GameId, AccessToken, Nickname, AvatarUrl }`
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

## Implementation guide — first-launch flow

The canonical first-launch sequence (per https://docs.noctua.gg/docs/unity/authentication/integrate-noctua-account):

```csharp
using com.noctuagames.sdk;
using Cysharp.Threading.Tasks;
using System;
using System.Collections.Generic;
using UnityEngine;

public class AuthenticationManager : MonoBehaviour
{
    private void Awake() => StartCoroutine(Authenticate().ToCoroutine());

    private async UniTask Authenticate()
    {
        try
        {
            var bundle = await Noctua.Auth.AuthenticateAsync();
            // Player.Id is GUARANTEED unique per user per game — use it for analytics keys.
            var playerId = bundle.Player.Id;
            Debug.Log($"PlayerId: {playerId}");
        }
        catch (Exception e) when (e is NoctuaException nex)
        {
            // Banned-user code is 2202 — block access to gameplay.
            if (nex.ErrorCode == 2202) return;
            Debug.LogError($"Auth {nex.ErrorCode}: {nex.Message}");
            return;
        }

        // Update RoleId / ServerId once the in-game UID is generated.
        await Noctua.Auth.UpdatePlayerAccountAsync(new PlayerAccountData
        {
            IngameUsername = "CoolGamer123",
            IngameServerId = "Server001",
            IngameRoleId   = "Role789",
            Extra = new Dictionary<string, string>
            {
                { "level", "42" },
                { "xp", "9876" }
            }
        });
    }
}
```

`AuthenticateAsync` handles guest auto-create and returning-player auto-login transparently — game code does not branch on user type. A welcome toast is shown by the SDK on first authentication.

### Banned users — error code 2202

```csharp
try { await Noctua.Auth.AuthenticateAsync(); }
catch (NoctuaException nex) when (nex.ErrorCode == 2202)
{
    // SDK already showed the banned dialog and the exception fires after the user
    // dismisses it. Prevent the player from entering gameplay — do NOT load the
    // home scene, do NOT call gameplay APIs.
    return;
}
```

### `UpdatePlayerAccountAsync` — when to call

Call after each of these transitions (per https://docs.noctua.gg/docs/unity/authentication/updating-player-account):

1. **First entry to the game** — after `AuthenticateAsync` and once the in-game `RoleId` is generated.
2. **Login / logout** — every account change.
3. **Server hops** — player switches in-game shard / region.
4. **Profile updates** — nickname change.
5. **Before any IAP** — ensures the purchase is associated with the current role.

The `Extra` dictionary is for identification metadata only (level, VIP tier). Do **not** push transient game state into it — that is the role of cloud `GameState`.

## Implementation guide — Switch Account & User Center

```csharp
// Switch Account button — opens the SDK's account picker UI
public void OnSwitchAccountTapped() => Noctua.Auth.SwitchAccount();

// User Center button — full account management UI (profile, link providers, delete)
public async void OnUserCenterTapped()
{
    try { await Noctua.Auth.ShowUserCenter(); }
    catch (NoctuaException nex) { Debug.LogError($"UserCenter {nex.ErrorCode}: {nex.Message}"); }
}
```

Both APIs throw `NoctuaException(Application)` if the SDK is offline or `Auth` URLs are missing in `noctuagg.json`.

## Implementation guide — Account change & deletion events

Wire these BEFORE `Noctua.InitAsync()`:

```csharp
Noctua.Auth.OnAccountChanged += bundle =>
{
    // Fires on login, logout, AND switch-account. bundle is null on logout.
    Debug.Log(bundle == null
        ? "Logged out"
        : $"Now active: Player {bundle.Player.Id}");
    RefreshHudForPlayer(bundle?.Player);
};

Noctua.Auth.OnAccountDeleted += player =>
{
    // User-initiated deletion — clear LOCAL save, surface a "goodbye" screen,
    // then call AuthenticateAsync() again to provision a fresh guest if needed.
    Debug.Log($"Deleted player: {player.Id}");
    LocalSave.Wipe();
};
```

## Implementation guide — Cloud `GameState`

Use cloud save for cross-device progress that should follow the player's Noctua account (per https://docs.noctua.gg/docs/unity/authentication/cloud-game-state):

```csharp
[Serializable]
public class PlayerProgress
{
    public int level;
    public int score;
    public string lastCheckpoint;
}

public async UniTask SaveProgress(PlayerProgress p)
{
    string json = JsonUtility.ToJson(p);
    await Noctua.Auth.SaveGameState("player_progress", json);
}

public async UniTask<PlayerProgress> LoadProgress()
{
    string json = await Noctua.Auth.LoadGameState("player_progress");
    if (string.IsNullOrEmpty(json)) return null;
    return JsonUtility.FromJson<PlayerProgress>(json);
}
```

- Keys: `^[a-zA-Z0-9_\-\.]{1,128}$` — letters, numbers, underscore, hyphen, dot. Examples: `progress_slot_1`, `settings.audio`, `inventory-data`.
- Values are arbitrary strings — JSON-serialise complex structures yourself.
- Auth is required; calls throw `NoctuaException(Authentication)` if the player isn't signed in.
- Storage is per **player per game** — no cross-game data sharing.

## Implementation guide — Server-side access-token validation

If your backend accepts player-authenticated requests, validate the token cryptographically rather than re-querying Noctua:

1. Client passes `bundle.Player.AccessToken` (a JWT signed by Noctua) to your backend.
2. Backend fetches JWKS from `https://sdk-api-v2.noctuaprojects.com/api/v1/auth/jwks` (cache it — ES256 keys rotate rarely).
3. Verify the JWT signature with the matching `kid`. The decoded payload identifies the user.

See https://docs.noctua.gg/docs/unity/authentication/integrate-noctua-account#validation-process for full PHP / Node.js examples (jose, jwks-rsa).

Same JWKS verifies IAP / reward webhook `signed_data` payloads — see [iap.md](iap.md#server-delivery-webhook).
