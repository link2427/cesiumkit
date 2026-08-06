# Color

Color with RGBA components (0.0 to 1.0), 148 named colors, and
`.with_alpha()` for transparency.

```python
import cesiumkit

point = cesiumkit.PointGraphics(
    color=cesiumkit.Color.from_css("#ff8800"),
    outline_color=cesiumkit.Color.RED.with_alpha(0.5),
)
```

::: cesiumkit.color
