# `Noctua.IAP` — In-App Purchases

Source: `Packages/com.noctuagames.sdk/Runtime/Presenter/NoctuaIAPService.cs`.

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
// Set priority order of payment types tried
Noctua.IAP.SetEnabledPaymentTypes(new List<PaymentType>
{
    PaymentType.google_play,
    PaymentType.noctua
});

// Override distribution platform string (default auto-detected)
Noctua.IAP.SetDistributionPlatform("google_play");

// Force-init native billing (rarely needed)
Noctua.IAP.Init();
```

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
await Noctua.IAP.PurchaseItemAsync(request, enforcedPaymentType: PaymentType.noctua);
```

## Pending purchases

Purchases that completed at the store but haven't been verified yet (network drop, app closed mid-flow).

```csharp
List<InternalPurchaseItem> pending = Noctua.IAP.GetPendingPurchases();   // sync, local

// Retry verification for all pending
await Noctua.IAP.RetryPendingPurchasesAsync();

// Retry one specific order
OrderStatus status = await Noctua.IAP.RetryPendingPurchaseByOrderId(orderId);

// Remove from retry queue (e.g. after permanent failure)
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
- `PurchaseResponse` — `{ Status, OrderId, ... }`
- `ProductList` — `{ Items: List<ProductItem> }`
- `ProductItem` — `{ ProductId, DisplayPrice, Currency, Description, ... }`
- `OrderRequest` / `OrderStatus` — order metadata
- `InternalPurchaseItem` — local pending/history row
- `PendingDeliverables` — `{ OrderId, Items, ... }`
- `NoctuaGoldData` — `{ Balance, Currency }`
- `ClaimRedeemCodeResponse` — redeem result
- `PaymentType` — enum: `unknown`, `google_play`, `app_store`, `noctua`, ...

See `Runtime/Model/` for exact field layouts.

## Recommended flow

```csharp
Noctua.IAP.OnPurchaseDone += order => GrantContent(order);

// After init
await Noctua.IAP.RetryPendingPurchasesAsync();        // resume any pending
var products = await Noctua.IAP.GetProductListAsync(); // show store UI

// On button press
await Noctua.IAP.PurchaseItemAsync(new PurchaseRequest { ... });
```
