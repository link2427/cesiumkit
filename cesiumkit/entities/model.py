"""Model (3D) graphics for cesiumkit."""

from __future__ import annotations

from typing import Any

from cesiumkit.entities._base import EntityGraphics


class ModelGraphics(EntityGraphics):
    """A 3D model (glTF/glb) attached to an entity."""

    uri: str | None = None
    scale: float | None = None
    minimum_pixel_size: float | None = None
    maximum_scale: float | None = None
    run_animations: bool | None = None
    clamp_animations: bool | None = None
    shadows: Any = None
    height_reference: Any = None
    silhouette_color: Any = None
    silhouette_size: float | None = None
    color: Any = None
    color_blend_mode: Any = None
    color_blend_amount: float | None = None
    distance_display_condition: Any = None

    def _graphics_key(self) -> str:
        return "model"
