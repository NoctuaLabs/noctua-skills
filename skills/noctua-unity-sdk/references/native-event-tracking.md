# Native (Android / iOS) Event Tracking

> **Sources** — Tutorials: https://docs.noctua.gg/docs/android-native · /android-native/custom-event-tracking · /android-native/tracking-revenue · https://docs.noctua.gg/docs/ios-native · /ios-native/custom-event-tracking · /ios-native/tracking-revenue · Cross-platform overview: https://docs.noctua.gg/docs/unity/tracking/overview

This page is a **pointer file** — for native (non-Unity) integrations OR Unity teams that need to instrument event tracking from native code (e.g. inside a custom Android plugin or an iOS native module that the Unity layer doesn't have access to).

For Unity-side instrumentation use [events.md](events.md). The Noctua Unity SDK already wires the native tracker — game code in C# should always prefer `Noctua.Event.TrackCustomEvent` over reaching into the native bridge.

## Native SDK availability

| Surface | Android Native | iOS Native | Notes |
|---|---|---|---|
| Auth | Not available | Not available | Unity-only |
| IAP | Not available | Not available | Unity-only |
| IAA | Not available | Not available | Unity-only |
| **Event tracking** | **Available** | **Available** | This page |
| Platform features | Not available | Not available | Unity-only |

Event tracking is the only feature exposed in standalone native SDKs today.

## Android Native — minimal bootstrap

Per https://docs.noctua.gg/docs/android-native:

```gradle
dependencies {
    implementation "com.noctuagames.sdk:noctua-android-sdk:<latest-version>"
}
```

Place `noctuagg.json` (and `google-services.json` if Firebase is in scope) under `Assets/`. Init from `Application.onCreate`:

```kotlin
import com.noctuagames.sdk.Noctua

class MyApp : Application() {
    override fun onCreate() {
        super.onCreate()
        Noctua.init(this, emptyList())
    }
}

override fun onResume() { super.onResume(); Noctua.onResume() }
override fun onPause()  { super.onPause();  Noctua.onPause()  }
```

Required `noctuagg.json` field for native integrations:
- `offlineFirstEnabled` (`bool`) — set `true` for offline-first behaviour.

For custom-event tracking and revenue tracking call APIs see the matching native tutorials:
- https://docs.noctua.gg/docs/android-native/custom-event-tracking
- https://docs.noctua.gg/docs/android-native/tracking-revenue

## iOS Native — minimal bootstrap

Per https://docs.noctua.gg/docs/ios-native:

```ruby
# Podfile
pod 'NoctuaSDK'
```

```bash
pod install
```

Place `noctuagg.json` (and `GoogleService-Info.plist` if applicable) in your Xcode project (typically under `Project/`). Init in your App entry:

```swift
@main
struct NoctuaSDKExampleApp: App {
    init() {
        try! Noctua.initNoctua()
    }
    var body: some Scene {
        WindowGroup { ContentView() }
    }
}
```

For custom-event and revenue tracking APIs see:
- https://docs.noctua.gg/docs/ios-native/custom-event-tracking
- https://docs.noctua.gg/docs/ios-native/tracking-revenue

## When to use native event tracking from a Unity project

Almost never. The Unity facade `Noctua.Event.TrackCustomEvent` already routes through the native bridge to Adjust + Firebase + Facebook + Noctua tracker API. Reach for native event APIs only when:

1. You have a Unity-as-a-library setup where the native shell needs to record a lifecycle event before Unity finishes loading.
2. You write a custom Android `Service` or iOS background task that runs outside the Unity activity / view controller and needs to emit analytics.
3. You're integrating Noctua into an existing Android / iOS app where the Unity portion is a sub-screen.

In all other Unity scenarios, use C# (`Noctua.Event.*`) — see [events.md](events.md).

## Cross-platform parity

The native Custom Events Tracking and Revenue Tracking surfaces follow the same conceptual API as the Unity / Godot SDKs:

- `TrackCustomEvent(name, params)` / `TrackCustomEventWithRevenue(name, revenue, currency, params)`
- `TrackPurchase(orderId, amount, currency, extra)`
- `TrackAdRevenue(source, revenue, currency, extra)`

Event names defined in `noctuagg.json → adjust.<platform>.eventMap` route to Adjust by token; unmapped events still reach Firebase + Facebook + Noctua. The Integration Manifest Document Noctua provides per-game lists which events to fire and where in the gameplay loop.

## Related

- [events.md](events.md) — Unity-side event tracking (preferred for Unity projects)
- [iaa-event-schema.md](iaa-event-schema.md) — IAA event payload schema (the same schema is emitted on all platforms)
- [sandbox-inspector.md](sandbox-inspector.md) — Inspector overlay (Unity-only) and platform-agnostic log filters for Firebase / Adjust / Facebook verification
