# Full Public API Index

> **Sources** — Official API root: https://docs.noctua.gg/sdk · Per-module pages: /noctua, /auth, /iap, /event, /iaa, /iaa-event-tracking, /app, /platform, /platform-content, /platform-locale, /noctua-firebase, /types · Repo: [Runtime/View/](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/tree/main/Runtime/View) for facades, [Runtime/Presenter/](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/tree/main/Runtime/Presenter) for services, [Runtime/Model/](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/tree/main/Runtime/Model) for DTOs · CHANGELOG: [CHANGELOG.md](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/CHANGELOG.md)

Every public member on `Noctua.*`. Use this as a single-page lookup; follow the linked reference file for detailed usage.

## `Noctua` (static)

From `Runtime/View/Noctua.cs`.

### Facades
- `Noctua.Event` → `NoctuaEventService` — [events.md](events.md)
- `Noctua.Auth` → `NoctuaAuthentication` — [authentication.md](authentication.md)
- `Noctua.IAP` → `NoctuaIAPService` — [iap.md](iap.md)
- `Noctua.Platform` → `NoctuaPlatform` — [platform-features.md](platform-features.md)
- `Noctua.IAA` → `MediationManager` — [iaa-ads.md](iaa-ads.md)
- `Noctua.App` → `NoctuaAppManager` — [app-manager.md](app-manager.md)
- `Noctua.Config` → `GlobalConfig` (loaded from `noctuagg.json`)

### Sandbox-only
- `Noctua.HttpLog` → `HttpInspectorLog` (null in production)
- `Noctua.DebugMonitor` → `TrackerDebugMonitor` (null in production)
- `Noctua.Inspector` → `NoctuaInspectorController` (null in production)
- `Noctua.ShowInspector()` / `HideInspector()` / `ToggleInspector()`
- `Noctua.IsSandbox() : bool`

### Init state
- `Noctua.InitAsync(Func<UniTask>? onSuccess = null) : UniTask` — optional callback runs after the init pipeline completes.
- `Noctua.OnInitSuccess : Action?` — public **field** (not an `event`); subscribe with `+=`, but expect plain delegate semantics.
- `Noctua.IsInitialized() : bool`
- `Noctua.IsOfflineMode() : bool`
- `Noctua.IsOfflineFirst() : bool`
- `Noctua.IsOfflineAsync() : UniTask<bool>`
- `Noctua.OnOnline()` / `Noctua.OnOffline()`
- `Noctua.AdjustOfflineModeDisabled() : bool`

### Event storage (low-level)
- `Noctua.SaveEvents(string json)`
- `Noctua.GetEventsAsync() : Task<List<string>>` — bulk dump as raw JSON strings.
- `Noctua.DeleteEvents()`
- `Noctua.InsertEvent(string eventJson)`
- `Noctua.GetEventsBatchAsync(int limit, int offset) : Task<List<NativeEvent>>` — typed per-row reader (fields: `Id`, `EventJson`, `Timestamp`).
- `Noctua.DeleteEventsByIdsAsync(long[] ids) : Task<int>`
- `Noctua.GetEventCountAsync() : Task<int>`

### PlayerPrefs backup
- `Noctua.BackupPlayerPrefs() : KeyValuePair<string,string>[]` — exports Noctua-owned PlayerPrefs entries with `:int` / `:string` type suffixes.
- `Noctua.RestorePlayerPrefs(KeyValuePair<string,string>[] keyValues)` — inverse of `BackupPlayerPrefs`.
- `Noctua.GetPlayerPrefsKeys() : string[]` — list the Noctua-owned keys without exporting values.

