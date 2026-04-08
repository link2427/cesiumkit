"""Utility classes and functions for cesiumkit."""

from __future__ import annotations

from uuid import uuid4


class JsCode:
    """Wraps raw JavaScript code that should be inserted verbatim, not quoted."""

    def __init__(self, js_code: str) -> None:
        self.js_code = js_code

    def __repr__(self) -> str:
        return f"JsCode({self.js_code!r})"

    def __str__(self) -> str:
        return self.js_code

    def __eq__(self, other: object) -> bool:
        if isinstance(other, JsCode):
            return self.js_code == other.js_code
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self.js_code)


def generate_id() -> str:
    """Generate a unique identifier."""
    return str(uuid4())
