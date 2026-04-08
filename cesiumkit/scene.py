"""Scene configuration for CesiumJS viewer."""

from __future__ import annotations

from typing import Any

from cesiumkit._js_serializer import to_js_value
from cesiumkit.base import CesiumBase
from cesiumkit.enums import SceneMode


class SceneConfig(CesiumBase):
    """Configuration for the CesiumJS scene.

    Generates JS statements to configure scene properties after viewer creation.
    """

    mode: SceneMode | None = None
    sky_box: bool | None = None
    sky_atmosphere: bool | None = None
    sun: bool | None = None
    moon: bool | None = None
    fog_enabled: bool | None = None
    background_color: Any = None
    order_independent_translucency: bool | None = None

    def _js_class_name(self) -> str:
        return "scene"

    def to_js_statements(self, viewer_var: str = "viewer") -> list[str]:
        """Generate JS statements to configure the scene after viewer creation."""
        stmts: list[str] = []
        if self.mode is not None:
            stmts.append(f"{viewer_var}.scene.mode = {self.mode.to_js()};")
        if self.sky_box is not None:
            stmts.append(f"{viewer_var}.scene.skyBox.show = {str(self.sky_box).lower()};")
        if self.sky_atmosphere is not None:
            stmts.append(f"{viewer_var}.scene.skyAtmosphere.show = {str(self.sky_atmosphere).lower()};")
        if self.sun is not None:
            stmts.append(f"{viewer_var}.scene.sun.show = {str(self.sun).lower()};")
        if self.moon is not None:
            stmts.append(f"{viewer_var}.scene.moon.show = {str(self.moon).lower()};")
        if self.fog_enabled is not None:
            stmts.append(f"{viewer_var}.scene.fog.enabled = {str(self.fog_enabled).lower()};")
        if self.background_color is not None:
            stmts.append(f"{viewer_var}.scene.backgroundColor = {to_js_value(self.background_color)};")
        if self.order_independent_translucency is not None:
            stmts.append(
                f"{viewer_var}.scene.orderIndependentTranslucency = {str(self.order_independent_translucency).lower()};"
            )
        return stmts
