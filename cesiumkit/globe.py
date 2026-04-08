"""Globe configuration for CesiumJS viewer."""

from __future__ import annotations

from typing import Any

from cesiumkit._js_serializer import to_js_value
from cesiumkit.base import CesiumBase


class GlobeConfig(CesiumBase):
    """Configuration for the CesiumJS globe.

    Generates JS statements to configure globe properties after viewer creation.
    """

    show: bool | None = None
    enable_lighting: bool | None = None
    depth_test_against_terrain: bool | None = None
    base_color: Any = None
    show_ground_atmosphere: bool | None = None
    show_sky_atmosphere: bool | None = None

    def _js_class_name(self) -> str:
        return "globe"

    def to_js_statements(self, viewer_var: str = "viewer") -> list[str]:
        """Generate JS statements to configure the globe after viewer creation."""
        stmts: list[str] = []
        if self.show is not None:
            stmts.append(f"{viewer_var}.scene.globe.show = {str(self.show).lower()};")
        if self.enable_lighting is not None:
            stmts.append(f"{viewer_var}.scene.globe.enableLighting = {str(self.enable_lighting).lower()};")
        if self.depth_test_against_terrain is not None:
            stmts.append(
                f"{viewer_var}.scene.globe.depthTestAgainstTerrain = {str(self.depth_test_against_terrain).lower()};"
            )
        if self.base_color is not None:
            stmts.append(f"{viewer_var}.scene.globe.baseColor = {to_js_value(self.base_color)};")
        if self.show_ground_atmosphere is not None:
            stmts.append(f"{viewer_var}.scene.globe.showGroundAtmosphere = {str(self.show_ground_atmosphere).lower()};")
        return stmts
