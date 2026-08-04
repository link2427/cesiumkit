"""Locating the bundled Cesium build.

scripts/fetch_cesium.py downloads the official Cesium release and extracts
its Build/Cesium directory into ``cesiumkit/vendor/cesium/``. The directory
is gitignored and only present when the fetch script has been run (or the
wheel was built with it included); everything here degrades gracefully to
CDN loading when it is absent.
"""

from __future__ import annotations

from pathlib import Path

from cesiumkit._html import DEFAULT_CESIUM_VERSION

_VENDOR_ROOT = Path(__file__).resolve().parent / "vendor" / "cesium"
_VERSION_MARKER = ".cesiumkit-version"


def vendor_dir() -> Path | None:
    """Return the bundled Cesium build directory, or None if unavailable."""
    if not (_VENDOR_ROOT / "Cesium.js").is_file():
        return None
    marker = _VENDOR_ROOT / _VERSION_MARKER
    if marker.is_file() and marker.read_text(encoding="utf-8").strip() != DEFAULT_CESIUM_VERSION:
        # Stale build for a different Cesium version than we generate for.
        return None
    return _VENDOR_ROOT


def vendor_base_url() -> str | None:
    """URL prefix (relative to the served root) for the vendor build, if any."""
    return "/vendor/cesium" if vendor_dir() is not None else None
