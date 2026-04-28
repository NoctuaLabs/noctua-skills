"""Lightweight C# extractor for Noctua's facade and DTO style.

The upstream codebase uses straightforward `public` declarations with XML doc
comments and `[JsonProperty("name")]` attributes on DTO fields. Regex is enough.

Public surface:
- extract_public_members(source) -> dict with `methods`, `properties`, `events`, `class_doc`
- extract_dto_fields(source) -> list of {json_name, csharp_name, type, default, doc}
- extract_enum(source) -> dict with `name`, `summary`, `values: [{name, value, doc}]`
"""
from __future__ import annotations

import re

# Strip /* ... */ block comments (XML doc /// is preserved separately by being matched first)
_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_LINE_COMMENT_RE = re.compile(r"^[ \t]*//(?!/).*$", re.MULTILINE)  # // but not ///

# An XML doc block: one or more contiguous /// lines.
_DOC_BLOCK_RE = re.compile(r"((?:^[ \t]*///[^\n]*\n)+)", re.MULTILINE)
_SUMMARY_RE = re.compile(r"<summary>(.*?)</summary>", re.DOTALL | re.IGNORECASE)


def _clean_doc(doc: str) -> str:
    """Pull <summary> out of a /// XML doc block, collapse whitespace."""
    if not doc:
        return ""
    text = "\n".join(line.lstrip().lstrip("/").strip() for line in doc.splitlines())
    m = _SUMMARY_RE.search(text)
    body = m.group(1) if m else text
    return re.sub(r"\s+", " ", body).strip()


def _strip_comments_keep_doc(source: str) -> str:
    s = _BLOCK_COMMENT_RE.sub("", source)
    s = _LINE_COMMENT_RE.sub("", s)
    return s


def _annotate_with_docs(source: str) -> list[tuple[str, str]]:
    """Split source into (preceding_doc, following_chunk) pairs at each /// block."""
    pieces: list[tuple[str, str]] = []
    last_end = 0
    last_doc = ""
    for m in _DOC_BLOCK_RE.finditer(source):
        pre_chunk = source[last_end:m.start()]
        if last_doc or pre_chunk.strip():
            pieces.append((last_doc, pre_chunk))
        last_doc = m.group(1)
        last_end = m.end()
    pieces.append((last_doc, source[last_end:]))
    return pieces


_METHOD_RE = re.compile(
    r"public\s+(?!class|interface|enum|struct|partial)"
    r"(?:async\s+)?"
    r"(?:static\s+)?"
    r"(?:virtual\s+|override\s+|sealed\s+|new\s+)?"
    r"([\w<>?\[\],\s\.]+?)\s+"           # return type
    r"([A-Z]\w+)\s*"                      # method name (PascalCase)
    r"(\([^)]*\))"                        # parameter list (no nested parens supported)
    r"(?=\s*(?:where\s+\w+\s*:[^{;]+)?\s*[{;])",
)
_PROPERTY_RE = re.compile(
    r"public\s+(?!class|interface|enum|struct)"
    r"(?:static\s+)?"
    r"(?:readonly\s+)?"
    r"([\w<>?\[\],\s\.]+?)\s+"
    r"([A-Z]\w+)\s*"
    r"(?:=>\s*[^;]+;|\{\s*get;[^}]*\})",
)
_EVENT_RE = re.compile(
    r"public\s+event\s+([\w<>?\[\],\s\.]+?)\s+([A-Z]\w+)\s*[;{]"
)
_CLASS_DECL_RE = re.compile(
    r"public\s+(?:partial\s+)?(?:sealed\s+)?(?:abstract\s+)?class\s+(\w+)"
)


def extract_public_members(source: str) -> dict:
    cleaned = _strip_comments_keep_doc(source)
    pairs = _annotate_with_docs(cleaned)

    class_doc = ""
    cls_match = _CLASS_DECL_RE.search(cleaned)
    class_name = cls_match.group(1) if cls_match else ""
    if cls_match:
        # Find the doc immediately preceding the class declaration
        for doc, chunk in pairs:
            if _CLASS_DECL_RE.search(chunk):
                class_doc = _clean_doc(doc)
                break

    methods: list[dict] = []
    properties: list[dict] = []
    events: list[dict] = []

    for doc, chunk in pairs:
        cleaned_doc = _clean_doc(doc)

        for m in _METHOD_RE.finditer(chunk):
            ret, name, params = m.group(1).strip(), m.group(2), m.group(3)
            # filter out constructors (return type would equal class name and no return part)
            if name == class_name:
                continue
            methods.append({
                "name": name,
                "return_type": ret,
                "signature": f"{ret} {name}{params}",
                "summary": cleaned_doc,
            })
        for m in _PROPERTY_RE.finditer(chunk):
            properties.append({
                "name": m.group(2),
                "type": m.group(1).strip(),
                "summary": cleaned_doc,
            })
        for m in _EVENT_RE.finditer(chunk):
            events.append({
                "name": m.group(2),
                "type": m.group(1).strip(),
                "summary": cleaned_doc,
            })

    return {
        "class": class_name,
        "summary": class_doc,
        "methods": _dedupe_by_name(methods),
        "properties": _dedupe_by_name(properties),
        "events": _dedupe_by_name(events),
    }


def _dedupe_by_name(items: list[dict]) -> list[dict]:
    seen: dict[str, dict] = {}
    for it in items:
        seen.setdefault(it["name"], it)
    return list(seen.values())


_DTO_FIELD_RE = re.compile(
    r'\[JsonProperty\(\s*"([^"]+)"\s*\)\]\s*'
    r'public\s+([\w<>?\[\],\s\.]+?)\s+(\w+)\s*'
    r'(?:=\s*([^;]+?))?\s*;'
)


def extract_dto_fields(source: str) -> list[dict]:
    cleaned = _strip_comments_keep_doc(source)
    pairs = _annotate_with_docs(cleaned)
    out: list[dict] = []
    for doc, chunk in pairs:
        for m in _DTO_FIELD_RE.finditer(chunk):
            out.append({
                "json_name": m.group(1),
                "csharp_name": m.group(3),
                "type": m.group(2).strip(),
                "default": (m.group(4) or "").strip() or None,
                "doc": _clean_doc(doc),
            })
    return out


_ENUM_RE = re.compile(r"public\s+enum\s+(\w+)\s*\{([^}]*)\}", re.DOTALL)
_ENUM_MEMBER_RE = re.compile(
    r"(\w+)\s*=\s*(\d+|0x[0-9a-fA-F]+)\s*[,}]"
)


def extract_enum(source: str, enum_name: str | None = None) -> dict | None:
    cleaned = _strip_comments_keep_doc(source)
    pairs = _annotate_with_docs(cleaned)
    for m in _ENUM_RE.finditer(cleaned):
        name = m.group(1)
        if enum_name and name != enum_name:
            continue
        body = m.group(2)
        # Find enum-level doc
        enum_doc = ""
        for doc, chunk in pairs:
            if re.search(rf"public\s+enum\s+{name}\b", chunk):
                enum_doc = _clean_doc(doc)
                break

        members: list[dict] = []
        member_pairs = _annotate_with_docs(body)
        for mdoc, mchunk in member_pairs:
            for em in _ENUM_MEMBER_RE.finditer(mchunk):
                val = em.group(2)
                ival = int(val, 16) if val.startswith("0x") else int(val)
                members.append({
                    "name": em.group(1),
                    "value": ival,
                    "doc": _clean_doc(mdoc),
                })
        return {"name": name, "summary": enum_doc, "values": members}
    return None
