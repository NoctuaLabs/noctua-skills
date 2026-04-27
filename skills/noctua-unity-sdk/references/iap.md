# `Noctua.IAP` — In-App Purchases

> **Sources** — Official API: https://docs.noctua.gg/sdk/iap · Tutorials: https://docs.noctua.gg/docs/unity/iap/overview, /implementing-in-app-purchase, /displaying-in-game-products, /item-delivery, /restore-purchases, /refund-mechanism, /implementing-noctua-gold, /noctua-redeem, /setup-skus-in-stores, /non-consumable-product-that-contains-consumable-currency · Types: https://docs.noctua.gg/sdk/types · Repo: [Runtime/Presenter/NoctuaIAPService.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/Presenter/NoctuaIAPService.cs)

Supports Google Play Billing (Android), StoreKit (iOS), and Noctua direct payment (web). Handles verification, pending state, redeem codes, Noctua Gold balance.

## Properties & events

```csharp
// True once native billing is initialized
bool ready = Noctua.IAP.IsReady;

// Fires after backend-verified purchase (safe to grant content)
Noctua.IAP.OnPurchaseDone    += (OrderRequest o) => { /* o.Id, o.ProductId */ };

// Fires when payment completed but verification still in-flight
Noctua.IAP.OnPurchasePending += (OrderRequest o) => { /* show "verifying..." */ };
```

Wire both before `Noctua.InitAsync()` — see [initialization.md](initialization.md).

## Setup

Usually you don't need to call these — `InitAsync` runs them. Override only when needed:

```csharp
// Set priority order of payment types tried.
// Enum values per https://docs.noctua.gg/sdk/types (PaymentType section):
//   unknown, playstore, appstore, direct, noctuawallet, noctuagold, editor
Noctua.IAP.SetEnabledPaymentTypes(new List<PaymentType>
{
    PaymentType.playstore,
    PaymentType.noctuawallet
});

// Override distribution platform string (default auto-detected)
Noctua.IAP.SetDistributionPlatform("google_play");
```

> `Noctua.IAP.Init()` is `internal` (`NoctuaIAPService.cs:122`) — do not call it from game code. The facade is initialized for you by `Noctua.InitAsync()`. Wait for `IsReady` to flip true before calling purchase methods.

## List products

```csharp
ProductList products = await Noctua.IAP.GetProductListAsync();

// Optional: filter by currency and/or platform
ProductList idrProducts = await Noctua.IAP.GetProductListAsync(currency: "IDR");
ProductList webOnly     = await Noctua.IAP.GetProductListAsync(platformType: "web");

foreach (var p in products.Items)
{
    Debug.Log($"{p.ProductId} — {p.DisplayPrice} ({p.Currency})");
}
```

Thrown if: player not authenticated, game ID missing.

## Purchase

```csharp
var request = new PurchaseRequest
{
    ProductId = "com.example.gem_pack_small",
    Price     = 0.99m,
    Currency  = "USD",
    RoleId    = "game-role-id",
    ServerId  = "game-server-id"
};

try
{
    PurchaseResponse result = await Noctua.IAP.PurchaseItemAsync(request);
    // `result.Status` / `result.OrderId` — content grant happens via OnPurchaseDone
}
catch (NoctuaException nex) when (nex.ErrorCode == 2046)
{
    // User canceled
}
catch (NoctuaException nex)
{
    Debug.LogError($"IAP {nex.ErrorCode}: {nex.Message}");
}
```

Optional flags:
```csharp
// Try secondary payment type if primary fails
await Noctua.IAP.PurchaseItemAsync(request, tryToUseSecondaryPayment: true);

// Force a specific payment type
await Noctua.IAP.PurchaseItemAsync(request, enforcedPaymentType: PaymentType.noctuawallet);
```

## Pending purchases

Purchases that completed at the store but haven't been verified yet (network drop, app closed mid-flow).

