"""Bounded XML helpers with DTD/entity rejection and namespace-aware lookup."""

from __future__ import annotations

from xml.etree import ElementTree as ET

from .errors import common


def parse_xml(data: bytes, maximum: int) -> ET.Element:
    if not data or len(data) > maximum:
        raise common("schemaViolation", "empty or oversized XML message")
    folded = data.upper()
    if b"<!DOCTYPE" in folded or b"<!ENTITY" in folded:
        raise common("schemaViolation", "DTD and entity declarations are prohibited")
    try:
        # Input is length-bounded above and DTD/entity declarations are rejected
        # before ElementTree sees the document.
        return ET.fromstring(data)  # noqa: S314
    except ET.ParseError as exc:
        raise common("schemaViolation", "malformed XML message") from exc


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def one(parent: ET.Element, name: str, *, required: bool = True) -> ET.Element | None:
    matches = [child for child in parent if local_name(child.tag) == name]
    if len(matches) > 1 or (required and not matches):
        raise common("schemaViolation", f"expected exactly one {name} element")
    return matches[0] if matches else None


def text(parent: ET.Element, name: str, *, required: bool = True) -> str | None:
    element = one(parent, name, required=required)
    if element is None:
        return None
    value = (element.text or "").strip()
    if required and not value:
        raise common("schemaViolation", f"{name} must not be empty")
    return value or None
