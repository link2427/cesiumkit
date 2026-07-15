"""Scene configuration for CesiumJS viewer."""

from __future__ import annotations

from typing import Any

from pydantic import Field

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
    request_render_mode: bool | None = None
    maximum_render_time_change: float | None = Field(default=None, ge=0, allow_inf_nan=False)

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
        if self.request_render_mode is not None:
            stmts.append(f"{viewer_var}.scene.requestRenderMode = {str(self.request_render_mode).lower()};")
        if self.maximum_render_time_change is not None:
            stmts.append(f"{viewer_var}.scene.maximumRenderTimeChange = {self.maximum_render_time_change};")
        return stmts


class PostProcessConfig(CesiumBase):
    """Post-processing effects for the CesiumJS scene.

    Controls bloom (glow), FXAA (anti-aliasing), and ambient occlusion.
    """

    bloom: BloomConfig | None = None
    fxaa: FXAAConfig | None = None
    ambient_occlusion: AmbientOcclusionConfig | None = None

    def _js_class_name(self) -> str:
        return "PostProcess"

    def to_js_statements(self, viewer_var: str = "viewer") -> list[str]:
        stmts: list[str] = []
        pp = f"{viewer_var}.scene.postProcessStages"
        if self.bloom is not None:
            stmts.extend(self.bloom._stmts(pp))
        if self.fxaa is not None:
            stmts.extend(self.fxaa._stmts(pp))
        if self.ambient_occlusion is not None:
            stmts.extend(self.ambient_occlusion._stmts(pp))
        return stmts


class BloomConfig:
    """Bloom (glow) post-processing effect configuration."""

    def __init__(
        self,
        enabled: bool = True,
        contrast: float = 128.0,
        brightness: float = -0.3,
        delta: float = 1.0,
        sigma: float = 2.0,
        step_size: float = 5.0,
    ) -> None:
        self.enabled = enabled
        self.contrast = contrast
        self.brightness = brightness
        self.delta = delta
        self.sigma = sigma
        self.step_size = step_size

    def _stmts(self, pp_var: str) -> list[str]:
        stmts = [f"{pp_var}.bloom.enabled = {str(self.enabled).lower()};"]
        if self.enabled:
            stmts.append(f"{pp_var}.bloom.contrast = {self.contrast};")
            stmts.append(f"{pp_var}.bloom.brightness = {self.brightness};")
            stmts.append(f"{pp_var}.bloom.delta = {self.delta};")
            stmts.append(f"{pp_var}.bloom.sigma = {self.sigma};")
            stmts.append(f"{pp_var}.bloom.stepSize = {self.step_size};")
        return stmts


class FXAAConfig:
    """Fast approximate anti-aliasing configuration."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled

    def _stmts(self, pp_var: str) -> list[str]:
        return [f"{pp_var}.fxaa.enabled = {str(self.enabled).lower()};"]


class AmbientOcclusionConfig:
    """Screen-space ambient occlusion configuration."""

    def __init__(
        self,
        enabled: bool = True,
        intensity: float = 1.0,
        bias: float = 0.1,
        length_cap: float = 0.5,
        step_size: float = 1.0,
        frustum_length: float = 200.0,
    ) -> None:
        self.enabled = enabled
        self.intensity = intensity
        self.bias = bias
        self.length_cap = length_cap
        self.step_size = step_size
        self.frustum_length = frustum_length

    def _stmts(self, pp_var: str) -> list[str]:
        stmts = [f"{pp_var}.ambientOcclusion.enabled = {str(self.enabled).lower()};"]
        if self.enabled:
            stmts.append(f"{pp_var}.ambientOcclusion.intensity = {self.intensity};")
            stmts.append(f"{pp_var}.ambientOcclusion.bias = {self.bias};")
            stmts.append(f"{pp_var}.ambientOcclusion.lengthCap = {self.length_cap};")
            stmts.append(f"{pp_var}.ambientOcclusion.stepSize = {self.step_size};")
            stmts.append(f"{pp_var}.ambientOcclusion.frustumLength = {self.frustum_length};")
        return stmts
