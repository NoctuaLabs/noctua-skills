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
// gold.Balance, gold.Currency, ...
```

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
- `NoctuaGoldData` — `{ Balance, Currency, UpdatedAt }`
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
