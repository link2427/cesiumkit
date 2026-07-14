"""Particle system graphics for cesiumkit."""

from __future__ import annotations

from typing import Any

from cesiumkit.entities._base import EntityGraphics


class ParticleSystemGraphics(EntityGraphics):
    """A particle system for smoke, fire, explosions, and weather effects."""

    image: str | None = None  # URL of particle image
    emission_rate: float | None = None
    lifetime: float | None = None
    speed: float | None = None
    start_scale: float | None = None
    end_scale: float | None = None
    start_color: Any = None
    end_color: Any = None
    minimum_speed: float | None = None
    maximum_speed: float | None = None
    minimum_particle_size: float | None = None
    maximum_particle_size: float | None = None
    particle_life: float | None = None
    emitter: Any = None  # Cartesian3
    model_matrix: Any = None  # Matrix4

    def _graphics_key(self) -> str:
        return "particleSystem"
