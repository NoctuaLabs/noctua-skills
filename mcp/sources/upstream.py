"""Cached HTTP fetcher for raw.githubusercontent.com and other upstreams.

In-memory TTL cache keyed on URL. 5-minute default; tunable per call. Avoids
hammering GitHub raw on every tool invocation.
"""
from __future__ import annotations

import time
from threading import Lock
from typing import Optional

import httpx

SKILLS_REPO = "NoctuaLabs/noctua-skills"
UPM_REPO = "NoctuaLabs/noctua-unity-sdk-upm"
DEFAULT_TTL = 300  # 5 minutes
DEFAULT_BRANCH = "main"

_cache: dict[str, tuple[float, str]] = {}
_lock = Lock()


def raw_url(repo: str, path: str, ref: str = DEFAULT_BRANCH) -> str:
    return f"https://raw.githubusercontent.com/{repo}/{ref}/{path}"


def fetch(url: str, ttl: int = DEFAULT_TTL) -> str:
    """GET `url`, cached for `ttl` seconds. Raises on non-2xx."""
    now = time.monotonic()
    with _lock:
        hit = _cache.get(url)
        if hit is not None:
            ts, body = hit
            if now - ts < ttl:
                return body

    resp = httpx.get(url, timeout=15.0, follow_redirects=True)
    resp.raise_for_status()
    body = resp.text

    with _lock:
        _cache[url] = (now, body)
    return body


def fetch_skill(path: str, ttl: int = DEFAULT_TTL) -> str:
    return fetch(raw_url(SKILLS_REPO, path), ttl)


def fetch_upm(path: str, ttl: int = DEFAULT_TTL) -> str:
    return fetch(raw_url(UPM_REPO, path), ttl)


def invalidate(url: Optional[str] = None) -> None:
    with _lock:
        if url is None:
            _cache.clear()
        else:
            _cache.pop(url, None)
