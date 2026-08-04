"""The main Viewer class — primary entry point for cesiumkit."""

from __future__ import annotations

import base64
import binascii
import json
import logging
import math
import queue
import tempfile
import threading
import time
import webbrowser
from collections import deque
from collections.abc import Callable, Iterable
from io import BytesIO
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from cesiumkit._html import DEFAULT_CESIUM_VERSION, HtmlDocument
from cesiumkit._js_serializer import camelize, to_js_value
from cesiumkit._vendor import vendor_base_url, vendor_dir
from cesiumkit.czml import CzmlDocument
from cesiumkit.enums import SceneMode, ScreenSpaceEventType
from cesiumkit.events import EventHandler
from cesiumkit.utils import JsCode

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage

    from cesiumkit.coordinates import Cartesian2
    from cesiumkit.entities._base import Entity


class Viewer:
    """The main cesiumkit object. Corresponds to Cesium.Viewer.

    This is the primary entry point for building CesiumJS visualizations.
    Add entities, data sources, configure the camera, and render to HTML.
    """

    def __init__(
        self,
        # Ion
        ion_token: str | None = None,
        # Container
        container_id: str = "cesiumContainer",
        width: str = "100%",
        height: str = "100%",
        # Cesium version
        cesium_version: str | None = None,
        # Title
        title: str = "cesiumkit",
        # Viewer constructor options
        animation: bool | None = None,
        base_layer_picker: bool | None = None,
        fullscreen_button: bool | None = None,
        vr_button: bool | None = None,
        geocoder: bool | None = None,
        home_button: bool | None = None,
        info_box: bool | None = None,
        scene_mode_picker: bool | None = None,
        selection_indicator: bool | None = None,
        timeline: bool | None = None,
        navigation_help_button: bool | None = None,
        navigation_instructions_initially_visible: bool | None = None,
        request_render_mode: bool | None = None,
        maximum_render_time_change: float | None = None,
        resolution_scale: float | None = None,
        target_frame_rate: int | None = None,
        show_renderer_errors: bool | None = None,
        # Scene
        scene_mode: SceneMode | None = None,
        scene: Any = None,  # SceneConfig
        # Globe
        globe: Any = None,  # GlobeConfig
        # Terrain
        terrain_provider: Any = None,  # TerrainProvider
        # Imagery
        imagery_provider: Any = None,  # ImageryProvider
        # Clock
        clock: Any = None,  # ClockConfig
        should_animate: bool | None = None,
        # Camera
        camera: Any = None,  # Camera
    ) -> None:
        # Ion
        if ion_token is None:
            from cesiumkit.ion import Ion

            ion_token = Ion.get_default_token()
        self.ion_token = ion_token

        # Container/display
        self.container_id = container_id
        self.width = width
        self.height = height
        self.cesium_version = cesium_version or DEFAULT_CESIUM_VERSION
        self.title = title

        # Viewer options
        self._viewer_options: dict[str, Any] = {}
        opt_map = {
            "animation": animation,
            "base_layer_picker": base_layer_picker,
            "fullscreen_button": fullscreen_button,
            "vr_button": vr_button,
            "geocoder": geocoder,
            "home_button": home_button,
            "info_box": info_box,
            "scene_mode_picker": scene_mode_picker,
            "selection_indicator": selection_indicator,
            "timeline": timeline,
            "navigation_help_button": navigation_help_button,
            "navigation_instructions_initially_visible": navigation_instructions_initially_visible,
            "should_animate": should_animate,
            "request_render_mode": request_render_mode,
            "maximum_render_time_change": maximum_render_time_change,
            "target_frame_rate": target_frame_rate,
            "show_render_loop_errors": show_renderer_errors,
        }
        for key, val in opt_map.items():
            if val is not None:
                self._viewer_options[key] = val

        if scene_mode is not None:
            self._viewer_options["scene_mode"] = scene_mode
        if terrain_provider is not None:
            self._terrain_provider = terrain_provider
        else:
            self._terrain_provider = None
        if imagery_provider is not None:
            self._viewer_options["base_layer"] = imagery_provider

        if maximum_render_time_change is not None and (
            not math.isfinite(maximum_render_time_change) or maximum_render_time_change < 0
        ):
            raise ValueError("maximum_render_time_change must be finite and non-negative")
        if resolution_scale is not None and (not math.isfinite(resolution_scale) or resolution_scale <= 0):
            raise ValueError("resolution_scale must be a positive finite number")
        if target_frame_rate is not None and target_frame_rate <= 0:
            raise ValueError("target_frame_rate must be positive")
        self._resolution_scale = resolution_scale

        # Scene/Globe/Clock config (applied post-construction)
        self.scene_config = scene
        self.globe_config = globe
        self.clock_config = clock

        # Camera
        if camera is None:
            from cesiumkit.camera import Camera

            camera = Camera()
        self.camera = camera

        # Collections
        from cesiumkit.entities._base import EntityCollection

        self.entities = EntityCollection()
        self._data_sources: list[Any] = []
        self._tilesets: list[Any] = []
        self._primitives: list[Any] = []
        self._event_handlers: list[EventHandler] = []
        self._custom_scripts: list[str] = []

        # Runtime command queue (for live viewer control)
        self._command_seq = 0
        self._command_queue: deque[dict[str, Any]] = deque()
        self._runtime_results: dict[str, Any] = {}
        self._runtime_errors: dict[str, str] = {}
        self._runtime_condition = threading.Condition()
        self._server: Any = None
        self._click_callbacks: list[Callable[[str | None], None]] = []
        self._click_events: queue.Queue[str | None] = queue.Queue()
        self._click_bridge_registered = False

    # --- Entity convenience methods ---

    def add_entity(self, entity: Any = None, **kwargs: Any) -> Any:
        """Add an entity. Can pass an Entity instance or keyword args."""
        return self.entities.add(entity, **kwargs)

    def remove_entity(self, entity: Any) -> bool:
        """Remove an entity from the viewer.

        Returns True if the entity was found and removed.
        """
        return self.entities.remove(entity)

    def remove_entity_by_id(self, entity_id: str) -> bool:
        """Remove an entity by its ID.

        Returns True if the entity was found and removed.
        """
        entity = self.entities.get_by_id(entity_id)
        if entity is not None:
            return self.entities.remove(entity)
        return False

    def clear_entities(self) -> None:
        """Remove all entities from the viewer."""
        self.entities.remove_all()

    def get_entity(self, entity_id: str) -> Any | None:
        """Get an entity by its ID, or None if not found."""
        return self.entities.get_by_id(entity_id)

    @property
    def entity_count(self) -> int:
        """Number of entities currently in the viewer."""
        return len(self.entities)

    def add_geodataframe(self, gdf: Any, **options: Any) -> list[Any]:
        """Add all features from a ``geopandas.GeoDataFrame`` to this Viewer.

        This is a one-line shortcut for the most common geospatial workflow:
        load a GeoDataFrame, drop it on the globe. The GeoDataFrame is
        auto-reprojected to WGS84 (EPSG:4326) if needed. All keyword arguments
        are forwarded to ``cesiumkit.gis.geodataframe_to_entities``.

        Returns the list of created entities so they can be further customized.
        """
        from cesiumkit.gis import geodataframe_to_entities

        entities = geodataframe_to_entities(gdf, **options)
        for e in entities:
            self.entities.add(e)
        return entities

    def add_dataframe(self, df: Any, lon_col: str, lat_col: str, **options: Any) -> list[Any]:
        """Add point entities from a plain ``pandas.DataFrame`` with lon/lat columns.

        Shortcut for ``cesiumkit.gis.dataframe_to_entities`` that also attaches
        each entity to the viewer. Returns the list of created entities.
        """
        from cesiumkit.gis import dataframe_to_entities

        entities = dataframe_to_entities(df, lon_col, lat_col, **options)
        for e in entities:
            self.entities.add(e)
        return entities

    # --- Data source methods ---

    def add_data_source(self, data_source: Any) -> Any:
        """Add a data source."""
        self._data_sources.append(data_source)
        return data_source

    def load_czml(self, url: str | None = None, data: list[dict] | None = None) -> Any:
        """Load CZML data."""
        from cesiumkit.datasources import CzmlDataSource

        ds = CzmlDataSource(url=url, data=data)
        self._data_sources.append(ds)
        return ds

    def load_geojson(self, url: str | None = None, data: dict | None = None, **kwargs: Any) -> Any:
        """Load GeoJSON data."""
        from cesiumkit.datasources import GeoJsonDataSource

        ds = GeoJsonDataSource(url=url, data=data, **kwargs)
        self._data_sources.append(ds)
        return ds

    def load_kml(self, url: str = "", **kwargs: Any) -> Any:
        """Load KML/KMZ data."""
        from cesiumkit.datasources import KmlDataSource

        ds = KmlDataSource(url=url, **kwargs)
        self._data_sources.append(ds)
        return ds

    # --- 3D Tiles ---

    def add_tileset(self, url: str | None = None, ion_asset_id: int | None = None, **kwargs: Any) -> Any:
        """Add a 3D Tiles tileset."""
        from cesiumkit.ion import Cesium3DTileset

        ts = Cesium3DTileset(url=url, ion_asset_id=ion_asset_id, **kwargs)
        self._tilesets.append(ts)
        return ts

    def add_primitive(self, primitive: Any) -> Any:
        """Add a scene primitive such as a particle system."""
        self._primitives.append(primitive)
        return primitive

    def add_particle_system(self, particle_system: Any = None, **kwargs: Any) -> Any:
        """Add a :class:`cesiumkit.ParticleSystem` scene primitive."""
        if particle_system is None:
            from cesiumkit.particle import ParticleSystem

            particle_system = ParticleSystem(**kwargs)
        elif kwargs:
            raise TypeError("keyword options cannot be combined with a particle_system instance")
        return self.add_primitive(particle_system)

    # --- Event handling ---

    def on(self, event_type: ScreenSpaceEventType, handler: JsCode | str) -> None:
        """Register a screen space event handler."""
        if isinstance(handler, str):
            handler = JsCode(handler)
        self._event_handlers.append(EventHandler(event_type=event_type, handler=handler))

    def on_click(self, callback: Callable[[str | None], None]) -> None:
        """Register a Python callback for left-click events on entities.

        The callback receives the public Cesium entity ID, or ``None`` when
        the click did not hit an entity. The bridge works when registered
        before or after :meth:`show` starts.
        """
        if not callable(callback):
            raise TypeError("callback must be callable")
        self._click_callbacks.append(callback)
        self._ensure_click_bridge()

    def _ensure_click_bridge(self) -> None:
        """Register the browser-side click handler exactly once."""
        if self._click_bridge_registered:
            return

        self._click_bridge_registered = True
        script = self._click_bridge_js()
        if self._server is None:
            self.add_script(script)
        else:
            self._send_command(script)

    def wait_for_click(self, timeout: float | None = 30.0) -> str | None:
        """Wait for the next left click and return its entity ID, if any.

        Raises :class:`TimeoutError` if no click arrives within ``timeout``.
        Pass ``None`` to wait indefinitely.
        """
        if timeout is not None and (not math.isfinite(timeout) or timeout < 0):
            raise ValueError("timeout must be a finite non-negative number or None")
        self._ensure_click_bridge()
        try:
            return self._click_events.get(timeout=timeout)
        except queue.Empty as exc:
            raise TimeoutError(f"No click received within {timeout:g}s") from exc

    @staticmethod
    def _click_bridge_js() -> str:
        return (
            "(() => {"
            "if (window.__cesiumkitClickHandler) window.__cesiumkitClickHandler.destroy();"
            "const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);"
            "window.__cesiumkitClickHandler = handler;"
            "handler.setInputAction(async (movement) => {"
            "const picked = viewer.scene.pick(movement.position);"
            "const entityId = picked && picked.id && picked.id.id != null ? String(picked.id.id) : null;"
            "try { await __cesiumkitPostEvent('click', entityId); }"
            "catch (error) { console.error('cesiumkit click event failed:', error); }"
            "}, Cesium.ScreenSpaceEventType.LEFT_CLICK);"
            "})();"
        )

    def _handle_runtime_event(self, event: str, result: Any) -> None:
        """Dispatch an event received from the browser bridge."""
        if event != "click":
            raise ValueError(f"Unsupported runtime event: {event}")
        if result is not None and not isinstance(result, str):
            raise TypeError("Click event result must be a string or null")

        self._click_events.put(result)
        for callback in tuple(self._click_callbacks):
            try:
                callback(result)
            except Exception:
                logger.exception("Unhandled exception in cesiumkit click callback")

    def add_script(self, js_code: str) -> None:
        """Add custom JavaScript code to be executed after viewer setup."""
        self._custom_scripts.append(js_code)

    # --- Camera convenience ---

    def fly_to(self, destination: Any, **kwargs: Any) -> None:
        """Fly the camera to a destination."""
        self.camera.fly_to(destination, **kwargs)

    def set_view(self, destination: Any, orientation: Any = None) -> None:
        """Set the camera view immediately."""
        self.camera.set_view(destination, orientation)

    def look_at(self, target: Any, offset: Any) -> None:
        """Point the camera at a target."""
        self.camera.look_at(target, offset)

    # --- Runtime clock control ---

    def _send_command(self, js: str) -> int:
        """Queue a JS command for the live viewer to execute."""
        with self._runtime_condition:
            self._command_seq += 1
            self._command_queue.append({"seq": self._command_seq, "js": js})
            self._runtime_condition.notify_all()
            return self._command_seq

    def _request_runtime_result(self, expression: str, *, timeout: float) -> Any:
        """Evaluate a JavaScript expression and wait for its JSON result."""
        if self._server is None:
            raise RuntimeError("The viewer must be running via show() before reading browser state")

        request_id = uuid4().hex
        request_id_js = json.dumps(request_id)
        self._send_command(
            "(async () => {"
            "try {"
            f"const value = ({expression});"
            f"await __cesiumkitPostResult({request_id_js}, value, null);"
            "} catch (error) {"
            f"await __cesiumkitPostResult({request_id_js}, null, String(error));"
            "}"
            "})();"
        )
        return self._wait_for_runtime_result(request_id, timeout=timeout)

    def _wait_for_runtime_result(self, request_id: str, *, timeout: float) -> Any:
        """Wait for a result posted by the browser runtime bridge."""
        with self._runtime_condition:
            ready = self._runtime_condition.wait_for(
                lambda: request_id in self._runtime_results or request_id in self._runtime_errors,
                timeout=timeout,
            )
            if not ready:
                raise TimeoutError(f"Browser response timed out after {timeout:g}s")
            if request_id in self._runtime_errors:
                message = self._runtime_errors.pop(request_id)
                raise RuntimeError(f"Browser command failed: {message}")
            return self._runtime_results.pop(request_id)

    def set_time(self, iso_string: str) -> None:
        """Jump the timeline to a specific ISO 8601 epoch and update the widget.

        Example: ``viewer.set_time(\"2024-03-15T03:00:00Z\")``
        """
        iso_js = json.dumps(iso_string)
        self._send_command(f"viewer.clock.currentTime = Cesium.JulianDate.fromIso8601({iso_js});")
        self._send_command("if (viewer.timeline) viewer.timeline.updateFromClock();")

    def animate(self, on: bool = True) -> None:
        """Start or stop clock playback.

        Example: ``viewer.animate(on=False)`` to pause.
        """
        val = "true" if on else "false"
        self._send_command(f"viewer.clock.shouldAnimate = {val};")

    def set_multiplier(self, multiplier: float) -> None:
        """Change the clock playback speed.

        Example: ``viewer.set_multiplier(3600)`` for 1 hour per second.
        """
        if not math.isfinite(multiplier):
            raise ValueError("multiplier must be finite")
        self._send_command(f"viewer.clock.multiplier = {multiplier};")

    def get_current_time(self, *, timeout: float = 10.0) -> str:
        """Return the live viewer clock as an ISO 8601 string."""
        result = self._request_runtime_result(
            "Cesium.JulianDate.toIso8601(viewer.clock.currentTime)",
            timeout=timeout,
        )
        if not isinstance(result, str):
            raise RuntimeError("Browser returned a non-string clock value")
        return result

    # --- Screenshot export ---

    def screenshot_base64(self, *, timeout: float = 10.0) -> str:
        """Return a PNG screenshot of the live viewer as base64 text."""
        result = self._request_runtime_result(
            "(() => {"
            "viewer.scene.requestRender();"
            "viewer.scene.render();"
            "return viewer.scene.canvas.toDataURL('image/png').split(',')[1];"
            "})()",
            timeout=timeout,
        )
        if not isinstance(result, str):
            raise RuntimeError("Browser returned an invalid screenshot payload")
        return result

    def _screenshot_bytes(self, *, timeout: float) -> bytes:
        """Decode a live screenshot and validate its base64 payload."""
        try:
            return base64.b64decode(self.screenshot_base64(timeout=timeout), validate=True)
        except (binascii.Error, ValueError) as exc:
            raise RuntimeError("Browser returned malformed screenshot data") from exc

    def screenshot(self, path: str | PathLike[str], *, timeout: float = 10.0) -> None:
        """Save a PNG screenshot of the live viewer."""
        Path(path).write_bytes(self._screenshot_bytes(timeout=timeout))

    def canvas_to_image(self, *, timeout: float = 10.0) -> PILImage:
        """Return a screenshot as a detached Pillow image.

        Install the optional ``images`` extra to use this method.
        """
        try:
            from PIL import Image
        except ImportError as exc:  # pragma: no cover - depends on optional installation
            raise ImportError("canvas_to_image() requires `pip install cesiumkit[images]`") from exc

        with Image.open(BytesIO(self._screenshot_bytes(timeout=timeout))) as image:
            return image.copy()

    # --- Entity picking and selection ---

    def select_entity(self, entity_id: str) -> None:
        """Select a viewer entity by ID."""
        entity_id_js = json.dumps(entity_id)
        self._send_command(
            f"const entity = viewer.entities.getById({entity_id_js});"
            "if (entity) { viewer.selectedEntity = entity; viewer.scene.requestRender(); }"
        )

    def deselect(self) -> None:
        """Clear the live viewer selection."""
        self._send_command("viewer.selectedEntity = undefined; viewer.scene.requestRender();")

    def _get_selected_entity_id(self, *, timeout: float = 10.0) -> str | None:
        """Return the selected Cesium entity ID."""
        result = self._request_runtime_result(
            "viewer.selectedEntity ? viewer.selectedEntity.id : null",
            timeout=timeout,
        )
        if result is not None and not isinstance(result, str):
            raise RuntimeError("Browser returned an invalid selected entity ID")
        return result

    @property
    def selected_entity(self) -> Entity | None:
        """Return the selected local entity, or ``None`` if it is not local."""
        entity_id = self._get_selected_entity_id()
        return self.entities.get_by_id(entity_id) if entity_id is not None else None

    @staticmethod
    def _screen_position_js(position: Cartesian2) -> str:
        """Serialize and validate a screen-space position."""
        if not math.isfinite(position.x) or not math.isfinite(position.y):
            raise ValueError("screen position coordinates must be finite")
        return f"new Cesium.Cartesian2({position.x}, {position.y})"

    def pick(self, position: Cartesian2, *, timeout: float = 10.0) -> Entity | None:
        """Return the local entity at a screen position."""
        position_js = self._screen_position_js(position)
        entity_id = self._request_runtime_result(
            "(() => {"
            f"const picked = viewer.scene.pick({position_js});"
            "return picked && picked.id ? picked.id.id : null;"
            "})()",
            timeout=timeout,
        )
        if entity_id is None:
            return None
        if not isinstance(entity_id, str):
            raise RuntimeError("Browser returned an invalid picked entity ID")
        return self.entities.get_by_id(entity_id)

    def drill_pick(self, position: Cartesian2, *, timeout: float = 10.0) -> list[Entity]:
        """Return all local entities at a screen position."""
        position_js = self._screen_position_js(position)
        entity_ids = self._request_runtime_result(
            "(() => {"
            f"const picked = viewer.scene.drillPick({position_js});"
            "return picked.map((item) => item && item.id ? item.id.id : null)"
            ".filter((id) => typeof id === 'string');"
            "})()",
            timeout=timeout,
        )
        if not isinstance(entity_ids, list) or not all(isinstance(item, str) for item in entity_ids):
            raise RuntimeError("Browser returned invalid drill-pick entity IDs")
        entities = [self.entities.get_by_id(entity_id) for entity_id in entity_ids]
        return [entity for entity in entities if entity is not None]

    # --- Runtime data source updates ---

    @staticmethod
    def _data_source_update_js(source: Any, cesium_class: str) -> str:
        """Build an async command that replaces the first matching data source."""
        source_js = json.dumps(source)
        return (
            "(async () => {"
            f"const replacement = await Cesium.{cesium_class}.load({source_js});"
            "const collection = viewer.dataSources;"
            "let existing;"
            "for (let index = 0; index < collection.length; index += 1) {"
            "const candidate = collection.get(index);"
            f"if (candidate instanceof Cesium.{cesium_class}) {{ existing = candidate; break; }}"
            "}"
            "if (existing) collection.remove(existing, true);"
            "await collection.add(replacement);"
            "viewer.scene.requestRender();"
            "})();"
        )

    def update_czml(self, source: str | list[dict[str, Any]]) -> None:
        """Replace the first live CZML data source from a URL or CZML packets."""
        self._send_command(self._data_source_update_js(source, "CzmlDataSource"))

    def update_geojson(self, source: str | dict[str, Any]) -> None:
        """Replace the first live GeoJSON data source from a URL or mapping."""
        self._send_command(self._data_source_update_js(source, "GeoJsonDataSource"))

    def poll_czml(self, url: str, *, interval: float = 5.0) -> str:
        """Refresh CZML from *url* in the browser at a fixed interval.

        Returns an identifier that can be passed to :meth:`stop_polling`.
        """
        if not math.isfinite(interval) or interval <= 0:
            raise ValueError("interval must be a positive finite number")

        poller_id = uuid4().hex
        poller_id_js = json.dumps(poller_id)
        url_js = json.dumps(url)
        interval_ms = interval * 1000
        self._send_command(
            "(async () => {"
            "window.__cesiumkitPollers ??= new Map();"
            f"const pollerId = {poller_id_js};"
            f"const source = {url_js};"
            "const refresh = async () => {"
            "const replacement = await Cesium.CzmlDataSource.load(source);"
            "const collection = viewer.dataSources;"
            "let existing;"
            "for (let index = 0; index < collection.length; index += 1) {"
            "const candidate = collection.get(index);"
            "if (candidate instanceof Cesium.CzmlDataSource) { existing = candidate; break; }"
            "}"
            "if (existing) collection.remove(existing, true);"
            "await collection.add(replacement);"
            "viewer.scene.requestRender();"
            "};"
            "await refresh();"
            f"const timer = setInterval(() => refresh().catch(console.error), {interval_ms});"
            "window.__cesiumkitPollers.set(pollerId, timer);"
            "})();"
        )
        return poller_id

    def stop_polling(self, poller_id: str) -> None:
        """Stop a browser-side data-source poller."""
        poller_id_js = json.dumps(poller_id)
        self._send_command(
            "if (window.__cesiumkitPollers) {"
            f"const timer = window.__cesiumkitPollers.get({poller_id_js});"
            "if (timer !== undefined) clearInterval(timer);"
            f"window.__cesiumkitPollers.delete({poller_id_js});"
            "}"
        )

    def stream_czml(
        self,
        packets: Iterable[list[dict[str, Any]]],
        *,
        interval: float = 1.0,
    ) -> threading.Thread:
        """Consume CZML packet batches in a daemon thread and queue live updates."""
        if not math.isfinite(interval) or interval <= 0:
            raise ValueError("interval must be a positive finite number")

        def stream() -> None:
            for batch in packets:
                self.update_czml(batch)
                time.sleep(interval)

        thread = threading.Thread(target=stream, name="cesiumkit-czml-stream", daemon=True)
        thread.start()
        return thread

    # --- Serialization helpers ---

    def _build_viewer_options_js(self) -> str:
        """Build the viewer constructor options as a JS object literal."""
        if not self._viewer_options:
            return "{}"

        parts: list[str] = []
        for key, value in self._viewer_options.items():
            # The imagery provider must be wrapped in an ImageryLayer and
            # passed as `baseLayer`; the old `imageryProvider` viewer option
            # was removed in Cesium 1.144.
            if key == "base_layer" and hasattr(value, "to_js"):
                parts.append(f"baseLayer: new Cesium.ImageryLayer({value.to_js()})")
                continue
            js_key = camelize(key)
            js_val = to_js_value(value)
            parts.append(f"{js_key}: {js_val}")

        return "{\n        " + ",\n        ".join(parts) + "\n    }"

    def _build_entity_js_list(self) -> list[str]:
        """Build JS expressions for all entities."""
        return [entity.to_js() for entity in self.entities]

    def _build_data_source_js_list(self) -> list[str]:
        """Build JS expressions for all data sources."""
        return [ds.to_js() for ds in self._data_sources]

    def _build_tileset_js_list(self) -> list[str]:
        """Build JS expressions for all tilesets."""
        return [ts.to_js() for ts in self._tilesets]

    def _build_primitive_js_list(self) -> list[str]:
        """Build JS expressions for synchronous scene primitives."""
        return [primitive.to_js() for primitive in self._primitives]

    def _build_camera_operations(self) -> list[str]:
        """Build JS statements for camera operations."""
        return self.camera.to_js_operations("viewer")

    def _build_event_handler_js(self) -> list[str]:
        """Build JS expressions for event handlers."""
        return [eh.to_js("viewer") for eh in self._event_handlers]

    def _build_scene_statements(self) -> list[str]:
        """Build JS statements for scene configuration."""
        statements: list[str] = []
        if self._resolution_scale is not None:
            statements.append(f"viewer.resolutionScale = {self._resolution_scale};")
        if self.scene_config and hasattr(self.scene_config, "to_js_statements"):
            statements.extend(self.scene_config.to_js_statements("viewer"))
        return statements

    def _build_globe_statements(self) -> list[str]:
        """Build JS statements for globe configuration."""
        if self.globe_config and hasattr(self.globe_config, "to_js_statements"):
            return self.globe_config.to_js_statements("viewer")
        return []

    def _build_clock_statements(self) -> list[str]:
        """Build JS statements for clock configuration."""
        if self.clock_config and hasattr(self.clock_config, "to_js_statements"):
            return self.clock_config.to_js_statements("viewer")
        return []

    def _build_terrain_statement(self) -> str | None:
        """Build the JS expression assigned to scene.terrainProvider."""
        if self._terrain_provider is None:
            return None
        return self._terrain_provider.to_js()

    # --- Output methods ---

    def _render_html(self, cesium_base_url: str | None = None) -> str:
        """Render the full HTML document, optionally from a local Cesium build.

        Args:
            cesium_base_url: URL prefix of the directory containing Cesium.js.
                None loads Cesium from the CDN at self.cesium_version.
        """
        doc = HtmlDocument(
            cesium_version=self.cesium_version,
            cesium_base_url=cesium_base_url,
            ion_token=self.ion_token,
            width=self.width,
            height=self.height,
            title=self.title,
            container_id=self.container_id,
        )
        return doc.render(
            viewer_options=self._build_viewer_options_js(),
            entities=self._build_entity_js_list(),
            data_sources=self._build_data_source_js_list(),
            tilesets=self._build_tileset_js_list(),
            primitives=self._build_primitive_js_list(),
            camera_operations=self._build_camera_operations(),
            event_handlers=self._build_event_handler_js(),
            scene_statements=self._build_scene_statements(),
            globe_statements=self._build_globe_statements(),
            clock_statements=self._build_clock_statements(),
            terrain_statement=self._build_terrain_statement(),
            custom_scripts=self._custom_scripts,
        )

    def to_html(self) -> str:
        """Render the complete standalone HTML document string."""
        return self._render_html()

    def save(self, path: str) -> None:
        """Save to an HTML file."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_html())

    def show(self, port: int = 0, open_browser: bool = True) -> None:
        """Launch a local HTTP server and open the visualization in a browser.

        Cesium requires HTTP (not file://) due to web worker CORS restrictions.
        The server runs until interrupted. Call ``show()`` from a background
        thread when other Python code needs to control the live viewer.

        Args:
            port: Port to serve on. 0 = auto-pick a free port.
            open_browser: Whether to automatically open the browser.
        """
        import os
        from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
        from urllib.parse import parse_qs, urlparse

        tmpdir = tempfile.mkdtemp(prefix="cesiumkit_")
        html_path = os.path.join(tmpdir, "index.html")
        cesium_base_url = vendor_base_url()
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(self._render_html(cesium_base_url=cesium_base_url))

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=tmpdir, **kwargs)

            def translate_path(self, path):
                # Serve the bundled Cesium build (if present) from the
                # installed package, without copying it into the temp dir.
                if cesium_base_url and path.startswith(cesium_base_url + "/"):
                    vendor = vendor_dir()
                    if vendor is None:
                        return os.path.join(tmpdir, path.lstrip("/"))
                    rel = path[len(cesium_base_url) :].lstrip("/")
                    target = os.path.abspath(os.path.join(str(vendor), rel))
                    if os.path.commonpath([os.path.abspath(str(vendor)), target]) != os.path.abspath(str(vendor)):
                        # Path traversal outside the vendor dir: 404.
                        return os.path.join(tmpdir, path.lstrip("/"))
                    return target
                return super().translate_path(path)

            def do_GET(self):
                if self.path.startswith("/__cesiumkit_cmd"):
                    self._handle_command_poll()
                    return
                super().do_GET()

            def do_POST(self):
                if self.path == "/__cesiumkit_result":
                    self._handle_runtime_result()
                    return
                self.send_error(405)

            def _handle_command_poll(self):
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                try:
                    client_seq = int(params.get("seq", [0])[0])
                except (TypeError, ValueError):
                    self.send_error(400, "Invalid command sequence")
                    return

                with self._viewer._runtime_condition:
                    while self._viewer._command_queue and self._viewer._command_queue[0]["seq"] <= client_seq:
                        self._viewer._command_queue.popleft()
                    cmd = self._viewer._command_queue[0] if self._viewer._command_queue else None

                body = json.dumps(cmd or {}).encode("utf-8")

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _handle_runtime_result(self):
                try:
                    content_length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    self.send_error(400, "Invalid content length")
                    return
                if content_length <= 0 or content_length > 100 * 1024 * 1024:
                    self.send_error(413, "Invalid result payload size")
                    return

                try:
                    data = json.loads(self.rfile.read(content_length))
                    if not isinstance(data, dict):
                        raise TypeError
                    if "event" in data:
                        event = data["event"]
                        if not isinstance(event, str):
                            raise TypeError
                        self._viewer._handle_runtime_event(event, data.get("result"))
                        self._send_json_success()
                        return
                    request_id = data["requestId"]
                    if not isinstance(request_id, str):
                        raise TypeError
                except (json.JSONDecodeError, KeyError, TypeError, ValueError):
                    self.send_error(400, "Invalid result payload")
                    return

                with self._viewer._runtime_condition:
                    if data.get("error") is not None:
                        self._viewer._runtime_errors[request_id] = str(data["error"])
                    else:
                        self._viewer._runtime_results[request_id] = data.get("result")
                    self._viewer._runtime_condition.notify_all()

                self._send_json_success()

            def _send_json_success(self):
                body = b'{"ok":true}'
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                pass  # Suppress request logs

        Handler._viewer = self  # Attach viewer for command queue access

        server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        self._server = server
        actual_port = server.server_address[1]
        url = f"http://127.0.0.1:{actual_port}/index.html"

        if open_browser:
            webbrowser.open(url)

        print(f"Serving at {url}")
        print("Press Ctrl+C to stop the server.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
        finally:
            server.server_close()
            self._server = None

    def show_in_browser(self) -> None:
        """Alias for show(). Opens visualization via local HTTP server."""
        self.show()

    def _repr_html_(self) -> str:
        """Jupyter notebook display (HTML iframe)."""
        doc = HtmlDocument(
            cesium_version=self.cesium_version,
            ion_token=self.ion_token,
            width=self.width,
            height=self.height,
            title=self.title,
            container_id=self.container_id,
        )
        full_html = self.to_html()
        return doc.render_jupyter(full_html, width=self.width, height="600px")

    # --- CZML export ---

    def to_czml(self) -> list[dict]:
        """Export all entities as CZML JSON."""
        czml_doc = CzmlDocument(name=self.title, clock=self.clock_config)
        for entity in self.entities:
            czml_doc.add_entity(entity)
        return czml_doc.to_list()

    def to_czml_string(self, indent: int = 2) -> str:
        """Export CZML as formatted JSON string."""
        return json.dumps(self.to_czml(), indent=indent)

    def save_czml(self, path: str) -> None:
        """Save CZML to a .czml file."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_czml_string())