### Crash & error forwarding (sandbox + production)
- `Noctua.DebugInjectFakeNativeCrash()` — testing hook for the native crash forwarder; emits a `client_error` with `source=native` on the next launch. See [error-handling.md](error-handling.md#native-crash-forwarding).

### Experiments / tags
- `Noctua.SetGeneralExperiment(string key, string value)`
- `Noctua.GetGeneralExperiment(string key) : string`
- `Noctua.SetExperiment(string name)`
- `Noctua.GetActiveExperiment() : string`

### Misc
- `Noctua.GetPseudoUserId() : string`
- `Noctua.ShowDatePicker(int year, int month, int day, int id)`
- `Noctua.CloseDatePicker()`
- `Noctua.OpenDatePicker(int year, int month, int day, int pickerId=1, Action<DateTime> onChange=null, Action<DateTime> onClose=null)`

## `Noctua.Auth` — `NoctuaAuthentication`

From `Runtime/View/NoctuaAuthentication.cs`.

### State (properties)
- `AccountList : IReadOnlyList<UserBundle>` — locally cached accounts (`auth.md` §Properties).
- `IsAuthenticated : bool` — true when a session is active.
- `RecentAccount : UserBundle` — the most recently used account.
- `SsoCloseWebViewKeywords : List<string>` — URL substrings that signal the SSO WebView should close after the OAuth redirect.

### Events
- `OnAccountChanged : event Action<UserBundle>` — login / logout / switch.
- `OnAccountDeleted : event Action<Player>` — user-initiated account deletion.

### Core
- `GetRecentAccount() : UserBundle`
- `GetAccessToken() : string`
- `AuthenticateAsync() : UniTask<UserBundle>`
- `LoginAsGuest() : UniTask<UserBundle>`
- `LogoutAsync() : UniTask<UserBundle>`
- `ResetAccounts()`
- `SwitchAccount()` / `SwitchAccount(UserBundle)`
- `ShowUserCenter() : UniTask`
- `ExchangeToken(string accessToken) : UniTask<UserBundle>`

### Email
- `RegisterWithEmailAsync(string email, string password, Dictionary<string,string> regExtra=null) : UniTask<CredentialVerification>`
- `VerifyEmailRegistrationAsync(int id, string code) : UniTask<UserBundle>`
- `LinkWithEmailAsync(string email, string password) : UniTask<CredentialVerification>`
- `VerifyEmailLinkingAsync(int id, string code) : UniTask<Credential>`
- `LoginWithEmailAsync(string email, string password) : UniTask<UserBundle>`
- `RequestResetPasswordAsync(string email) : UniTask<CredentialVerification>`
- `ConfirmResetPasswordAsync(int id, string code, string newPassword) : UniTask<PlayerToken>`

### Social
- `GetSocialLoginRedirectURL(string provider) : UniTask<string>`
- `SocialLoginAsync(string provider) : UniTask<UserBundle>`
- `SocialLoginAsync(string provider, SocialLoginRequest payload) : UniTask<UserBundle>`
- `SocialLinkAsync(string provider, SocialLinkRequest payload) : UniTask<Credential>`

### Profile
- `UpdatePlayerAccountAsync(PlayerAccountData data) : UniTask`

### GameState (cloud save)
- `SaveGameState(string key, string value) : UniTask`
- `LoadGameState(string key) : UniTask<string>`
- `GetGameStateKeys() : UniTask<List<string>>`
- `DeleteGameState(string key) : UniTask`

### Feature flags
- `SetFlag(Dictionary<string, bool> flags)`

## `Noctua.IAP` — `NoctuaIAPService`

From `Runtime/Presenter/NoctuaIAPService.cs`.

### Events
- `OnPurchaseDone : Action<OrderRequest>`
- `OnPurchasePending : Action<OrderRequest>`

### State
- `IsReady : bool`

### Setup
- `SetEnabledPaymentTypes(List<PaymentType>)`
- `SetDistributionPlatform(string platform)`

> `Noctua.IAP.Init()` is `internal` (`NoctuaIAPService.cs:122`) — do not call it. The facade is initialized for you by `Noctua.InitAsync()`.

### Products & purchase
- `GetProductListAsync(string currency=null, string platformType=null) : UniTask<ProductList>`
- `PurchaseItemAsync(PurchaseRequest, bool tryToUseSecondaryPayment=false, PaymentType enforcedPaymentType=PaymentType.unknown) : UniTask<PurchaseResponse>`
- `GetActiveCurrencyAsync(string productId) : UniTask<string>`

### Pending & history
- `GetPendingPurchases() : List<InternalPurchaseItem>`
- `GetPendingPurchaseByOrderId(int orderId) : InternalPurchaseItem` — single lookup; throws if not found.
- `RetryPendingPurchasesAsync() : UniTask`
- `RetryPendingPurchaseByOrderId(int orderId) : UniTask<OrderStatus>`
- `GetThenRemoveFromRetryPendingPurchasesByOrderID(int orderId) : InternalPurchaseItem` — atomic find+remove; returns empty item when not found.
- `RemoveFromRetryPendingPurchasesByOrderID(int orderId)`
- `GetPurchaseHistory() : List<InternalPurchaseItem>`
- `RemoveFromPurchaseHistoryByOrderID(int orderId)`

### Deliverables
- `GetPendingDeliverables() : UniTask<PendingDeliverables[]>`
- `DeliverPendingDeliverablesAsync() : UniTask`

### Status checks
- `GetPurchaseStatusAsync(string productId) : Task<bool>`
- `GetProductPurchaseStatusDetailAsync(string productId) : Task<ProductPurchaseStatus>`
- `GetPurchasedProductsAsync(List<string> productIds) : Task<List<string>>`
- `CheckIfProductPurchased(string productId, Action<bool> callback)`
- `RestorePurchasedProducts(List<string> productIds) : Task<List<string>>`

### Misc
- `GetNoctuaGold() : UniTask<NoctuaGoldData>`
- `ClaimRedeemAsync(string code) : UniTask<ClaimRedeemCodeResponse>`
- `QueryPurchasesAsync()`
- `HandleUnpairedPurchaseDebugAsync(string productId, string receiptData) : UniTask`

## `Noctua.Event` — `NoctuaEventService`

From `Runtime/Presenter/NoctuaEventService.cs`.

- `SetProperties(string country="", string ipAddress="", bool isSandbox=false)`
- `SetCurrentFeature(string featureName)`
- `GetCurrentFeature() : string`
- `TrackAdRevenue(string source, double revenue, string currency, Dictionary<string,IConvertible> extraPayload=null)`
- `TrackPurchase(string orderId, double amount, string currency, Dictionary<string,IConvertible> extraPayload=null)`
- `TrackCustomEvent(string name, Dictionary<string,IConvertible> extraPayload=null)`
- `TrackCustomEventWithRevenue(string name, double revenue, string currency, Dictionary<string,IConvertible> extraPayload=null)`

## `Noctua.IAA` — `MediationManager`

From `Runtime/Presenter/MediationManager.cs`.

### Properties
- `InterstitialAdUnitID / RewardedAdUnitID / RewardedInterstitialAdUnitID / BannerAdUnitID : string`
- `AppOpenManager : AppOpenAdManager`
- `MediationType : string`
- `IsHybridMode : bool`

> `IAAResponse` (the merged runtime IAA config) is `internal` and not exposed on the public docs facade. Use the sandbox Inspector overlay to inspect the merged config.

### Events (common)
- `OnInitialized / OnAdDisplayed / OnAdFailedDisplayed / OnAdClicked / OnAdImpressionRecorded / OnAdClosed : Action`
- `OnAdNotAvailable : Action<string>`

### Events (AdMob, `#if UNITY_ADMOB`)
- `AdmobOnUserEarnedReward : Action<Reward>`
- `AdmobOnAdRevenuePaid : Action<AdValue, ResponseInfo>`
- `OnAdsAvailable : Action<PreloadConfiguration>`
- `OnAdExhausted : Action<PreloadConfiguration>`

### Events (AppLovin, `#if UNITY_APPLOVIN`)
- `AppLovinOnUserEarnedReward : Action<MaxSdk.Reward>`
- `AppLovinOnAdRevenuePaid : Action<MaxSdkBase.AdInfo>`

### Init
- `Initialize(Action initCompleteAction=null)`
- `SetupAdUnitID(IAA iAAResponse)`

### Show / hide
- `ShowInterstitial()` / `ShowInterstitial(string placement)`
- `ShowRewardedAd()` / `ShowRewardedAd(string placement)`
- `ShowRewardedInterstitialAd()`
- `ShowBannerAd()`
- `HideBannerAd()` — **network-agnostic banner hide** (added in 0.109.0). Prefer this over the legacy `HideAppLovinBanner()` / `DestroyBannerAppLovin()` / `HideBannerAppLovin()` variants, which are kept only for fine-grained network control.
- `ShowAppOpenAd()`
- `LoadInterstitialAd()` / `LoadRewardedAd()`

### Readiness
- `IsInterstitialReady() : bool`
- `IsRewardedAdReady() : bool`
- `IsAppOpenAdReady() : bool`

### Banner configuration
- `CreateBannerViewAdAdmob(AdSize, AdPosition)`
- `CreateBannerViewAdAppLovin(Color, MaxSdkBase.BannerPosition)`
- `CreateBannerViewAdAppLovin(Color, MaxSdkBase.AdViewPosition)`
- `SetBannerWidth(int)`
- `SetBannerPlacement(string)`
- `SetBannerRefreshInterval(int seconds)` — clamped to 10–120 s.
- `StartBannerAutoRefresh()` / `StopBannerAutoRefresh()`
- `GetBannerPosition() : Rect` — current banner frame in screen coordinates (AppLovin).
- `HideAppLovinBanner()` / `DestroyBannerAppLovin()` — legacy AppLovin-specific helpers; prefer `HideBannerAd()`.

### Misc
- `SetMuted(bool)`
- `OnApplicationForeground()`

### Diagnostics
- `GetSegmentKey() : string` — composite user segment, e.g. `"t1_nonpayer_loyal_d30plus"`.
- `GetExperimentAssignments() : Dictionary<string,string>` — experiment ID → variant. Persisted in PlayerPrefs.
- `GetCpmFloorStatus() : Dictionary<string,string>` — per format/network floor evaluation result.

### Diagnostics (sandbox)
- `ShowCreativeDebugger()`
- `ShowMediationDebugger()` / `ShowMediationDebugger(string networkName)`
- `SetTestDeviceIds(List<string>)`
- `ShowAdPlaceholder(AdPlaceholderType)` / `CloseAdPlaceholder()`

## `Noctua.Platform`

From `Runtime/View/NoctuaPlatform.cs`.

### `Noctua.Platform.Locale` (`NoctuaLocale`)
- `OnLanguageChanged : event Action<string>` — new active language code.
- `GetLanguage() : string` — ISO 639-1 (priority: user pref > region config > system).
- `GetCountry() : string` — persisted ISO 3166-1 alpha-2.
- `GetCurrency() : string` — persisted ISO 4217 (defaults to `"USD"`).
- `SetCountry(string)` / `SetCurrency(string)` — uppercased, persisted to PlayerPrefs.
- `SetUserPrefsLanguage(string)` — pass `null`/empty to clear the override.
- `GetTranslation(string key) : string`
- `GetTranslation(LocaleTextKey key) : string`
- `GetTranslations() : Dictionary<string,string>` — full translation dictionary for the active language.

### `Noctua.Platform.Content` (`NoctuaWebContent`)
- `ShowAnnouncement() : UniTask<bool>` — `false` if skipped (24-hour cooldown or no content).
- `ShowCustomerService(string reason = "general", string context = "") : UniTask` — both params have defaults; pass `reason` to pre-fill the support form.
- `ShowReward() : UniTask`
- `ShowSocialMedia() : UniTask<bool>` — `false` if no page is configured.

## `Noctua.Firebase` — static helpers on `Noctua`

Documented at https://docs.noctua.gg/sdk/noctua-firebase. Full usage in [firebase-and-push.md](firebase-and-push.md).

### Async getters
- `Noctua.GetFirebaseInstallationID() : Task<string>`
- `Noctua.GetFirebaseAnalyticsSessionID() : Task<string>`
- `Noctua.GetFirebaseMessagingToken() : Task<string>` — empty on iOS until APNs handshake completes; retry after 2–5 s.
- `Noctua.GetFirebaseRemoteConfigString(string key) : Task<string>`
- `Noctua.GetFirebaseRemoteConfigBoolean(string key) : Task<bool>`
- `Noctua.GetFirebaseRemoteConfigDouble(string key) : Task<double>`
- `Noctua.GetFirebaseRemoteConfigLong(string key) : Task<long>`
- `Noctua.GetAdjustAttributionAsync() : Task<NoctuaAdjustAttribution>`

### Push notification events
- `Noctua.OnRemoteNotificationReceived : event Action<NoctuaNotificationPayload>` — foreground or background delivery.
- `Noctua.OnNotificationTapped : event Action<NoctuaNotificationPayload>` — primary deeplink hook.
- `Noctua.OnFirebaseMessagingTokenRefresh : event Action<string>` — FCM token rotation; re-register with backend.

### `NoctuaNotificationPayload`
Fields: `RawJson`, `Aps` (iOS only), `Custom`, `Title`, `Body`, `Deeplink` (auto-discovered from `deeplink` / `noctua_deeplink` / `route` / `link` / `url`). Method: `GetCustomString(string key)`.

## `Noctua.App` — `NoctuaAppManager`

From `Runtime/View/NoctuaAppManager.cs`.

- `RequestInAppReview() : UniTask`
- `CheckForUpdate() : UniTask<AppUpdateInfo>` (Android only)
- `StartImmediateUpdate() : UniTask<AppUpdateResult>` (Android only)
- `StartFlexibleUpdate(Action<float> onProgress=null) : UniTask<AppUpdateResult>`
- `CompleteUpdate()`

## Types

Field lists below match https://docs.noctua.gg/sdk/types.

### Auth
| Type | Fields / values |
|---|---|
| `UserBundle` | `User`, `Player`, `Credential`, `PlayerAccounts` |
| `Player` | `Id`, `UserId`, `GameId`, `AccessToken`, `Nickname`, `AvatarUrl` |
| `Credential` | `Id`, `UserId`, `Provider` (`"email"`/`"google"`/`"facebook"`/`"guest"`/…), `DisplayText`, `VerifiedAt` |
| `CredentialVerification` | `Id`, `Channel` (e.g. `"email"`), `Target` (masked email/phone) |
| `PlayerToken` | `AccessToken`, `RefreshToken`, `Player`, `User`, `Credential` |
| `PlayerAccountData` | `Nickname`, `AvatarUrl`, `BirthDate`, `Gender`, `Language`, `Country`, `IsProfileCompleted` |
| `SocialLoginRequest` / `SocialLinkRequest` | `Code` (OAuth code/id-token), `State` (optional CSRF) |

### IAP
| Type | Fields / values |
|---|---|
| `ProductList` | `class ProductList : List<Product>` |
| `Product` | `Id`, `Description`, `GameId`, `EnabledPaymentTypes : PaymentType[]`, `Price : decimal`, `Currency`, `DisplayPrice`, `PriceInUsd`, `Platform` |
| `PurchaseRequest` | `ProductId`, `Price`, `Currency`, `RoleId`, `ServerId`, `IngameUsername`, `ExtraData` |
| `PurchaseResponse` | `OrderId`, `Status`, `Message`, `ReceiptData` |
| `OrderRequest` | `Id` (`0` for new), `PaymentType`, `ProductId`, `Price`, `Currency`, `PriceInUsd`, `RoleId`, `ServerId`, `IngameUsername`, `ExtraData` |
| `OrderStatus` | enum: `pending`, `verification_failed`, `completed`, `canceled`, `refunded`, `voided`, `unknown` |
| `InternalPurchaseItem` | `{ OrderId, OrderRequest : OrderRequest, VerifyOrderRequest : VerifyOrderRequest, AccessToken, Status, PlayerId : long?, PurchaseToken }` (verified against `Runtime/Presenter/InternalPurchaseItem.cs`). The product details live on the embedded `OrderRequest`. |
| `PaymentType` | enum: `unknown`, `playstore`, `appstore`, `direct`, `noctuawallet`, `noctuagold`, `editor` |
| `NoctuaGoldData` | `{ VipLevel, GoldAmount, BoundGoldAmount, TotalGoldAmount, EligibleGoldAmount }` — all `double`. Verified against `Runtime/Model/DTOs/IAPModels.cs`. Use `EligibleGoldAmount` for the current purchase context. |
| `PendingDeliverables` | `OrderId`, `Data : PendingDeliverablesData`, `CreatedAt` |
| `ClaimRedeemCodeResponse` | `OrderIds : List<…>`, `Message` |
| `ProductPurchaseStatus` | `{ ProductId, IsPurchased, IsAcknowledged, IsAutoRenewing, PurchaseState : int (0=Unspecified / 1=Purchased / 2=Pending), PurchaseToken, PurchaseTime : long (ms epoch), ExpiryTime : long (ms epoch; 0 if N/A — always 0 on Android), OrderId, OriginalJson, TransactionJson }` (verified against `Runtime/Model/Entities/ProductPurchaseStatus.cs`). |

### Events
| Type | Fields |
|---|---|
| `NativeEvent` | `Id`, `EventJson`, `Timestamp` |
| `NoctuaAdjustAttribution` | `{ TrackerToken, TrackerName, Network, Campaign, Adgroup, Creative, ClickLabel, Adid, CostType, CostAmount : double, CostCurrency, FbInstallReferrer }` (note: `Adgroup`, lowercase 'g'; verified against `Runtime/Model/Entities/NoctuaAdjustAttribution.cs`) |

### App
| Type | Fields / values |
|---|---|
| `AppUpdateInfo` | `{ IsUpdateAvailable, IsImmediateAllowed, IsFlexibleAllowed, AvailableVersionCode, StalenessDays }` (verified against `Runtime/Model/DTOs/AppUpdateInfo.cs`) |
| `AppUpdateResult` | enum (`Runtime/Model/DTOs/AppUpdateInfo.cs`): `Success=0`, `UserCancelled=1`, `Failed=2`, `NotAvailable=3` |

### Locale
| Type | Notes |
|---|---|
| `LocaleTextKey` | Strongly-typed UI translation keys. Common values include `IAPCanceled`, `IAPFailed`, `IAPNotReady`, `IAPRequiresAuthentication`, `IAPPaymentDisabled`, `IAPPendingPurchaseTitle`, `IAPPendingPurchaseCompleted/Refunded/Voided/Canceled/NotVerified`, `IAPPurchaseHistoryTitle`, `IAPDisabled`, `OfflineModeMessage`, `ErrorEmailEmpty/NotValid`, `ErrorPasswordEmpty/Short`, `ErrorRePasswordEmpty/NotMatch`, `AuthEmailLinkingSuccessful`. |

### Errors
| Type | Notes |
|---|---|
| `NoctuaException` | `ErrorCode : int`, `Message`, `Payload` (string; parse as JSON when present — the SDK does not populate `InnerException`). The constructor takes a `NoctuaErrorCode` and casts to `int`. |
| `NoctuaErrorCode` | enum (`Runtime/Model/Entities/NoctuaException.cs`): `Unknown=3000`, `Networking=3001`, `Application=3002`, `Authentication=3003`, `ActiveCurrencyFailure=3004`, `MissingCompletionHandler=3005`, `Payment=3006`, `AccountStorage=3007`, `PaymentStatusCanceled=3008`, `PaymentStatusItemAlreadyOwned=3009`, `PaymentStatusIapNotReady=3010`, `UserBanned=2202` |

### Misc
| Type | Notes |
|---|---|
| `GlobalConfig` | Deserialized `noctuagg.json`. |
| `IAA` | Runtime ad mediation config (`internal` outside the facade). |
