"""Scene-level Cesium particle systems."""

from __future__ import annotations

from typing import Any

from pydantic import Field, model_validator

from cesiumkit.base import CesiumBase


class ParticleSystem(CesiumBase):
    """A particle primitive for smoke, fire, weather, and similar effects.

    Cesium particle systems are scene primitives rather than entity graphics.
    Add one with :meth:`cesiumkit.Viewer.add_particle_system`.
    """

    image: str
    show: bool = True
    emission_rate: float = Field(default=5.0, ge=0, allow_inf_nan=False)
    lifetime: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    loop: bool = True
    speed: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    minimum_speed: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    maximum_speed: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    particle_life: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    minimum_particle_life: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    maximum_particle_life: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    start_scale: float = Field(default=1.0, ge=0, allow_inf_nan=False)
    end_scale: float = Field(default=1.0, ge=0, allow_inf_nan=False)
    start_color: Any = None
    end_color: Any = None
    image_size: Any = None
    minimum_image_size: Any = None
    maximum_image_size: Any = None
    size_in_meters: bool = False
    emitter: Any = None
    model_matrix: Any = None
    emitter_model_matrix: Any = None
    bursts: list[Any] | None = None

    @model_validator(mode="after")
    def _validate_ranges(self) -> ParticleSystem:
        pairs = (
            ("minimum_speed", self.minimum_speed, "maximum_speed", self.maximum_speed),
            (
                "minimum_particle_life",
                self.minimum_particle_life,
                "maximum_particle_life",
                self.maximum_particle_life,
            ),
        )
        for minimum_name, minimum, maximum_name, maximum in pairs:
            if minimum is not None and maximum is not None and maximum < minimum:
                raise ValueError(f"{maximum_name} must be greater than or equal to {minimum_name}")
        return self

    def _js_class_name(self) -> str:
        return "Cesium.ParticleSystem"
