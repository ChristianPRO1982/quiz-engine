"""Helpers for exposing available plugin question types in the editor."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import Request

from quiz_engine.contracts.runtime_models import StageContext, StageDefinition
from quiz_engine.schemas.quiz_editor_schemas import QuestionTypeOption


class PluginRegistryService:
    def list_question_types(self, request: Request) -> list[QuestionTypeOption]:
        registry = getattr(request.app.state, "plugin_registry", None)
        if registry is None:
            return [
                QuestionTypeOption(
                    type="slide",
                    label="Slide",
                    plugin_type="info",
                    default_stage_config={},
                )
            ]

        options: list[QuestionTypeOption] = []
        for manifest in registry.list_manifests():
            capabilities = (
                manifest.capabilities if isinstance(manifest.capabilities, dict) else {}
            )
            plugin_type = getattr(manifest, "plugin_type", None) or capabilities.get(
                "general_type"
            )
            stage_config_schema = getattr(manifest, "stage_config_schema", None)
            default_stage_config = getattr(manifest, "default_stage_config", None)
            editor_hints = getattr(manifest, "editor_hints", None)
            options.append(
                QuestionTypeOption(
                    type=manifest.plugin_id,
                    label=manifest.display_name,
                    description=manifest.description,
                    plugin_type=plugin_type if isinstance(plugin_type, str) else None,
                    stage_config_schema=(
                        stage_config_schema
                        if isinstance(stage_config_schema, dict)
                        else None
                    ),
                    default_stage_config=(
                        default_stage_config
                        if isinstance(default_stage_config, dict)
                        else {}
                    ),
                    editor_hints=(
                        editor_hints if isinstance(editor_hints, dict) else None
                    ),
                )
            )

        if not any(option.type == "slide" for option in options):
            options.append(
                QuestionTypeOption(
                    type="slide",
                    label="Slide",
                    plugin_type="info",
                    default_stage_config={},
                )
            )

        options.sort(key=lambda option: (option.label.lower(), option.type.lower()))
        return options

    def build_preview_view_model(
        self,
        request: Request,
        *,
        quiz_id: int,
        stage_index: int,
        stage_id: str,
        plugin_id: str,
        stage_title: str,
        plugin_spec: dict[str, Any],
    ) -> dict[str, Any]:
        registry = getattr(request.app.state, "plugin_registry", None)
        if registry is None:
            return self._placeholder_view_model(
                plugin_id=plugin_id,
                stage_title=stage_title,
                reason="Plugin registry unavailable.",
            )

        plugin = registry.get(plugin_id)
        if plugin is None:
            return self._placeholder_view_model(
                plugin_id=plugin_id,
                stage_title=stage_title,
                reason="No preview renderer registered.",
            )

        try:
            stage = StageDefinition(
                stage_id=stage_id,
                stage_index=stage_index,
                plugin_id=plugin_id,
                stage_kind=plugin_id,
                engine_prompt={},
                plugin_spec=plugin_spec,
            )
            runtime = plugin.create_runtime("preview-session", stage)
            context = StageContext(
                session_id="preview-session",
                quiz_id=str(quiz_id),
                stage=stage,
                server_now=datetime.now(UTC),
                players=[],
            )
            frames = runtime.on_stage_open(context) or []
        except Exception as exc:
            return self._placeholder_view_model(
                plugin_id=plugin_id,
                stage_title=stage_title,
                reason=str(exc),
            )

        frame = next(
            (
                candidate
                for candidate in frames
                if candidate.frame_type == "VIEW_MODEL"
                and isinstance(candidate.payload, dict)
            ),
            None,
        )
        if frame is None:
            return self._placeholder_view_model(
                plugin_id=plugin_id,
                stage_title=stage_title,
                reason="No VIEW_MODEL frame produced.",
            )

        return {
            "kind": "plugin_frame",
            "plugin_id": plugin_id,
            "frame_type": frame.frame_type,
            "payload": frame.payload,
            "is_placeholder": False,
            "reason": None,
        }

    def _placeholder_view_model(
        self, *, plugin_id: str, stage_title: str, reason: str
    ) -> dict[str, Any]:
        return {
            "kind": "placeholder",
            "plugin_id": plugin_id,
            "frame_type": "VIEW_MODEL",
            "payload": {
                "title": stage_title,
                "body": (
                    f"Preview unavailable for '{plugin_id}'. "
                    "This plugin is shown as a static placeholder."
                ),
            },
            "is_placeholder": True,
            "reason": reason,
        }
