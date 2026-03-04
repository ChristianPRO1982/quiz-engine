"""Schema helpers for the built-in SLIDE plugin."""

from __future__ import annotations

from typing import Any

_ALLOWED_ROOT_KEYS = {
    "schema_version",
    "type",
    "title",
    "body",
    "body_format",
    "media",
    "image_url",
    "content",
}
_ALLOWED_CONTENT_KEYS = {
    "title",
    "body",
    "body_format",
    "media",
    "image_url",
    "media_text",
}
_ALLOWED_MEDIA_KEYS = {"type", "src"}


def validate_slide_plugin_spec(plugin_spec: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize raw slide plugin_spec."""
    if not isinstance(plugin_spec, dict):
        raise ValueError("slide plugin_spec must be an object.")

    _require_only_known_keys(
        plugin_spec,
        allowed=_ALLOWED_ROOT_KEYS,
        field_name="slide plugin_spec",
    )

    schema_version = _normalize_schema_version(plugin_spec.get("schema_version"))
    _validate_slide_type(plugin_spec.get("type"))

    raw_content = plugin_spec.get("content")
    source = plugin_spec
    if raw_content is not None:
        if not isinstance(raw_content, dict):
            raise ValueError("slide.content must be an object.")
        _require_only_known_keys(
            raw_content,
            allowed=_ALLOWED_CONTENT_KEYS,
            field_name="slide.content",
        )
        source = raw_content

    title = _require_non_empty_text(source.get("title"), "slide title")
    body = _require_non_empty_text(source.get("body"), "slide body")
    body_format = _normalize_body_format(source.get("body_format"))
    media = _normalize_media(source=source, root=plugin_spec)

    content: dict[str, Any] = {
        "title": title,
        "body": body,
        "body_format": body_format,
    }
    if media is not None:
        content["media"] = media

    return {"schema_version": schema_version, "content": content}


def build_slide_frame_payload(plugin_spec: dict[str, Any]) -> dict[str, Any]:
    """Build VIEW_MODEL payload from raw or normalized slide plugin_spec."""
    validated = validate_slide_plugin_spec(plugin_spec)
    content = validated["content"]
    payload: dict[str, Any] = {
        "title": content["title"],
        "body": content["body"],
        "body_format": content["body_format"],
    }
    media = content.get("media")
    if isinstance(media, dict):
        payload["media"] = media
    return payload


def _require_only_known_keys(
    source: dict[str, Any],
    *,
    allowed: set[str],
    field_name: str,
) -> None:
    unknown = sorted(set(source) - allowed)
    if unknown:
        raise ValueError(f"{field_name} contains unknown key(s): {', '.join(unknown)}")


def _normalize_schema_version(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("slide schema_version is required.")
    normalized = value.strip().lower()
    if normalized not in {"v0", "v1"}:
        raise ValueError("slide schema_version must be 'v0' or 'v1'.")
    return normalized


def _validate_slide_type(value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, str) or value.strip().lower() != "slide":
        raise ValueError("slide type must be 'slide' when provided.")


def _require_non_empty_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value.strip()


def _normalize_body_format(value: Any) -> str:
    if value is None:
        return "text"
    if not isinstance(value, str):
        raise ValueError("slide body_format must be a string.")
    normalized = value.strip().lower()
    if normalized not in {"text", "markdown"}:
        raise ValueError("slide body_format must be 'text' or 'markdown'.")
    return normalized


def _normalize_media(
    *,
    source: dict[str, Any],
    root: dict[str, Any],
) -> dict[str, Any] | None:
    raw_media = source.get("media")
    if raw_media is None and source is not root:
        raw_media = root.get("media")

    if raw_media is not None:
        return _normalize_media_object(raw_media)

    image_url = _resolve_image_url(source=source, root=root)
    if image_url is None:
        return None
    return {"type": "image", "src": image_url}


def _normalize_media_object(raw_media: Any) -> dict[str, Any]:
    if not isinstance(raw_media, dict):
        raise ValueError("slide media must be an object.")
    _require_only_known_keys(
        raw_media,
        allowed=_ALLOWED_MEDIA_KEYS,
        field_name="slide media",
    )

    media_type = _require_non_empty_text(
        raw_media.get("type"), "slide media.type"
    ).lower()
    media_src = raw_media.get("src")

    if media_type == "none":
        if media_src is not None:
            raise ValueError("slide media.src must be null when media.type is 'none'.")
        return {"type": "none", "src": None}

    if media_type == "image":
        src = _require_non_empty_text(media_src, "slide media.src")
        return {"type": "image", "src": src}

    raise ValueError("slide media.type must be 'image' or 'none'.")


def _resolve_image_url(*, source: dict[str, Any], root: dict[str, Any]) -> str | None:
    value = source.get("image_url")
    if value is None and source is not root:
        value = root.get("image_url")
    if value is None:
        return None
    return _require_non_empty_text(value, "slide image_url")
