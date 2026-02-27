"""Plugin catalog discovery and synchronization service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from quiz_engine.contracts.runtime_models import PluginManifest
from quiz_engine.models.plugin_catalog import PluginCatalog
from quiz_engine.plugins.registry import discover_available_plugins

PLUGIN_TYPE_ALIASES = {
    "info": "info",
    "quiz": "quiz",
    "scoreboard": "scoreboard",
    "display_score": "scoreboard",
    "display score": "scoreboard",
    "form": "form",
}


@dataclass
class PluginCatalogScanResult:
    scanned_at: datetime
    discovered_count: int
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class PluginCatalogService:
    def list_catalog(self, session: Session) -> list[PluginCatalog]:
        stmt = select(PluginCatalog).order_by(PluginCatalog.plugin_id.asc())
        return list(session.execute(stmt).scalars())

    def scan_and_sync(self, session: Session) -> PluginCatalogScanResult:
        discovery = discover_available_plugins(include_sandbox_fallback=False)
        scanned_at = datetime.now(UTC)
        result = PluginCatalogScanResult(
            scanned_at=scanned_at,
            discovered_count=len(discovery.plugins),
            errors=list(discovery.errors),
        )

        existing_by_id = {
            row.plugin_id: row
            for row in session.execute(select(PluginCatalog)).scalars()
        }

        for plugin in discovery.plugins:
            manifest = plugin.get_manifest()
            plugin_type = _resolve_plugin_type(manifest)
            if plugin_type is None:
                result.errors.append(
                    f"Plugin {manifest.plugin_id}: missing/invalid general type"
                )
                continue

            manifest_payload = manifest.to_transport_dict()
            manifest_payload["plugin_type"] = plugin_type
            manifest_payload["schema_version"] = "v2"

            existing = existing_by_id.pop(manifest.plugin_id, None)
            if existing is None:
                session.add(
                    PluginCatalog(
                        plugin_id=manifest.plugin_id,
                        display_name=manifest.display_name,
                        plugin_version=manifest.plugin_version,
                        plugin_type=plugin_type,
                        manifest_payload=manifest_payload,
                        last_scanned_at=scanned_at,
                    )
                )
                result.added.append(manifest.plugin_id)
                continue

            changed = False
            if existing.display_name != manifest.display_name:
                existing.display_name = manifest.display_name
                changed = True
            if existing.plugin_version != manifest.plugin_version:
                existing.plugin_version = manifest.plugin_version
                changed = True
            if existing.plugin_type != plugin_type:
                existing.plugin_type = plugin_type
                changed = True
            if existing.manifest_payload != manifest_payload:
                existing.manifest_payload = manifest_payload
                changed = True
            existing.last_scanned_at = scanned_at
            if changed:
                result.updated.append(manifest.plugin_id)

        for stale in existing_by_id.values():
            result.removed.append(stale.plugin_id)
            session.delete(stale)

        session.commit()

        result.added.sort()
        result.updated.sort()
        result.removed.sort()
        return result


def _resolve_plugin_type(manifest: PluginManifest) -> str | None:
    capabilities = (
        manifest.capabilities if isinstance(manifest.capabilities, dict) else {}
    )
    raw_type = capabilities.get("general_type")
    if raw_type is None:
        raw_type = capabilities.get("plugin_type")
    if raw_type is None and manifest.plugin_id == "slide":
        raw_type = "info"
    if not isinstance(raw_type, str):
        return None

    normalized = raw_type.strip().lower()
    return PLUGIN_TYPE_ALIASES.get(normalized)
