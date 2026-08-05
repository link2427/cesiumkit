"""Scene and post-processing configuration for CesiumJS viewers."""

from __future__ import annotations

from typing import Any

from pydantic import Field

from cesiumkit._js_serializer import to_js_value
from cesiumkit.base import CesiumBase
from cesiumkit.coordinates import Cartesian3
from cesiumkit.enums import ClassificationType, SceneMode


class ClippingPlane(CesiumBase):
    """A single clipping plane, defined by a point and a normal.

    Everything on the side the normal points away from is clipped away.
    The position and normal are ECEF :class:`Cartesian3` values; for globe
    or tileset work you usually want a geodetic position, so build them
    with :class:`Cartesian3FromDegrees`.
    """

    position: Cartesian3
    normal: Cartesian3

    def _js_class_name(self) -> str:
        return "Cesium.ClippingPlane"

    def to_js(self) -> str:
        return f"new Cesium.ClippingPlane({self.position.to_js()}, {self.normal.to_js()})"


class ClippingPlaneCollection(CesiumBase):
    """A set of planes used to clip tilesets, models, or the globe.

    ``union`` controls how the planes combine: ``False`` (default) keeps
    the intersection of the kept regions, ``True`` keeps the union. Planes
    are all applied regardless; the flag only changes how they combine.
    """

    planes: list[ClippingPlane] = Field(min_length=1)
    enabled: bool = True
    union: bool = False

    def _js_class_name(self) -> str:
        return "Cesium.ClippingPlaneCollection"

    def to_js(self) -> str:
        planes = ", ".join(plane.to_js() for plane in self.planes)
        opts = [f"planes: [{planes}]"]
        if not self.enabled:
            opts.append("enabled: false")
        if self.union:
            opts.append("union: true")
        return f"new Cesium.ClippingPlaneCollection({{{', '.join(opts)}}})"


class ClassificationPrimitive(CesiumBase):
    """A filled polygon drawn by classifying terrain or 3D Tiles.

    Classification reuses the depth of the surface it sits on instead of
    rendering its own geometry, so the polygon drapes perfectly over
    hills and buildings. The polygon ring is ``positions`` (ECEF
    :class:`Cartesian3` values, usually from :class:`Cartesian3FromDegrees`)
    at a fixed ``height`` above the ellipsoid.
    """

    positions: list[Cartesian3] = Field(min_length=3)
    color: Any = None
    height: float = 0.0
    classification_type: ClassificationType = ClassificationType.BOTH
    show: bool = True

    def _js_class_name(self) -> str:
        return "Cesium.ClassificationPrimitive"

    def to_js(self) -> str:
        positions = ", ".join(pos.to_js() for pos in self.positions)
        color = self.color.to_js() if self.color is not None else "Cesium.Color.RED"
        geometry = (
            "new Cesium.GeometryInstance({\n"
            f"    geometry: new Cesium.PolygonGeometry.fromPositions({{\n"
            f"        positions: [{positions}],\n"
            f"        height: {self.height},\n"
            f"    }}),\n"
            f"    attributes: {{ color: Cesium.ColorGeometryInstanceAttribute.fromColor({color}) }},\n"
            "})"
        )
        opts = [
            f"geometryInstances: {geometry}",
            f"classificationType: Cesium.ClassificationType.{self.classification_type.value}",
        ]
        if not self.show:
            opts.append("show: false")
        inner = ",\n    ".join(opts)
        return f"new Cesium.ClassificationPrimitive({{\n    {inner}\n}})"


class BloomConfig(CesiumBase):
    """Bloom glow configuration."""

    enabled: bool = True
    contrast: float = Field(default=128.0, ge=-255, le=255, allow_inf_nan=False)
    brightness: float = Field(default=-0.3, allow_inf_nan=False)
    delta: float = Field(default=1.0, gt=0, allow_inf_nan=False)
    sigma: float = Field(default=2.0, gt=0, allow_inf_nan=False)
    step_size: float = Field(default=5.0, gt=0, allow_inf_nan=False)

    def _js_class_name(self) -> str:
        return "BloomConfig"

    def to_js_statements(self, stages_var: str) -> list[str]:
        """Generate statements for Cesium's built-in bloom stage."""
        stage = f"{stages_var}.bloom"
        statements = [f"{stage}.enabled = {str(self.enabled).lower()};"]
        if self.enabled:
            uniforms = f"{stage}.uniforms"
            statements.extend(
                [
                    f"{uniforms}.contrast = {self.contrast};",
                    f"{uniforms}.brightness = {self.brightness};",
                    f"{uniforms}.delta = {self.delta};",
                    f"{uniforms}.sigma = {self.sigma};",
                    f"{uniforms}.stepSize = {self.step_size};",
                ]
            )
        return statements


