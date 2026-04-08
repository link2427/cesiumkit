"""3D Tileset graphics for cesiumkit."""

from __future__ import annotations

from typing import Any

from cesiumkit.entities._base import EntityGraphics


class Cesium3DTilesetGraphics(EntityGraphics):
    """A 3D Tiles tileset attached to an entity."""

    uri: str | None = None
    maximum_screen_space_error: float | None = None

    def _graphics_key(self) -> str:
        return "tileset"
