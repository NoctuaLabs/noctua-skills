# Experiments, Segments, and CPM Floors

> **Sources** — Official APIs: https://docs.noctua.gg/sdk/noctua (`SetExperiment` / `Get*Experiment`), https://docs.noctua.gg/sdk/iaa (`GetSegmentKey`, `GetExperimentAssignments`, `GetCpmFloorStatus`) · Tutorial: https://docs.noctua.gg/docs/unity/iaa/advanced-configuration · Repo: [Runtime/Presenter/ExperimentManager.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/Presenter/ExperimentManager.cs), [AdExperimentManager.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/Presenter/AdExperimentManager.cs), [CpmFloorManager.cs](https://github.com/NoctuaLabs/noctua-unity-sdk-upm/blob/main/Runtime/Presenter/CpmFloorManager.cs)

The SDK exposes three related but distinct mechanisms for varying behavior per user:

| Mechanism | API | Lifetime | Purpose |
|---|---|---|---|
| **General experiment tag** | `Noctua.SetGeneralExperiment(key, value)` / `GetGeneralExperiment(key)` | Per-session, in-memory | Free-form key/value flag attached to every event via `ExperimentManager` |
| **Active experiment name** | `Noctua.SetExperiment(name)` / `GetActiveExperiment()` | Per-session, in-memory | Single-string label for the user's current A/B variant |
| **User segment** | `Noctua.IAA.GetSegmentKey()` | Server-assigned, refreshed each init | Derived bucket (whale / mid / new / etc.) used to gate ad config |
| **Ad experiment variant** | `noctuagg.json → iaa.ad_experiments` (server-merged) | Server-assigned | A/B variant for ad placements (mediation order, floors, formats) |
| **CPM floors** | `noctuagg.json → iaa.cpm_floors` (server-merged) | Server-assigned per segment | Minimum bid floor applied per format, optionally segment-overridden |

Source: `Runtime/View/Noctua.cs:436-463`, `Runtime/Presenter/ExperimentManager.cs`, `Runtime/Presenter/AdExperimentManager.cs`, `Runtime/Presenter/CpmFloorManager.cs`, `Runtime/Presenter/UserSegmentManager.cs`.

## General experiment tag

Use this when you want a piece of state to ride along on every analytics event:

```csharp
Noctua.SetGeneralExperiment("loot_drop", "2x");

// Later, every Noctua.Event.* emission carries { "loot_drop": "2x" }
// (under the experiment-tag dimension consumed by ExperimentManager).

string current = Noctua.GetGeneralExperiment("loot_drop"); // "2x"
```

Multiple keys are supported — call `SetGeneralExperiment` once per key. Values are strings; cast on the read side.

## Active experiment name

A single-string label, useful when your A/B platform assigns one variant per user:

```csharp
Noctua.SetExperiment("tutorial_v3");
string variant = Noctua.GetActiveExperiment(); // "tutorial_v3"
```

The active name is attached to all session events (`session_*`, `noctua_user_engagement*`, `native_user_engagement`) so cohort splits work without extra payload plumbing.

## User segment (read-only)

The SDK assigns a segment server-side at init based on spending / engagement profile. Game code can read it but cannot set it:

```csharp
string segment = Noctua.IAA.GetSegmentKey();   // e.g. "whale", "mid", "new"
```

Use the segment for analytics dimensions only. Do not branch gameplay on it without product approval — it's a monetization signal, not a feature flag.

## CPM floors and ad experiments

These are configured entirely in `noctuagg.json → iaa.cpm_floors` and `iaa.ad_experiments` (and overridable server-side). Game code does not call them directly. Useful diagnostic actions in the sandbox **Inspector** overlay:

- **Show Segment** — print the current `GetSegmentKey()` value.
- **Show Experiments** — list active ad experiments and the user's variant.
- **Show CPM Floors** — list the floor table currently applied (post server-merge), keyed by format and segment.

If a placement is failing to fill in production but working in test, check that the assigned segment isn't applying a floor higher than the network's available bids.

## Server-merge semantics

All four mechanisms above (active experiment, ad experiments, CPM floors, segments) are populated from the server config that `Noctua.InitAsync()` fetches. The merge is **field-by-field** against the local `noctuagg.json` block, so you can ship a baseline locally and tune it remotely without a game update. Frequency caps and cooldowns merge the same way (see [iaa-ads.md](iaa-ads.md#frequency-caps--cooldowns)).
