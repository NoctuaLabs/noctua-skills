"""noctua-sdk-mcp — FastMCP server exposing live Noctua Unity SDK guidance.

Tools fall into three groups:
1. `get_<topic>` — one per skills/noctua-unity-sdk/references/*.md, fetched live
   from the noctua-skills repo.
2. SDK metadata — `get_sdk_version`, `get_changelog`, `get_native_dependencies`,
   `get_skadnetwork_ids`.
3. C#-parsed API surface — `list_api_modules`, `get_api_reference`,
   `get_noctuagg_schema`, `get_error_codes`.

Run:
    python server.py stdio                # local Claude Code dev
    python server.py streamable-http      # remote deploy (Railway, Fly, etc.)
"""
from __future__ import annotations

import json
import os
import sys

from mcp.server.fastmcp import FastMCP

from server_types import SkillRef
from sources import api_surface, sdk_meta, skill_refs

PORT = int(os.environ.get("PORT", "8000"))
mcp = FastMCP("noctua-sdk", host="0.0.0.0", port=PORT)


# ── Skill reference tools (auto-registered, one per references/*.md) ──────────


def _register_skill_ref(ref: SkillRef) -> None:
    def _fn() -> str:
        return skill_refs.get_skill_markdown(ref.name)

    _fn.__name__ = f"get_{ref.name}"
    _fn.__doc__ = (
        f"{ref.description}\n\n"
        f"Returns the live markdown of {ref.path} from the noctua-skills repo (main branch)."
    )
    mcp.tool()(_fn)


for _ref in skill_refs.SKILL_REFS:
    _register_skill_ref(_ref)


@mcp.tool()
def list_topics() -> str:
    """Routing table: every skill reference topic with one-line description and source path.

    Call this first when you don't know which `get_<topic>` tool to use.
    """
    return json.dumps(skill_refs.list_topics_payload(), indent=2)


@mcp.tool()
def get_skill_manifest() -> str:
    """Live SKILL.md from the noctua-skills repo (the durable skill manifest)."""
    return skill_refs.get_skill_manifest()


# ── SDK metadata tools ────────────────────────────────────────────────────────


@mcp.tool()
def get_sdk_version() -> str:
    """Current Noctua Unity SDK version + Unity floor, parsed from upstream package.json."""
    return json.dumps(sdk_meta.get_sdk_version(), indent=2)


@mcp.tool()
def get_changelog(since_version: str = "") -> str:
    """Upstream CHANGELOG.md. If `since_version` is given (e.g. "0.109.0"), returns entries newer than it."""
    return sdk_meta.get_changelog(since_version or None)


@mcp.tool()
def get_native_dependencies() -> str:
    """Android packages and iOS pods declared in Editor/Dependencies/NativePluginDependencies.xml."""
    return json.dumps(sdk_meta.get_native_dependencies(), indent=2)


@mcp.tool()
def get_skadnetwork_ids() -> str:
    """SKAdNetwork IDs the SDK injects into Info.plist at iOS build time, parsed from BuildPostProcessor.cs."""
    return json.dumps(sdk_meta.get_skadnetwork_ids(), indent=2)


# ── C#-parsed API surface tools ───────────────────────────────────────────────


@mcp.tool()
def list_api_modules() -> str:
    """Available `module` slugs for `get_api_reference` (auth, iap, event, iaa, platform, app, noctua)."""
    return json.dumps(api_surface.list_api_modules(), indent=2)


@mcp.tool()
def get_api_reference(module: str) -> str:
    """Live public API for a Noctua facade, parsed from upstream C# source.

    Args:
        module: One of the slugs returned by `list_api_modules` (e.g. "auth", "iap").

    Returns JSON with class summary, methods, properties, events, plus a markdown rendering.
    """
    try:
        return json.dumps(api_surface.get_api_reference(module), indent=2)
    except ValueError as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def get_noctuagg_schema() -> str:
    """Canonical noctuagg.json schema, parsed live from Runtime/Model/* C# DTOs.

    The Newtonsoft deserializer silently ignores any field not present here, so this is
    the authoritative answer to "is field X valid?".
    """
    return json.dumps(api_surface.get_noctuagg_schema(), indent=2)


@mcp.tool()
def get_error_codes() -> str:
    """The NoctuaErrorCode enum (name, numeric value, summary) parsed from NoctuaException.cs."""
    return json.dumps(api_surface.get_error_codes(), indent=2)


# ── Entrypoint ────────────────────────────────────────────────────────────────


def main() -> None:
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
