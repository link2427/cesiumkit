# Getting Started

## Installation

```bash
pip install cesiumkit
```

Requires Python 3.10+. No external binary dependencies.

## Your first globe

```python
import cesiumkit

viewer = cesiumkit.Viewer(title="Hello Globe")
viewer.add_entity(cesiumkit.Entity(
    name="New York",
    position=cesiumkit.Cartesian3.from_degrees(-74.006, 40.7128, 400),
    point=cesiumkit.PointGraphics(pixel_size=12, color=cesiumkit.Color.RED),
))
viewer.show()
```

This opens your default browser with an interactive 3D globe. Press `Ctrl+C` to stop the local server.

## Adding more entities

```python
viewer.add_entity(cesiumkit.Entity(
    name="Headquarters",
    position=cesiumkit.Cartesian3.from_degrees(-77.0369, 38.9072, 0),
    polygon=cesiumkit.PolygonGraphics(
        hierarchy=[
            cesiumkit.Cartesian3.from_degrees(-77.04, 38.91),
            cesiumkit.Cartesian3.from_degrees(-77.03, 38.91),
            cesiumkit.Cartesian3.from_degrees(-77.035, 38.905),
        ],
        material=cesiumkit.Color.CORNFLOWERBLUE.with_alpha(0.6),
        extruded_height=200,
    ),
))
```

## Cesium Ion token

Many features work without a token (using bundled offline imagery). For full functionality — Bing imagery, world terrain, 3D Tilesets — get a free token at [cesium.com/ion](https://cesium.com/ion/):

```python
cesiumkit.Ion.set_default_token("your-token-here")
```

## What's next?

- Browse the [Examples](examples.md) for common patterns
- Explore the [API Reference](api/viewer.md) for all available classes
