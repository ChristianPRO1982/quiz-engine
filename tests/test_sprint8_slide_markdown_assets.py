"""Sprint 8 frontend asset checks for SLIDE markdown support."""

from __future__ import annotations

from pathlib import Path


def test_editor_js_exposes_slide_markdown_authoring_controls() -> None:
    source = Path("quiz_engine/static/js/quiz_editor.js").read_text(encoding="utf-8")

    assert "Slide body (Markdown)" in source
    assert "Markdown supported." in source
    assert "body_format" in source


def test_slide_renderer_blocks_raw_html_injection_patterns() -> None:
    source = Path("quiz_engine/static/js/slide_renderer.js").read_text(encoding="utf-8")

    assert "createTextNode" in source
    assert "innerHTML" not in source
    assert "javascript|data|vbscript" in source