```csharp
List<InternalPurchaseItem> pending = Noctua.IAP.GetPendingPurchases();   // sync, local

// Look up a single pending purchase (throws if not found)
InternalPurchaseItem item = Noctua.IAP.GetPendingPurchaseByOrderId(orderId);

// Retry verification for all pending
await Noctua.IAP.RetryPendingPurchasesAsync();

// Retry one specific order
OrderStatus status = await Noctua.IAP.RetryPendingPurchaseByOrderId(orderId);

// Atomic find + remove (returns empty item if not found)
InternalPurchaseItem removed = Noctua.IAP.GetThenRemoveFromRetryPendingPurchasesByOrderID(orderId);

// Remove from retry queue without returning the item
Noctua.IAP.RemoveFromRetryPendingPurchasesByOrderID(orderId);
```

## Deliverables (content grants)

After verification, the server produces a **deliverable** — the content the player should receive.

```csharp
PendingDeliverables[] pending = await Noctua.IAP.GetPendingDeliverables();

foreach (var d in pending) { GrantContent(d); }

// Acknowledge to the server (call after granting)
await Noctua.IAP.DeliverPendingDeliverablesAsync();
```

## Purchase history

```csharp
List<InternalPurchaseItem> history = Noctua.IAP.GetPurchaseHistory();
Noctua.IAP.RemoveFromPurchaseHistoryByOrderID(orderId);
```

## Check / restore previously purchased products

```csharp
// Single product
bool owned = await Noctua.IAP.GetPurchaseStatusAsync("com.example.remove_ads");

// Detailed status
ProductPurchaseStatus detail = await Noctua.IAP.GetProductPurchaseStatusDetailAsync("com.example.remove_ads");

// Batch — returns owned IDs
List<string> owned = await Noctua.IAP.GetPurchasedProductsAsync(new List<string>
{
    "com.example.remove_ads", "com.example.vip_badge"
});

// Callback-style
Noctua.IAP.CheckIfProductPurchased("com.example.remove_ads", owned => { /* ... */ });

// iOS / Play restore — ask store to re-emit entitlements
List<string> restored = await Noctua.IAP.RestorePurchasedProducts(new List<string>
{
    "com.example.remove_ads"
});
```

## Noctua Gold

```csharp
NoctuaGoldData gold = await Noctua.IAP.GetNoctuaGold();
// gold.VipLevel, gold.GoldAmount, gold.BoundGoldAmount,
// gold.TotalGoldAmount, gold.EligibleGoldAmount
```

`NoctuaGoldData` fields (verified against `Runtime/Model/DTOs/IAPModels.cs`):

| Field | Type | Meaning |
|---|---|---|
| `VipLevel` | `double` | Player's VIP tier |
| `GoldAmount` | `double` | Free / spendable Noctua Gold |
| `BoundGoldAmount` | `double` | Bound (non-transferable) Noctua Gold |
| `TotalGoldAmount` | `double` | Free + bound |
| `EligibleGoldAmount` | `double` | Amount usable for the **current** purchase context (use this in your store UI) |

## Redeem codes

```csharp
ClaimRedeemCodeResponse res = await Noctua.IAP.ClaimRedeemAsync("ABCD-1234-EFGH");
```

## Debug helpers (sandbox)

```csharp
await Noctua.IAP.HandleUnpairedPurchaseDebugAsync(productId, receiptData);
Noctua.IAP.QueryPurchasesAsync();
string currency = await Noctua.IAP.GetActiveCurrencyAsync(productId);
```

## Error codes

| Code | Meaning | Typical UX |
|---|---|---|
| 2043 | Purchase pending verification | "Still verifying…" spinner; will resolve via `OnPurchaseDone` later |
| 2044 | Verification failed | Show error; offer retry |
| 2045 | Delivery callback failed | Content granted at server but your delivery callback errored — retry grant |
| 2046 | User canceled | Silently dismiss |
| 2047 | Refunded | Revoke content |
| 2048 | Voided | Revoke content |

