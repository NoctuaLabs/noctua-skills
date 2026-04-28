from dataclasses import dataclass


@dataclass(frozen=True)
class SkillRef:
    """A markdown reference file in skills/noctua-unity-sdk/references/ exposed as a tool."""
    name: str          # snake_case identifier (also the tool name suffix), e.g. "iap"
    path: str          # repo-relative path, e.g. "skills/noctua-unity-sdk/references/iap.md"
    description: str   # one-line tool description shown to the LLM


@dataclass(frozen=True)
class ApiModule:
    """A C# facade module whose public surface is parsed live from the upstream repo."""
    slug: str          # tool argument value, e.g. "auth"
    facade_path: str   # upstream repo path to the View/<Module>/Noctua*.cs file
    docs_url: str      # canonical docs.noctua.gg/sdk/<...> URL for "see also"


@dataclass(frozen=True)
class DtoFile:
    """A C# DTO file that contributes fields to the noctuagg.json schema."""
    section: str       # logical section in noctuagg.json (e.g. "noctua", "adjust", "firebase")
    path: str          # upstream repo path
