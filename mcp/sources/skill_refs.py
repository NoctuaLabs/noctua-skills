"""Auto-discover skills/noctua-unity-sdk/references/*.md and expose each as a tool.

The list of files is hard-coded (one entry per topic) so the MCP can advertise its
tool surface without hitting the network at startup. Descriptions match the
routing table in skills/noctua-unity-sdk/SKILL.md. When a new reference file is
added to the skill, append a row here.
"""
from __future__ import annotations

from server_types import SkillRef
from sources.upstream import fetch_skill

REFERENCES_DIR = "skills/noctua-unity-sdk/references"

SKILL_REFS: list[SkillRef] = [
    SkillRef("installation", f"{REFERENCES_DIR}/installation.md",
             "UPM install, prerequisites, Unity / iOS / Android floors, ATT and camera permissions."),
    SkillRef("noctuagg_json", f"{REFERENCES_DIR}/noctuagg-json.md",
             "noctuagg.json template and per-section field reference."),
    SkillRef("initialization", f"{REFERENCES_DIR}/initialization.md",
             "Bootstrap flow, event wiring before InitAsync, offline-auth recovery."),
    SkillRef("integration_checklist", f"{REFERENCES_DIR}/integration-checklist.md",
             "Pre-launch checklist: store-side prereqs, build patches, test plan."),
    SkillRef("authentication", f"{REFERENCES_DIR}/authentication.md",
             "Login, logout, switch account, cloud save, banned user, JWKS validation."),
    SkillRef("iap", f"{REFERENCES_DIR}/iap.md",
             "Purchase flow, pending purchases, restore, refund, Noctua Gold, redeem, webhooks."),
    SkillRef("events", f"{REFERENCES_DIR}/events.md",
             "Custom events, eventMap, feature engagement, game stage, ad revenue, built-in analytics."),
    SkillRef("iaa_ads", f"{REFERENCES_DIR}/iaa-ads.md",
             "Banner, interstitial, rewarded, app-open ads; adapter install; hybrid fallback; main-thread."),
    SkillRef("iaa_event_schema", f"{REFERENCES_DIR}/iaa-event-schema.md",
             "ad_loaded, ad_impression, wf_* IAA event tracking schema."),
    SkillRef("firebase_and_push", f"{REFERENCES_DIR}/firebase-and-push.md",
             "Firebase IDs, Remote Config, Adjust attribution, push setup, FCM testing, pseudo user ID."),
    SkillRef("platform_features", f"{REFERENCES_DIR}/platform-features.md",
             "Announcement, customer service, reward, social media, locale change, receive-rewards webhook."),
    SkillRef("app_manager", f"{REFERENCES_DIR}/app-manager.md",
             "In-app review, app update (immediate / flexible)."),
    SkillRef("offline_first", f"{REFERENCES_DIR}/offline-first.md",
             "Offline-first behaviour, connectivity API, offline auth recovery."),
    SkillRef("android_setup", f"{REFERENCES_DIR}/android-setup.md",
             "Android manifest, gradle, permissions."),
    SkillRef("ios_setup", f"{REFERENCES_DIR}/ios-setup.md",
             "iOS Info.plist, SKAdNetworks, CocoaPods."),
    SkillRef("editor_tooling", f"{REFERENCES_DIR}/editor-tooling.md",
             "Noctua Integration Manager, CocoaPods fixer."),
    SkillRef("sandbox_inspector", f"{REFERENCES_DIR}/sandbox-inspector.md",
             "Sandbox Inspector overlay, Trackers tab, log filters, Taichi, SDK log retrieval."),
    SkillRef("error_handling", f"{REFERENCES_DIR}/error-handling.md",
             "NoctuaException, error codes, try/catch patterns."),
    SkillRef("session_tracking", f"{REFERENCES_DIR}/session-tracking.md",
             "session_* events, engagement time."),
    SkillRef("experiments", f"{REFERENCES_DIR}/experiments.md",
             "A/B experiments, segments, CPM floors."),
    SkillRef("native_event_tracking", f"{REFERENCES_DIR}/native-event-tracking.md",
             "Native (Android / iOS) event tracking when the Unity facade isn't enough."),
    SkillRef("curated_api_reference", f"{REFERENCES_DIR}/api-reference.md",
             "Curated, handwritten public API list. For machine-parsed live API, prefer get_api_reference()."),
]


def get_skill_markdown(name: str) -> str:
    for ref in SKILL_REFS:
        if ref.name == name:
            return fetch_skill(ref.path)
    raise ValueError(f"unknown skill reference: {name}")


def list_topics_payload() -> list[dict[str, str]]:
    return [{"name": r.name, "description": r.description, "path": r.path} for r in SKILL_REFS]


def get_skill_manifest() -> str:
    return fetch_skill("skills/noctua-unity-sdk/SKILL.md")
