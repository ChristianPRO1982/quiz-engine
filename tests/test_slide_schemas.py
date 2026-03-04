"""Tests for SLIDE schema validation helpers."""

from __future__ import annotations

import pytest

from quiz_engine.plugins.slide.schemas import (
    build_slide_frame_payload,
    validate_slide_plugin_spec,
)


def _valid_spec() -> dict:
    return {
        "schema_version": "v1",
        "title": "Title",
        "body": "Body",
    }


def test_validate_slide_plugin_spec_accepts_minimal_payload() -> None:
    validated = validate_slide_plugin_spec(_valid_spec())
    assert validated["content"] == {
        "title": "Title",
        "body": "Body",
        "body_format": "text",
    }
    assert validated["schema_version"] == "v1"


def test_build_slide_frame_payload_keeps_media_when_present() -> None:
    spec = _valid_spec()
    spec["media"] = {"type": "image", "src": "https://img"}
    payload = build_slide_frame_payload(spec)
    assert payload["media"]["type"] == "image"
    assert payload["body_format"] == "text"


def test_build_slide_frame_payload_accepts_image_url_alias() -> None:
    spec = _valid_spec()
    spec["image_url"] = "https://cdn.example.org/slide.png"

    payload = build_slide_frame_payload(spec)

    assert payload["media"] == {
        "type": "image",
        "src": "https://cdn.example.org/slide.png",
    }


def test_validate_slide_plugin_spec_accepts_explicit_body_format_markdown() -> None:
    spec = _valid_spec()
    spec["body_format"] = "markdown"

    validated = validate_slide_plugin_spec(spec)

    assert validated["content"]["body_format"] == "markdown"


def test_slide_spec_accepts_media_text_hint_ignored_by_runtime() -> None:
    spec = {
        "schema_version": "v1",
        "content": {
            "title": "Slide",
            "body": "Body",
            "body_format": "markdown",
            "media_text": "https://example.org/image.png",
        },
    }

    validated = validate_slide_plugin_spec(spec)
    payload = build_slide_frame_payload(spec)

    assert validated["content"]["title"] == "Slide"
    assert "media_text" not in validated["content"]
    assert "media" not in payload


def test_validate_slide_plugin_spec_rejects_unknown_body_format() -> None:
    spec = _valid_spec()
    spec["body_format"] = "html"

    with pytest.raises(ValueError, match="body_format"):
        validate_slide_plugin_spec(spec)


def test_validate_slide_plugin_spec_rejects_non_dict_plugin_spec() -> None:
    with pytest.raises(ValueError):
        validate_slide_plugin_spec([])  # type: ignore[arg-type]


def test_validate_slide_plugin_spec_rejects_unknown_root_keys() -> None:
    spec = _valid_spec()
    spec["extra"] = True
    with pytest.raises(ValueError):
        validate_slide_plugin_spec(spec)


def test_validate_slide_plugin_spec_rejects_schema_version_and_type() -> None:
    bad_schema = _valid_spec()
    bad_schema["schema_version"] = "v9"
    with pytest.raises(ValueError):
        validate_slide_plugin_spec(bad_schema)

    bad_type = _valid_spec()
    bad_type["type"] = "other"
    with pytest.raises(ValueError):
        validate_slide_plugin_spec(bad_type)


def test_validate_slide_plugin_spec_rejects_non_string_title() -> None:
    spec = _valid_spec()
    spec["title"] = 7
    with pytest.raises(ValueError):
        validate_slide_plugin_spec(spec)


def test_validate_slide_plugin_spec_rejects_unknown_content_keys() -> None:
    spec = _valid_spec()
    spec["bad"] = "x"
    with pytest.raises(ValueError):
        validate_slide_plugin_spec(spec)


def test_validate_slide_plugin_spec_rejects_invalid_media_type() -> None:
    spec = _valid_spec()
    spec["media"] = {"type": "video", "src": None}
    with pytest.raises(ValueError):
        validate_slide_plugin_spec(spec)


def test_validate_slide_plugin_spec_rejects_invalid_media_src_type() -> None:
    spec = _valid_spec()
    spec["media"] = {"type": "image", "src": 123}
    with pytest.raises(ValueError):
        validate_slide_plugin_spec(spec)


def test_validate_slide_plugin_spec_rejects_media_none_with_src() -> None:
    spec = _valid_spec()
    spec["media"] = {"type": "none", "src": "x"}
    with pytest.raises(ValueError):
        validate_slide_plugin_spec(spec)


def test_validate_slide_plugin_spec_rejects_media_image_with_blank_src() -> None:
    spec = _valid_spec()
    spec["media"] = {"type": "image", "src": " "}
    with pytest.raises(ValueError):
        validate_slide_plugin_spec(spec)


def test_validate_slide_plugin_spec_accepts_legacy_v0_shape() -> None:
    legacy = {
        "schema_version": "v0",
        "type": "slide",
        "content": {
            "title": "Legacy",
            "body": "Body",
        },
    }

    validated = validate_slide_plugin_spec(legacy)

    assert validated["schema_version"] == "v0"
    assert validated["content"]["title"] == "Legacy"
