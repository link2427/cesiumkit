"""Unit tests for the release-time Cesium fetch script."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _fetch_script():
    path = Path(__file__).parents[1] / "scripts" / "fetch_cesium.py"
    spec = importlib.util.spec_from_file_location("fetch_cesium", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_cesium_checksum_is_pinned() -> None:
    fetch_cesium = _fetch_script()
    assert fetch_cesium.DEFAULT_VERSION == "1.144"
    assert fetch_cesium.resolve_checksum("1.144", None, True) == fetch_cesium.DEFAULT_SHA256


def test_custom_cesium_requires_checksum_or_explicit_opt_out() -> None:
    fetch_cesium = _fetch_script()
    with pytest.raises(ValueError, match="no pinned checksum"):
        fetch_cesium.resolve_checksum("1.145", None, True)
    assert fetch_cesium.resolve_checksum("1.145", None, False) is None


@pytest.mark.parametrize("checksum", ["not-a-digest", "a" * 63, "g" * 64])
def test_custom_checksum_must_be_sha256(checksum: str) -> None:
    fetch_cesium = _fetch_script()
    with pytest.raises(ValueError, match="64-character"):
        fetch_cesium.resolve_checksum("1.145", checksum, True)
