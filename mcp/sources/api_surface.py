"""High-level API surface tools backed by `csharp_parser` against the upm repo."""
from __future__ import annotations

from server_types import ApiModule, DtoFile
from sources import csharp_parser
from sources.upstream import fetch_upm

# Module slug -> facade C# file. Discovered from
# https://api.github.com/repos/NoctuaLabs/noctua-unity-sdk-upm/contents/Runtime/View
API_MODULES: list[ApiModule] = [
    ApiModule(
        slug="auth",
        facade_path="Runtime/View/Auth/NoctuaAuthentication.cs",
        docs_url="https://docs.noctua.gg/sdk/auth",
    ),
    ApiModule(
        slug="iap",
        facade_path="Runtime/Presenter/IAP/NoctuaIAPService.cs",
        docs_url="https://docs.noctua.gg/sdk/iap",
    ),
    ApiModule(
        slug="event",
        facade_path="Runtime/Presenter/Event/NoctuaEventService.cs",
        docs_url="https://docs.noctua.gg/sdk/event",
    ),
    ApiModule(
        slug="iaa",
        facade_path="Runtime/Presenter/IAA/MediationManager.cs",
        docs_url="https://docs.noctua.gg/sdk/iaa",
    ),
    ApiModule(
        slug="platform",
        facade_path="Runtime/View/Platform/NoctuaPlatform.cs",
        docs_url="https://docs.noctua.gg/sdk/platform",
    ),
    ApiModule(
        slug="app",
        facade_path="Runtime/View/App/NoctuaAppManager.cs",
        docs_url="https://docs.noctua.gg/sdk/app",
    ),
    ApiModule(
        slug="noctua",
        facade_path="Runtime/View/Noctua.cs",
        docs_url="https://docs.noctua.gg/sdk/noctua",
    ),
]

# DTO files contributing to noctuagg.json (canonical schema source — Newtonsoft drops
# anything not present here). Discovered under Runtime/Model/.
NOCTUAGG_DTOS: list[DtoFile] = [
    DtoFile(section="root",       path="Runtime/Model/Common/GlobalConfig.cs"),
    DtoFile(section="noctua",     path="Runtime/Model/Common/NoctuaConfig.cs"),
    DtoFile(section="copublisher",path="Runtime/Model/Common/CoPublisherConfig.cs"),
    DtoFile(section="adjust",     path="Runtime/Model/Event/AdjustConfig.cs"),
    DtoFile(section="firebase",   path="Runtime/Model/App/FirebaseConfig.cs"),
    DtoFile(section="facebook",   path="Runtime/Model/Auth/FacebookConfig.cs"),
    DtoFile(section="gameservice",path="Runtime/Model/App/GameServiceModels.cs"),
]

NOCTUA_EXCEPTION_PATH = "Runtime/Model/Common/NoctuaException.cs"


def list_api_modules() -> list[dict]:
    return [{"slug": m.slug, "docs_url": m.docs_url, "source_path": m.facade_path} for m in API_MODULES]


def get_api_reference(module: str) -> dict:
    mod = next((m for m in API_MODULES if m.slug == module), None)
    if mod is None:
        raise ValueError(f"unknown module '{module}'. Try one of: {', '.join(m.slug for m in API_MODULES)}")
    source = fetch_upm(mod.facade_path)
    parsed = csharp_parser.extract_public_members(source)
    return {
        "module": mod.slug,
        "source_path": mod.facade_path,
        "docs_url": mod.docs_url,
        **parsed,
        "markdown": _render_module_markdown(mod, parsed),
    }


def get_noctuagg_schema() -> dict:
    sections: dict[str, list[dict]] = {}
    for dto in NOCTUAGG_DTOS:
        try:
            source = fetch_upm(dto.path)
        except Exception as e:
            sections[dto.section] = [{"_error": str(e), "_source": dto.path}]
            continue
        sections[dto.section] = csharp_parser.extract_dto_fields(source)
    return {
        "note": "Canonical noctuagg.json schema parsed from Runtime/Model/* DTOs. Anything not listed here is silently ignored at runtime by the Newtonsoft deserializer.",
        "sections": sections,
        "sources": [d.path for d in NOCTUAGG_DTOS],
    }


def get_error_codes() -> dict:
    source = fetch_upm(NOCTUA_EXCEPTION_PATH)
    enum = csharp_parser.extract_enum(source, "NoctuaErrorCode")
    return enum or {"name": "NoctuaErrorCode", "values": [], "_warning": "enum not found"}


def _render_module_markdown(mod: ApiModule, parsed: dict) -> str:
    lines: list[str] = []
    lines.append(f"# Noctua.{mod.slug} — public API")
    lines.append("")
    lines.append(f"_Source: `{mod.facade_path}` · Docs: <{mod.docs_url}>_")
    lines.append("")
    if parsed.get("summary"):
        lines.append(f"> {parsed['summary']}")
        lines.append("")

    def section(title: str, items: list[dict]) -> None:
        if not items:
            return
        lines.append(f"## {title}")
        lines.append("")
        for it in items:
            sig = it.get("signature") or f"{it.get('type','')} {it.get('name','')}".strip()
            lines.append(f"### `{sig}`")
            if it.get("summary"):
                lines.append("")
                lines.append(it["summary"])
            lines.append("")

    section("Methods", parsed.get("methods", []))
    section("Properties", parsed.get("properties", []))
    section("Events", parsed.get("events", []))
    return "\n".join(lines).rstrip() + "\n"
