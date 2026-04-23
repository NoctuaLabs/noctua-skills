# Full Public API Index

Every public member on `Noctua.*`. Use this as a single-page lookup; follow the linked reference file for detailed usage.

Source of truth: `Packages/com.noctuagames.sdk/Runtime/View/Noctua.cs` + facade classes listed per section.

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
- `Noctua.InitAsync() : UniTask`
- `Noctua.OnInitSuccess : Action` (event)
- `Noctua.IsInitialized() : bool`
- `Noctua.IsOfflineMode() : bool`
- `Noctua.IsOfflineFirst() : bool`
- `Noctua.IsOfflineAsync() : UniTask<bool>`
- `Noctua.OnOnline()` / `Noctua.OnOffline()`
- `Noctua.AdjustOfflineModeDisabled() : bool`

### Event storage (low-level)
- `Noctua.SaveEvents(string json)`
- `Noctua.GetEventsAsync() : UniTask<List<NativeEvent>>`
- `Noctua.DeleteEvents()`
- `Noctua.InsertEvent(string eventJson)`
- `Noctua.GetEventsBatchAsync(int limit, int offset) : UniTask<List<NativeEvent>>`
- `Noctua.DeleteEventsByIdsAsync(long[] ids) : Task<int>`
- `Noctua.GetEventCountAsync() : Task<int>`

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

### State
- `AccountList : IReadOnlyList<UserBundle>`
- `IsAuthenticated : bool`
- `RecentAccount : UserBundle`

### Events
- `OnAccountChanged : Action<UserBundle>`
- `OnAccountDeleted : Action<Player>`

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
- `Init()`
- `SetEnabledPaymentTypes(List<PaymentType>)`
- `SetDistributionPlatform(string platform)`

### Products & purchase
- `GetProductListAsync(string currency=null, string platformType=null) : UniTask<ProductList>`
- `PurchaseItemAsync(PurchaseRequest, bool tryToUseSecondaryPayment=false, PaymentType enforcedPaymentType=PaymentType.unknown) : UniTask<PurchaseResponse>`
- `GetActiveCurrencyAsync(string productId) : UniTask<string>`

### Pending & history
- `GetPendingPurchases() : List<InternalPurchaseItem>`
- `RetryPendingPurchasesAsync() : UniTask`
- `RetryPendingPurchaseByOrderId(int orderId) : UniTask<OrderStatus>`
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
- `IAAResponse : IAA`
- `MediationType : string`
- `IsHybridMode : bool`

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
- `ShowBannerAd()` / `HideBannerAd()`
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
- `SetBannerRefreshInterval(int seconds)`
- `StartBannerAutoRefresh()` / `StopBannerAutoRefresh()`
- `HideAppLovinBanner()` / `DestroyBannerAppLovin()`

### Misc
- `SetMuted(bool)`
- `OnApplicationForeground()`
- `GetSegmentKey() : string`

### Diagnostics (sandbox)
- `ShowCreativeDebugger()`
- `ShowMediationDebugger()` / `ShowMediationDebugger(string networkName)`
- `SetTestDeviceIds(List<string>)`
- `ShowAdPlaceholder(AdPlaceholderType)` / `CloseAdPlaceholder()`

## `Noctua.Platform`

From `Runtime/View/NoctuaPlatform.cs`.

### `Noctua.Platform.Locale` (`NoctuaLocale`)
- `GetLanguage() : string`
- `GetCountry() : string`
- `GetCurrency() : string`
- `SetCountry(string)`
- `SetCurrency(string)`
- `SetUserPrefsLanguage(string)`
- `GetTranslation(string key) : string`
- `GetTranslation(LocaleTextKey key) : string`

### `Noctua.Platform.Content` (`NoctuaWebContent`)
- `ShowAnnouncement() : UniTask`
- `ShowCustomerService() : UniTask`
- `ShowReward() : UniTask`
- `ShowSocialMedia() : UniTask`

## `Noctua.App` — `NoctuaAppManager`

From `Runtime/View/NoctuaAppManager.cs`.

- `RequestInAppReview() : UniTask`
- `CheckForUpdate() : UniTask<AppUpdateInfo>` (Android only)
- `StartImmediateUpdate() : UniTask<AppUpdateResult>` (Android only)
- `StartFlexibleUpdate(Action<float> onProgress=null) : UniTask<AppUpdateResult>`
- `CompleteUpdate()`

## Types (selected)

| Type | Purpose |
|---|---|
| `UserBundle` | `{ Player, Credential, AccessToken, ... }` |
| `Player` | `{ Id, Nickname, Picture, ... }` |
| `Credential` | Linked credential descriptor |
| `CredentialVerification` | `{ Id, Method }` — pending email verification |
| `PlayerToken` | Short-lived token (password reset) |
| `PlayerAccountData` | Updatable profile fields |
| `SocialLoginRequest` / `SocialLinkRequest` | Provider-specific payload |
| `PurchaseRequest` | `{ ProductId, Price, Currency, RoleId, ServerId }` |
| `PurchaseResponse` | `{ Status, OrderId, ... }` |
| `ProductList` | `{ Items }` |
| `ProductItem` | `{ ProductId, DisplayPrice, Currency, Description, ... }` |
| `OrderRequest` / `OrderStatus` | Order lifecycle |
| `InternalPurchaseItem` | Local pending/history row |
| `PendingDeliverables` | `{ OrderId, Items, ... }` |
| `NoctuaGoldData` | `{ Balance, Currency }` |
| `ClaimRedeemCodeResponse` | Redeem result |
| `PaymentType` | Enum: `unknown`, `google_play`, `app_store`, `noctua`, ... |
| `NoctuaException` | `{ ErrorCode, Message }` |
| `NoctuaErrorCode` | Enum: `Application`, `Authentication`, `UserBanned`, `Payment`, `Networking` |
| `GlobalConfig` | Full deserialized `noctuagg.json` |
| `AppUpdateInfo` / `AppUpdateResult` | In-app update state |
| `IAA` | Runtime ad mediation config |
| `NativeEvent` | Raw stored event row |
