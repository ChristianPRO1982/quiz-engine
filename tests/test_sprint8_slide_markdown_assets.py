"""Frontend asset checks for plugin-driven quiz editor behavior."""

from __future__ import annotations

from pathlib import Path


def test_editor_js_uses_plugin_driven_json_authoring_without_slide_hardcode() -> None:
    source = Path("quiz_engine/static/js/quiz_editor.js").read_text(encoding="utf-8")

    assert "Configuration (JSON)" in source
    assert "createSchemaAutoForm" in source
    assert "Advanced JSON" in source
    assert 'new Set(["schema_version", "type", "plugin"])' in source
    assert "defaultStageConfig" in source
    assert "stageConfigSchema" in source
    assert 'question.type === "slide"' not in source


def test_slide_renderer_blocks_raw_html_injection_patterns() -> None:
    source = Path("quiz_engine/static/js/slide_renderer.js").read_text(encoding="utf-8")

    assert "createTextNode" in source
    assert "innerHTML" not in source
    assert "javascript|data|vbscript" in source
