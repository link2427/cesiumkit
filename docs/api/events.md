# Events

Declarative event handlers that emit CesiumJS screen-space event code.

```python
import cesiumkit

viewer = cesiumkit.Viewer()
viewer.on(
    cesiumkit.ScreenSpaceEventType.LEFT_CLICK,
    "console.log('clicked at ' + position)",
)
```

::: cesiumkit.events
