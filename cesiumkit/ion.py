"""Cesium Ion token management and asset loading."""

from __future__ import annotations

import os
from typing import Any

from cesiumkit.base import CesiumBase


class Ion:
    """Manages Cesium Ion token and asset loading."""

    _default_token: str | None = None

    @classmethod
    def set_default_token(cls, token: str) -> None:
        """Set the default Ion access token."""
        cls._default_token = token

    @classmethod
    def get_default_token(cls) -> str | None:
        """Get the default Ion token, falling back to CESIUM_ION_TOKEN env var."""
        return cls._default_token or os.environ.get("CESIUM_ION_TOKEN")


class IonResource(CesiumBase):
    """Reference to a Cesium Ion asset resource."""

    asset_id: int
    access_token: str | None = None

    def _js_class_name(self) -> str:
        return "Cesium.IonResource"

    def to_js(self) -> str:
        return f"Cesium.IonResource.fromAssetId({self.asset_id})"


class Cesium3DTileset(CesiumBase):
    """A 3D Tiles tileset added as a scene primitive."""

    url: str | None = None
    ion_asset_id: int | None = None
    show: bool = True
    maximum_screen_space_error: float = 16.0
    maximum_memory_usage: int | None = None
    shadows: Any = None

    def _js_class_name(self) -> str:
        return "Cesium.Cesium3DTileset"

    def to_js(self) -> str:
        if self.ion_asset_id:
            return f"Cesium.Cesium3DTileset.fromIonAssetId({self.ion_asset_id})"
        if self.url:
            return f'Cesium.Cesium3DTileset.fromUrl("{self.url}")'
        raise ValueError("Either url or ion_asset_id must be provided")
