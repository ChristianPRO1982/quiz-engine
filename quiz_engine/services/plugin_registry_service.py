"""Helpers for exposing available plugin question types in the editor."""

from __future__ import annotations

from fastapi import Request

from quiz_engine.schemas.quiz_editor_schemas import QuestionTypeOption


class PluginRegistryService:
    def list_question_types(self, request: Request) -> list[QuestionTypeOption]:
        registry = getattr(request.app.state, "plugin_registry", None)
        if registry is None:
            return [QuestionTypeOption(type="slide", label="Slide")]

        options: list[QuestionTypeOption] = []
        for manifest in registry.list_manifests():
            options.append(
                QuestionTypeOption(
                    type=manifest.plugin_id,
                    label=manifest.display_name,
                    description=manifest.description,
                )
            )

        if not any(option.type == "slide" for option in options):
            options.append(QuestionTypeOption(type="slide", label="Slide"))

        options.sort(key=lambda option: (option.label.lower(), option.type.lower()))
        return options
