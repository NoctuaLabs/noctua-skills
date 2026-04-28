# noctua-sdk-mcp

MCP server that serves **live** Noctua Games Unity SDK guidance to AI coding agents.

Where the static skill in `skills/noctua-unity-sdk/` requires every game-dev team to manually re-install on each release, this MCP fetches the latest reference content and SDK metadata from upstream at query time. Game devs add it once via URL; Claude Code (and any MCP-aware agent) gets the fresh data forever.

## Tools

### Skill reference (one tool per topic, live from `noctua-skills@main`)

`get_installation`, `get_noctuagg_json`, `get_initialization`, `get_integration_checklist`, `get_authentication`, `get_iap`, `get_events`, `get_iaa_ads`, `get_iaa_event_schema`, `get_firebase_and_push`, `get_platform_features`, `get_app_manager`, `get_offline_first`, `get_android_setup`, `get_ios_setup`, `get_editor_tooling`, `get_sandbox_inspector`, `get_error_handling`, `get_session_tracking`, `get_experiments`, `get_native_event_tracking`, `get_curated_api_reference`.

Plus `list_topics` and `get_skill_manifest` for routing.

### SDK metadata (live from `noctua-unity-sdk-upm@main`)

| Tool | Source |
|---|---|
| `get_sdk_version` | `package.json` |
| `get_changelog(since_version=)` | `CHANGELOG.md` |
| `get_native_dependencies` | `Editor/Dependencies/NativePluginDependencies.xml` |
| `get_skadnetwork_ids` | `Editor/Build/BuildPostProcessor.cs` |

### C#-parsed API surface (canonical, never drifts)

| Tool | Source |
|---|---|
| `list_api_modules` | enumerates supported facades |
| `get_api_reference(module)` | `Runtime/View/<Module>/Noctua*.cs` (or matching presenter) |
| `get_noctuagg_schema` | `Runtime/Model/{Common,Event,App,Auth}/*.cs` DTOs |
| `get_error_codes` | `Runtime/Model/Common/NoctuaException.cs` |

`docs.noctua.gg/sdk` URLs are surfaced as "see also" links inside `get_api_reference`, but the C# is the source of truth — docs can lag.

## Run (LAN / self-hosted SSE — recommended)

This is the same pattern as `noctua-data-mcp` — one host on the LAN runs the server, every teammate's Claude Code points at it via SSE URL.

On the host machine:

```sh
cd mcp
python -m venv .venv && source .venv/bin/activate
pip install -e .
python server.py sse              # listens on 0.0.0.0:8000, SSE endpoint at /sse
```

Then on each teammate's machine, in `~/.claude/settings.json` (or `~/.claude.json`):

```jsonc
{
  "mcpServers": {
    "noctua-sdk": {
      "type": "sse",
      "url": "http://<host-lan-ip>:8000/sse"
    }
  }
}
```

Replace `<host-lan-ip>` with the host machine's LAN IP (e.g. `ipconfig getifaddr en0` on macOS, `hostname -I` on Linux). Restart Claude Code.

## Run locally (stdio, single-machine dev)

```sh
python server.py stdio
```

Point Claude Code at `mcp/mcp-config.json` (already wired for stdio).

## Run via Docker

```sh
docker build -t noctua-sdk-mcp mcp/
docker run --rm -p 8000:8000 noctua-sdk-mcp
# now reachable at http://<host>:8000/sse
```

## Deploy to Railway (optional)

`railway.toml` is included if you ever want to host this remotely:

```sh
railway login
railway init
railway up
```

The Dockerfile builds the same image; Railway exposes it on a public URL.

## Caching

In-memory TTL cache (5 minutes) per upstream URL. Restart the server (or wait 5 min) to pick up upstream changes.

## Adding a new skill reference

When a new `references/<topic>.md` lands in `skills/noctua-unity-sdk/`, append a row to `SKILL_REFS` in `sources/skill_refs.py` and the tool auto-registers on next start.
