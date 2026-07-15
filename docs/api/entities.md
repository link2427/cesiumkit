# Entities

Entities and their graphics types.

::: cesiumkit.entities._base

::: cesiumkit.entities.billboard

::: cesiumkit.entities.box

::: cesiumkit.entities.corridor

::: cesiumkit.entities.cylinder

::: cesiumkit.entities.ellipse

::: cesiumkit.entities.ellipsoid

::: cesiumkit.entities.label

::: cesiumkit.entities.model

::: cesiumkit.entities.path

::: cesiumkit.entities.point

::: cesiumkit.entities.polygon

::: cesiumkit.entities.polyline

::: cesiumkit.entities.polyline_volume

::: cesiumkit.entities.rectangle

::: cesiumkit.entities.wall

::: cesiumkit.entities.tileset

::: cesiumkit.entities.plane

::: cesiumkit.particle

## Planes

`PlaneGraphics` is a normal entity graphic. Construct its geometric plane from
a normal vector and signed distance:

```python
plane = cesiumkit.Plane(normal=cesiumkit.Cartesian3(x=0, y=0, z=1), distance=0)
entity = cesiumkit.Entity(
    plane=cesiumkit.PlaneGraphics(
        plane=plane,
        dimensions=cesiumkit.Cartesian2(x=100, y=100),
        material=cesiumkit.Color.RED,
    )
)
```

## Particle systems

Cesium particle systems are scene primitives, not entity graphics:

```python
viewer.add_particle_system(
    image="smoke.png",
    emission_rate=10,
    particle_life=2,
    start_scale=1,
    end_scale=0.1,
)
```
