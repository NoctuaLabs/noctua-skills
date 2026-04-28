"""Live SDK metadata from NoctuaLabs/noctua-unity-sdk-upm@main."""
from __future__ import annotations

import json
import re
from typing import Optional

from sources.upstream import fetch_upm

UNITY_TEAM_FLOOR = "2022.3.62f2"


def get_sdk_version() -> dict:
    body = fetch_upm("package.json")
    pkg = json.loads(body)
    return {
        "version": pkg.get("version"),
        "name": pkg.get("name"),
        "displayName": pkg.get("displayName"),
        "unityFloorTechnical": pkg.get("unity"),
        "unityFloorTeam": UNITY_TEAM_FLOOR,
    }


_VERSION_HEADING_RE = re.compile(r"^##\s+\[?([^\]\s]+)\]?", re.MULTILINE)


def get_changelog(since_version: Optional[str] = None) -> str:
    body = fetch_upm("CHANGELOG.md")
    if not since_version:
        return body

    target = since_version.lstrip("vV")
    headings = list(_VERSION_HEADING_RE.finditer(body))
    for i, m in enumerate(headings):
        if m.group(1).lstrip("vV") == target:
            return body[: m.start()].rstrip() + "\n"
    return body


_ANDROID_PKG_RE = re.compile(r'<androidPackage\s+spec="([^"]+)"', re.IGNORECASE)
_IOS_POD_RE = re.compile(
    r'<iosPod\s+name="([^"]+)"\s+version="([^"]+)"(?:\s+minTargetSdk="([^"]+)")?',
    re.IGNORECASE,
)


def get_native_dependencies() -> dict:
    body = fetch_upm("Editor/Dependencies/NativePluginDependencies.xml")
    android = []
    for m in _ANDROID_PKG_RE.finditer(body):
        spec = m.group(1)
        parts = spec.rsplit(":", 1)
        android.append({"spec": spec, "version": parts[1] if len(parts) == 2 else None})
    ios = []
    for m in _IOS_POD_RE.finditer(body):
        ios.append({
            "name": m.group(1),
            "version": m.group(2),
            "minTargetSdk": m.group(3),
        })
    return {"android": android, "ios": ios}


_SKADNETWORK_RE = re.compile(
    r'"([0-9a-z]{8,12})\.skadnetwork"',
    re.IGNORECASE,
)


def get_skadnetwork_ids() -> dict:
    body = fetch_upm("Editor/Build/BuildPostProcessor.cs")
    ids = sorted({m.group(1).lower() for m in _SKADNETWORK_RE.finditer(body)})
    return {"count": len(ids), "ids": ids}
