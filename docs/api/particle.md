# Particle Systems

Scene primitives for smoke, fire, weather, and trails. Particles are added
to the viewer directly (not as entities).

```python
import cesiumkit

viewer = cesiumkit.Viewer()
viewer.add_particle_system(
    cesiumkit.ParticleSystem(
        image="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
        emission_rate=20,
        lifetime=1.0,
        speed=5.0,
        start_scale=1.0,
        end_scale=0.0,
    )
)
```

::: cesiumkit.particle
