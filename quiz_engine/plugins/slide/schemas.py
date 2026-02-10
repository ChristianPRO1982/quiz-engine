"""Schema validation for the SLIDE plugin spec (v0)."""

from __future__ import annotations

from typing import Any

ALLOWED_MEDIA_TYPES = {"image", "none"}


def validate_slide_plugin_spec(plugin_spec: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize the SLIDE plugin spec.

    Expected shape:
    {
      "schema_version": "v0",
      "type": "slide",
      "content": {
        "title": str,
        "body": str,
        "media"?: {"type": "image"|"none", "src": str|None}
      }
    }
    """
    _require_dict(plugin_spec, "plugin_spec")
    _reject_unknown_keys(
        plugin_spec,
        {"schema_version", "type", "content"},
        "plugin_spec",
    )

    schema_version = plugin_spec.get("schema_version")
    if schema_version != "v0":
        raise ValueError("plugin_spec.schema_version must be 'v0'.")

    plugin_type = plugin_spec.get("type")
    if plugin_type != "slide":
        raise ValueError("plugin_spec.type must be 'slide'.")

    content = _require_dict(plugin_spec.get("content"), "plugin_spec.content")
    _reject_unknown_keys(content, {"title", "body", "media"}, "plugin_spec.content")

    title = _require_str(content.get("title"), "plugin_spec.content.title")
    body = _require_str(content.get("body"), "plugin_spec.content.body")

    normalized_content: dict[str, Any] = {"title": title, "body": body}
    if "media" in content:
        normalized_content["media"] = _validate_media(content["media"])

    return {
        "schema_version": "v0",
        "type": "slide",
        "content": normalized_content,
    }


def build_slide_frame_payload(plugin_spec: dict[str, Any]) -> dict[str, Any]:
    """Build a frame payload from a validated plugin spec."""
    validated = validate_slide_plugin_spec(plugin_spec)
    content = validated["content"]
    payload: dict[str, Any] = {
        "title": content["title"],
        "body": content["body"],
    }
    if "media" in content:
        payload["media"] = content["media"]
    return payload


def _validate_media(media: Any) -> dict[str, Any]:
    media_dict = _require_dict(media, "plugin_spec.content.media")
    _reject_unknown_keys(media_dict, {"type", "src"}, "plugin_spec.content.media")

    media_type = _require_str(media_dict.get("type"), "plugin_spec.content.media.type")
    if media_type not in ALLOWED_MEDIA_TYPES:
        raise ValueError(
            "plugin_spec.content.media.type must be one of: 'image', 'none'."
        )

    src = media_dict.get("src")
    if src is not None and not isinstance(src, str):
        raise ValueError("plugin_spec.content.media.src must be a string or null.")
    if media_type == "none" and src is not None:
        raise ValueError(
            "plugin_spec.content.media.src must be null when type is 'none'."
        )
    if media_type == "image" and (not isinstance(src, str) or src.strip() == ""):
        raise ValueError(
            "plugin_spec.content.media.src must be a non-empty string when type "
            "is 'image'."
        )

    return {"type": media_type, "src": src}


def _require_dict(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a dict.")
    return value


def _require_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")
    return value


def _reject_unknown_keys(
    data: dict[str, Any], allowed: set[str], field_name: str
) -> None:
    extra = set(data) - allowed
    if extra:
        extras = ", ".join(sorted(extra))
        raise ValueError(f"{field_name} has unsupported field(s): {extras}.")