class FXAAConfig(CesiumBase):
    """Fast approximate anti-aliasing configuration."""

    enabled: bool = True

    def _js_class_name(self) -> str:
        return "FXAAConfig"

    def to_js_statements(self, stages_var: str) -> list[str]:
        """Generate the FXAA enablement statement."""
        return [f"{stages_var}.fxaa.enabled = {str(self.enabled).lower()};"]


class AmbientOcclusionConfig(CesiumBase):
    """Screen-space ambient occlusion configuration."""

    enabled: bool = True
    intensity: float = Field(default=1.0, ge=0, allow_inf_nan=False)
    bias: float = Field(default=0.1, ge=0, allow_inf_nan=False)
    length_cap: float = Field(default=0.5, ge=0, allow_inf_nan=False)
    step_size: float = Field(default=1.0, gt=0, allow_inf_nan=False)
    frustum_length: float = Field(default=200.0, gt=0, allow_inf_nan=False)

    def _js_class_name(self) -> str:
        return "AmbientOcclusionConfig"

    def to_js_statements(self, stages_var: str) -> list[str]:
        """Generate statements for Cesium's ambient-occlusion stage."""
        stage = f"{stages_var}.ambientOcclusion"
        statements = [f"{stage}.enabled = {str(self.enabled).lower()};"]
        if self.enabled:
            uniforms = f"{stage}.uniforms"
            statements.extend(
                [
                    f"{uniforms}.intensity = {self.intensity};",
                    f"{uniforms}.bias = {self.bias};",
                    f"{uniforms}.lengthCap = {self.length_cap};",
                    f"{uniforms}.stepSize = {self.step_size};",
                    f"{uniforms}.frustumLength = {self.frustum_length};",
                ]
            )
        return statements


class PostProcessConfig(CesiumBase):
    """Built-in post-processing effects for a CesiumJS scene."""

    bloom: BloomConfig | None = None
    fxaa: FXAAConfig | None = None
    ambient_occlusion: AmbientOcclusionConfig | None = None

    def _js_class_name(self) -> str:
        return "PostProcessConfig"

    def to_js_statements(self, viewer_var: str = "viewer") -> list[str]:
        """Generate statements for every explicitly configured effect."""
        stages = f"{viewer_var}.scene.postProcessStages"
        statements: list[str] = []
        for config in (self.bloom, self.fxaa, self.ambient_occlusion):
            if config is not None:
                statements.extend(config.to_js_statements(stages))
        return statements


class SceneConfig(CesiumBase):
    """Configuration applied to a CesiumJS scene after viewer creation."""

    mode: SceneMode | None = None
    sky_box: bool | None = None
    sky_atmosphere: bool | None = None
    sun: bool | None = None
    moon: bool | None = None
    fog_enabled: bool | None = None
    background_color: Any = None
    order_independent_translucency: bool | None = None
    request_render_mode: bool | None = None
    maximum_render_time_change: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    post_process: PostProcessConfig | None = None

    def _js_class_name(self) -> str:
        return "scene"

    def to_js_statements(self, viewer_var: str = "viewer") -> list[str]:
        """Generate JavaScript statements for the configured scene values."""
        statements: list[str] = []
        if self.mode is not None:
            statements.append(f"{viewer_var}.scene.mode = {self.mode.to_js()};")
        if self.sky_box is not None:
            statements.append(f"{viewer_var}.scene.skyBox.show = {str(self.sky_box).lower()};")
        if self.sky_atmosphere is not None:
            statements.append(f"{viewer_var}.scene.skyAtmosphere.show = {str(self.sky_atmosphere).lower()};")
        if self.sun is not None:
            statements.append(f"{viewer_var}.scene.sun.show = {str(self.sun).lower()};")
        if self.moon is not None:
            statements.append(f"{viewer_var}.scene.moon.show = {str(self.moon).lower()};")
        if self.fog_enabled is not None:
            statements.append(f"{viewer_var}.scene.fog.enabled = {str(self.fog_enabled).lower()};")
        if self.background_color is not None:
            statements.append(f"{viewer_var}.scene.backgroundColor = {to_js_value(self.background_color)};")
        if self.order_independent_translucency is not None:
            value = str(self.order_independent_translucency).lower()
            statements.append(f"{viewer_var}.scene.orderIndependentTranslucency = {value};")
        if self.request_render_mode is not None:
            statements.append(f"{viewer_var}.scene.requestRenderMode = {str(self.request_render_mode).lower()};")
        if self.maximum_render_time_change is not None:
            statements.append(f"{viewer_var}.scene.maximumRenderTimeChange = {self.maximum_render_time_change};")
        if self.post_process is not None:
            statements.extend(self.post_process.to_js_statements(viewer_var))
        return statements


__all__ = [
    "AmbientOcclusionConfig",
    "BloomConfig",
    "ClassificationPrimitive",
    "ClippingPlane",
    "ClippingPlaneCollection",
    "FXAAConfig",
    "PostProcessConfig",
    "SceneConfig",
]