Plus `NoctuaErrorCode.Payment` for category-level errors. See [error-handling.md](error-handling.md).

## Key types

- `PurchaseRequest` — `{ ProductId, Price, Currency, RoleId, ServerId }`
- `PurchaseResponse` — `{ OrderId, Status, Message, ReceiptData }`
- `ProductList` — `class ProductList : List<Product>` (the list itself; iterate directly).
- `Product` — `{ Id, Description, GameId, EnabledPaymentTypes : PaymentType[], Price : decimal, Currency, DisplayPrice, PriceInUsd, Platform }`
- `OrderRequest` — `{ Id, PaymentType, ProductId, Price, Currency, PriceInUsd, RoleId, ServerId, IngameUsername, ExtraData }`
- `OrderStatus` — enum: `pending`, `verification_failed`, `completed`, `canceled`, `refunded`, `voided`, `unknown`
- `InternalPurchaseItem` — local pending/history row: `{ OrderId, ProductId, Status, Timestamp, ReceiptData }`
- `PendingDeliverables` — `{ OrderId, Data : PendingDeliverablesData, CreatedAt }`
- `NoctuaGoldData` — `{ VipLevel, GoldAmount, BoundGoldAmount, TotalGoldAmount, EligibleGoldAmount }` — see [Noctua Gold](#noctua-gold) for field semantics
- `ClaimRedeemCodeResponse` — `{ OrderIds, Message }`
- `PaymentType` — enum: `unknown`, `playstore`, `appstore`, `direct`, `noctuawallet`, `noctuagold`, `editor`

See [api-reference.md](api-reference.md#types) for the canonical type table or https://docs.noctua.gg/sdk/types for the upstream definitions.

## Recommended flow

```csharp
Noctua.IAP.OnPurchaseDone += order => GrantContent(order);

// After init
await Noctua.IAP.RetryPendingPurchasesAsync();        // resume any pending
var products = await Noctua.IAP.GetProductListAsync(); // show store UI

// On button press
await Noctua.IAP.PurchaseItemAsync(new PurchaseRequest { ... });
```

## Implementation guide — store SKU setup

Configure the same Product ID in **App Store Connect** and **Google Play Console**:

- **App Store Connect:** App → In-App Purchases → create products. Match the Product ID exactly (e.g. `noctua.100coins`).
- **Google Play Console:** App → Monetize → Products → In-app products → Create.
- The SDK supports **single SKU mapped to multiple in-game items** — one store entry can grant several content drops based on game-side mapping.
- Skip this step entirely if the Noctua team provides default SKUs.

## Implementation guide — displaying products

`GetProductListAsync()` is the single source of truth for what to show. It returns localized prices ready for display — **do not maintain your own product table**:

```csharp
ProductList products = await Noctua.IAP.GetProductListAsync();
for (int i = 0; i < products.Count; i++)
{
    var p = products[i];
    // p.Id          → use as PurchaseRequest.ProductId
    // p.Price       → numeric (decimal)
    // p.Currency    → ISO-4217
    // p.DisplayPrice → already locale-formatted (e.g. "Rp 16.000")
    // p.Description → store-side copy
    SpawnStoreCard(p);
}
```

Cross-reference the player's owned non-consumable list to grey out already-purchased items — see [Non-consumable + consumable hybrid recipe](#recipe-non-consumable-with-consumable-currency).

## Implementation guide — purchase flow with `OnPurchaseDone` wiring

The cardinal rule: **wire `OnPurchaseDone` immediately before `Noctua.InitAsync()` in the same execution flow** (per https://docs.noctua.gg/docs/unity/iap/item-delivery). Splitting it into another class breaks pending-purchase resume.

```csharp
public class NoctuaSDKInitializer : MonoBehaviour
{
    private async void Awake()
    {
        // Wire FIRST — pending purchases from a prior session can resume during InitAsync.
        Noctua.IAP.OnPurchaseDone   += order => DeliverItem(order);
        Noctua.IAP.OnPurchasePending += order => ShowVerifyingSpinner(order);

        try { await Noctua.InitAsync(); }
        catch (NoctuaException nex) { /* show retry dialog */ return; }

        // AuthenticateAsync is required even if you don't expose login UI —
        // it does silent guest auth and is required for IAP to function.
        await Noctua.Auth.AuthenticateAsync();
    }
}
```

In the Unity Editor a mock payment sheet replaces the real store flow — product listing and order creation hit real servers, only the payment confirmation step is mocked. No code changes needed; the SDK detects Editor automatically.

### Pending purchases — `OnPurchasePending`

Fires when the store reports payment-in-flight (e.g. user paid via convenience store / slow card). **Do not deliver content** — wait for `OnPurchaseDone`. Show a "verifying" UI; the user can wait or restart the app and the SDK retries automatically.

## Implementation guide — Local vs Server delivery

| Approach | Use when |
|---|---|
| **Local delivery** (`OnPurchaseDone` only) | Casual / offline-capable games, no game server, instant gratification |
| **Server delivery** (webhook) | Server-authoritative games, fraud prevention, audit trails, mid-core / live-ops |

Best practice for production: **implement both** — local for UX, server-side webhook for verification + persistence.

### Server delivery (webhook)

Register your endpoint in the Noctua Developer Dashboard. The SDK backend POSTs a verified payload after each successful purchase:

**Headers:** `X-CALLBACK-TOKEN: <your_secret_token>` — compare against the secret from the dashboard, reject mismatches with 403.

**Body:**
```json
{
  "data": {
    "order_id": 1234567890,
    "order_status": "completed",
    "order_time": "2024-01-01T12:00:00Z",
    "product_id": "com.yourgame.gems100",
    "amount": 16000,
    "currency": "IDR",
    "amount_in_usd": 1.99,
    "player_id": 987654321,
    "ingame_item_id": "gems_100_pack",
    "ingame_role_id": "player_role_123",
    "ingame_server_id": "game_server_1",
    "platform": "appstore",
    "os": "ios",
    "extra": { "promotion_code": "SUMMERSALE" }
  },
  "signed_data": "eyJhbGciOiJFUzI1NiIs..."
}
```

**Verify `signed_data`** (preferred over `data`) — it is a JWS signed with the same JWKS as the user access token (https://sdk-api-v2.noctuaprojects.com/api/v1/auth/jwks). Cache the JWKS server-side. ES256 algorithm. PHP / Node.js samples in https://docs.noctua.gg/docs/unity/iap/item-delivery#request-body.

**Idempotency is mandatory** — the SDK retries on non-200 responses, so repeat deliveries with the same `order_id` must be no-ops.

**`order_status` values:** `unknown` · `pending` · `completed` · `failed` · `refunded` · `canceled` · `expired`.

**`platform` values:** `direct` · `playstore` · `playstore_redeem` · `appstore` · `huaweistore` · `playstationstore` · `microsoftstore` · `nintentdostore` · `noctuastore` · `noctuastore_redeem`.

**`os` values:** `android` · `ios` · `windows` · `playstation4` · `playstation5` · `xboxxs` · `nintendoswitch`.

**Response:** any 200 with arbitrary body (e.g. `{"success": true}`) acks the delivery. Return non-200 (400 / 401 / 500) only when you genuinely cannot process the payload — Noctua retries automatically on errors.

## Implementation guide — Restore Purchases (iOS requirement)

Apple **requires** every iOS app with IAPs to expose a "Restore Purchases" button. Use `RestorePurchasedProducts` (re-asks the store for entitlements) or `GetPurchasedProductsAsync` (asks the Noctua backend cache):

```csharp
private readonly List<string> _nonConsumableIds = new()
{
    "noctua.mygame.noads",
    "noctua.mygame.premium",
    "noctua.mygame.starterpack"
};

private async void OnRestoreTapped()
{
    try
    {
        var owned = await Noctua.IAP.GetPurchasedProductsAsync(_nonConsumableIds);
        foreach (var id in owned) GrantNonConsumable(id);
        if (owned.Count == 0) ShowToast("No purchases to restore.");
    }
    catch (NoctuaException nex)
    {
        Debug.LogError($"Restore {nex.ErrorCode}: {nex.Message}");
    }
}
```

**Limitations** — these APIs work for non-consumables only. Consumable products and redeem-based purchases never appear in the result.

## Implementation guide — Refund mechanism (non-consumables)

Because `GetPurchaseStatusAsync` / `GetPurchasedProductsAsync` reflect the active store entitlements, removed entitlements imply a refund. The Play Store occasionally returns stale lists, so guard refund-removal with two filters (per https://docs.noctua.gg/docs/unity/iap/refund-mechanism):

```csharp
foreach (var item in playerItems)
{
    bool stillOwned = await Noctua.IAP.GetPurchaseStatusAsync(item.ProductId);

    if (!stillOwned
        && !item.Consumable                                       // non-consumable only
        && item.PurchaseTimestamp < DateTime.UtcNow.AddDays(-2)   // age out flapping
        && (item.PaymentType == "playstore" || item.PaymentType == "appstore"))
    {
        RemovePlayerItem(item.ProductId);
    }
}
```

Run this after `Noctua.InitAsync` completes, and again before showing the store / inventory. **Maintain your own purchased-item table** keyed by `{ProductId, ProductType, PaymentType, PurchaseTimestamp}` — the SDK does not provide an inventory cache.

Refund handling for **consumable** products is not yet supported.

## Recipe — non-consumable that grants consumable currency

Bundles you can only buy once but which dispense consumable currency (e.g. "Starter Pack" → 1000 coins) should be configured as **non-consumable** in the store. Then:

1. **Display** — overlay the "Owned" badge using your local inventory (not the store list) so the player can't repurchase.
2. **Retrieve** — in `OnPurchaseDone`, store the non-consumable in inventory **and** add coins. Only convert once per `order_id` to avoid re-grant on restore.
3. **Refund** — when refund detection (above) removes the bundle, decide per game policy whether to claw back the coins. Most games leave the soft currency in place.

## Implementation guide — Noctua Redeem codes

Lets the Noctua admin tools mint codes that grant items in-game. Players enter the code in your own UI:

```csharp
try
{
    await Noctua.IAP.ClaimRedeemAsync(redeemCodeFromUiInput);
}
catch (NoctuaException nex)
{
    Debug.LogError($"Redeem {nex.ErrorCode}: {nex.Message}");
}
```

After a successful claim, the item is delivered through the same `OnPurchaseDone` (or webhook) path as a regular purchase. Distinguish the two by the `payment_type` / `platform` field — redemptions use `noctuastore_redeem`. `GetPurchaseStatusAsync` will **not** reflect redeem orders, so don't gate the redeem UI on it.

## Implementation guide — Noctua Gold display

Top up at https://noctua.gg/topup. Exchange rate: **1 USD = 100 Noctua Gold**. When the Noctua Store payment is prioritized in the dashboard, the SDK auto-selects Noctua Gold if balance covers the price; otherwise it falls back to the platform store's payment sheet.

Refresh the displayed balance:

- Before showing the in-game store
- Immediately after every successful purchase

```csharp
NoctuaGoldData gold = await Noctua.IAP.GetNoctuaGold();
goldLabel.text = gold.EligibleGoldAmount.ToString("N0");   // most useful for store UI
```

`EligibleGoldAmount` is the spendable amount in the current purchase context — prefer it over `GoldAmount` for store-side display.
