"""The main Viewer class — primary entry point for cesiumkit."""

from __future__ import annotations

import base64
import json
import logging
import math
import queue
import secrets
import socket
import struct
import tempfile
import threading
import time
import warnings
import webbrowser
import zlib
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
from cesiumkit.camera import Camera
from cesiumkit.clock import ClockConfig
from cesiumkit.clustering import EntityClusterConfig
from cesiumkit.czml import CzmlDocument
from cesiumkit.enums import ClassificationType, SceneMode, ScreenSpaceEventType, ShadowMode
from cesiumkit.events import EventHandler
from cesiumkit.globe import GlobeConfig
from cesiumkit.imagery import ImageryProvider
from cesiumkit.scene import SceneConfig
from cesiumkit.terrain import TerrainProvider
from cesiumkit.utils import JsCode

logger = logging.getLogger(__name__)

_MAX_COMMAND_LOG = 1_024
_MAX_COMMAND_BYTES = 1_048_576
_MAX_COMMAND_LOG_BYTES = 8 * 1_048_576
_MAX_PENDING_RUNTIME_RESULTS = 128
_MAX_RUNTIME_EVENT_QUEUE = 256
_MAX_RUNTIME_REQUEST_BYTES = 1_048_576
_MAX_PENDING_SCREENSHOTS = 1
_MAX_SCREENSHOT_BYTES = 32 * 1_048_576
_MAX_SCREENSHOT_PIXELS = 64 * 1_048_576
_MAX_RUNTIME_HTTP_THREADS = 32
_RUNTIME_CONNECTION_TIMEOUT_SECONDS = 10.0
_RUNTIME_OVERLOAD_DRAIN_SECONDS = 0.05
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage

    from cesiumkit.color import Color
    from cesiumkit.coordinates import Cartesian2, Cartesian3
    from cesiumkit.entities._base import Entity
    from cesiumkit.raster import RasterSource
    from cesiumkit.scene import ClassificationPrimitive


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
        scene3d_only: bool | None = None,
        shadows: ShadowMode | None = None,
        terrain_shadows: ShadowMode | None = None,
        scene: SceneConfig | None = None,
        # Globe
        globe: GlobeConfig | None = None,
        # Terrain
        terrain_provider: TerrainProvider | None = None,
        # Imagery
        imagery_provider: ImageryProvider | None = None,
        # Clock
        clock: ClockConfig | None = None,
        should_animate: bool | None = None,
        # Camera
        camera: Camera | None = None,
        # Clustering
        clustering: EntityClusterConfig | None = None,
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
            "shadows": shadows,
            "terrain_shadows": terrain_shadows,
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

        # camelize() would emit `scene3dOnly`, but Cesium's option keeps the
        # capital D, so this one gets set under its exact JS name.
        if scene3d_only is not None:
            self._viewer_options["scene3DOnly"] = scene3d_only

        if maximum_render_time_change is not None:
            if isinstance(maximum_render_time_change, bool) or not isinstance(maximum_render_time_change, (int, float)):
                raise TypeError("maximum_render_time_change must be a finite number")
            if not math.isfinite(maximum_render_time_change) or maximum_render_time_change < 0:
                raise ValueError("maximum_render_time_change must be finite and non-negative")
        if resolution_scale is not None:
            if isinstance(resolution_scale, bool) or not isinstance(resolution_scale, (int, float)):
                raise TypeError("resolution_scale must be a finite number")
            if not math.isfinite(resolution_scale) or resolution_scale <= 0:
                raise ValueError("resolution_scale must be a positive finite number")
        if target_frame_rate is not None:
            if type(target_frame_rate) is not int:
                raise TypeError("target_frame_rate must be an int")
            if target_frame_rate <= 0:
                raise ValueError("target_frame_rate must be positive")
        self._resolution_scale = resolution_scale

        # Scene/Globe/Clock config (applied post-construction)
        self.scene_config = scene
        self.globe_config = globe
        self.clock_config = clock
        self._clustering = clustering

        # Camera
        if camera is None:
            camera = Camera()
        self.camera = camera

        # Collections
        from cesiumkit.entities._base import EntityCollection

        self.entities = EntityCollection()
        self._data_sources: list[Any] = []
        self._tilesets: list[Any] = []
        self._raster_sources: dict[str, Any] = {}
        self._primitives: list[Any] = []
        self._imagery_layers: list[dict[str, Any]] = []
        self._event_handlers: list[EventHandler] = []
        self._custom_scripts: list[str] = []

        # Runtime command queue (for live viewer control)
        self._command_seq = 0
        self._command_queue: deque[dict[str, Any]] = deque()
        self._command_sizes: deque[int] = deque()
        self._command_log_bytes = 0
        self._runtime_results: dict[str, Any] = {}
        self._runtime_errors: dict[str, str] = {}
        self._pending_runtime_ids: set[str] = set()
        self._pending_screenshot_ids: set[str] = set()
        self._screenshot_upload_ids: set[str] = set()
        self._runtime_condition = threading.Condition()
        self._server: Any = None
        self._server_tempdir: tempfile.TemporaryDirectory[str] | None = None
        self._session_token: str | None = None
        self._lifecycle_lock = threading.RLock()
        self._runtime_finalization_done = threading.Event()
        self._runtime_finalization_owner: int | None = None
        self._closed = False
        self._click_callbacks: list[Callable[[str | None], None]] = []
        self._click_events: queue.Queue[str | None] = queue.Queue(maxsize=_MAX_RUNTIME_EVENT_QUEUE)
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

    def load_kml(self, url: str, **kwargs: Any) -> Any:
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

    def add_classification(
        self,
        positions: list[Cartesian3],
        *,
        color: Color | str | None = None,
        height: float = 0.0,
        extruded_height: float = 100_000.0,
        classification_type: ClassificationType | None = None,
    ) -> ClassificationPrimitive:
        """Draw a filled polygon onto terrain or 3D Tiles.

        The polygon reuses the depth of the surface it drapes over, so it
        follows hills and buildings instead of floating. ``positions`` are
        ECEF points (use ``Cartesian3FromDegrees``). ``height`` and
        ``extruded_height`` bound the required classification volume;
        ``classification_type`` is one of ``ClassificationType.TERRAIN``,
        ``CESIUM_3D_TILE``, or ``BOTH`` (the default).
        """
        from cesiumkit.scene import ClassificationPrimitive

        options: dict[str, Any] = {
            "positions": list(positions),
            "height": height,
            "extruded_height": extruded_height,
        }
        if color is not None:
            options["color"] = color
        if classification_type is not None:
            options["classification_type"] = classification_type
        return self.add_primitive(ClassificationPrimitive(**options))

    def add_raster(
        self,
        source: Any,
        *,
        name: str | None = None,
        opacity: float = 1.0,
        maximum_level: int | None = None,
    ) -> RasterSource:
        """Display a local raster (GeoTIFF/COG path or xarray DataArray).

        Requires ``[raster]`` extras (rio-tiler/rasterio/xarray). The raster
        is served as Web Mercator tiles by the ``show()`` server. The first
        raster becomes the viewer's base imagery layer; later rasters stack
        on top of it, each with its own ``opacity`` (0.0 to 1.0). Overlays
        keep the order they were added in, WMTS and raster alike; the first
        raster is always the base. Needs a running server (not static HTML
        export). ``maximum_level`` must be a plain ``int`` (numpy integers
        are rejected).
        """
        from cesiumkit.raster import RasterSource

        self._validate_layer_options(opacity=opacity, maximum_level=maximum_level)
        raster = RasterSource(source, name=name)
        self._raster_sources[raster.id] = raster
        from cesiumkit.imagery import UrlTemplateImageryProvider

        provider_options: dict[str, Any] = {"url": f"/raster/{raster.id}/{{z}}/{{x}}/{{y}}.png"}
        if maximum_level is not None:
            provider_options["maximum_level"] = maximum_level
        provider = UrlTemplateImageryProvider(**provider_options)
        if not any(spec["kind"] == "raster" for spec in self._imagery_layers):
            if "base_layer" in self._viewer_options:
                warnings.warn(
                    "add_raster() replaces the imagery_provider set on the Viewer; the raster becomes the base layer",
                    UserWarning,
                    stacklevel=2,
                )
            self._viewer_options["base_layer"] = provider
        self._imagery_layers.append(
            {"kind": "raster", "id": raster.id, "opacity": opacity, "maximum_level": maximum_level}
        )
        return raster

    @staticmethod
    def _validate_layer_options(*, opacity: float, maximum_level: int | None) -> None:
        if isinstance(opacity, bool) or not isinstance(opacity, (int, float)) or not math.isfinite(opacity):
            raise TypeError("opacity must be a finite number")
        if not 0.0 <= opacity <= 1.0:
            raise ValueError("opacity must be between 0.0 and 1.0")
        if maximum_level is not None:
            if type(maximum_level) is not int:
                raise TypeError("maximum_level must be an int or None")
            if maximum_level < 0:
                raise ValueError("maximum_level must be non-negative")

    def add_wmts_layer(
        self,
        url: str,
        layer: str,
        *,
        style: str = "",
        tile_matrix_set: str = "default",
        format: str = "image/png",
        maximum_level: int | None = None,
        opacity: float = 1.0,
    ) -> None:
        """Stack a remote WMTS layer over the current imagery.

        ``layer``/``style``/``tile_matrix_set`` map to the WMTS
        capabilities for the service at ``url``. The layer is added on top
        of whatever imagery is already configured, with its own opacity.
        Overlays keep the order they were added in, raster and WMTS alike;
        the first raster is always the base. ``maximum_level`` must be a
        plain ``int`` (numpy integers are rejected).
        """
        self._validate_layer_options(opacity=opacity, maximum_level=maximum_level)
        self._imagery_layers.append(
            {
                "kind": "wmts",
                "url": url,
                "layer": layer,
                "style": style,
                "tile_matrix_set": tile_matrix_set,
                "format": format,
                "maximum_level": maximum_level,
                "opacity": opacity,
            }
        )

    def add_points(
        self,
        gdf: Any,
        *,
        aggregation: bool = True,
        colormap: list[str] | None = None,
        plot_width: int = 1024,
        plot_height: int = 512,
        **kwargs: Any,
    ) -> Any:
        """Add points from a GeoDataFrame, optionally aggregated via datashader.

        With ``aggregation=True`` (default) the points are rasterized with
        datashader (``[datashader]`` extras) into an imagery layer, which
        stays responsive for millions of points. ``colormap`` is a list of
        CSS colors for the shading ramp. Pass ``aggregation=False`` to fall
        back to per-point entities.
        """
        if not aggregation:
            return self.add_geodataframe(gdf, **kwargs)
        from cesiumkit.raster import aggregate_points_to_raster

        options = dict(kwargs.pop("aggregate_options", {}))
        if colormap is not None:
            options["colormap"] = colormap
        options.setdefault("plot_width", plot_width)
        options.setdefault("plot_height", plot_height)
        name = kwargs.pop("name", "points")
        opacity = kwargs.pop("opacity", 1.0)
        maximum_level = kwargs.pop("maximum_level", None)
        if kwargs:
            unexpected = ", ".join(sorted(kwargs))
            raise TypeError(f"unexpected aggregation options: {unexpected}")
        path = aggregate_points_to_raster(gdf, **options)
        try:
            raster = self.add_raster(path, name=name, opacity=opacity, maximum_level=maximum_level)
        except Exception:
            Path(path).unlink(missing_ok=True)
            raise
        raster._mark_owned_path()
        return raster

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
        if timeout is not None:
            if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
                raise TypeError("timeout must be a finite non-negative number or None")
            if not math.isfinite(timeout) or timeout < 0:
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

        try:
            self._click_events.put_nowait(result)
        except queue.Full:
            # Keep the most recent click without ever letting a browser
            # request block on an unattended Python consumer.
            try:
                self._click_events.get_nowait()
            except queue.Empty:  # pragma: no cover - another consumer won the race
                pass
            try:
                self._click_events.put_nowait(result)
            except queue.Full:  # pragma: no cover - another producer won the race
                pass
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

    def fly_to_entities(self, duration: float = 3.0) -> None:
        """Fly the camera to fit the extent of all entities."""
        self.camera.fly_to_entities(duration=duration)

    def fly_to_bounding_sphere(self, bounding_sphere: Any, duration: float = 3.0, **kwargs: Any) -> None:
        """Fly the camera to a bounding sphere."""
        self.camera.fly_to_bounding_sphere(bounding_sphere, duration=duration, **kwargs)

    def to_widget(self, *, height: str = "600px", cesium_version: str | None = None) -> Any:
        """Return a Jupyter widget for this viewer (requires ``[widget]`` extras)."""
        from cesiumkit.widget import CesiumKitWidget

        return CesiumKitWidget(self, height=height, cesium_version=cesium_version)

    # --- Runtime clock control ---

    def _send_command(self, js: str) -> int:
        """Queue a JS command for the live viewer to execute."""
        if not isinstance(js, str):
            raise TypeError("Runtime command must be a string")
        command_size = len(js.encode("utf-8"))
        if command_size > _MAX_COMMAND_BYTES:
            raise ValueError("Runtime command exceeds the 1 MiB size limit")
        with self._runtime_condition:
            if self._closed:
                raise RuntimeError("Viewer is closed")
            while self._command_queue and (
                len(self._command_queue) >= _MAX_COMMAND_LOG
                or self._command_log_bytes + command_size > _MAX_COMMAND_LOG_BYTES
            ):
                self._command_queue.popleft()
                self._command_log_bytes -= self._command_sizes.popleft()
            self._command_seq += 1
            self._command_queue.append({"seq": self._command_seq, "js": js})
            self._command_sizes.append(command_size)
            self._command_log_bytes += command_size
            self._runtime_condition.notify_all()
            return self._command_seq

    @staticmethod
    def _validate_runtime_timeout(timeout: float) -> None:
        """Require a finite, non-negative timeout for browser round trips."""
        if (
            not isinstance(timeout, (int, float))
            or isinstance(timeout, bool)
            or not math.isfinite(timeout)
            or timeout < 0
        ):
            raise ValueError("timeout must be a finite non-negative number")

    def _request_runtime_result(self, expression: str, *, timeout: float) -> Any:
        """Evaluate a JavaScript expression and wait for its JSON result."""
        self._validate_runtime_timeout(timeout)

        request_id = uuid4().hex
        request_id_js = to_js_value(request_id)
        with self._runtime_condition:
            if self._server is None or self._closed:
                raise RuntimeError("The viewer must be running via show() before reading browser state")
            if len(self._pending_runtime_ids) >= _MAX_PENDING_RUNTIME_RESULTS:
                raise RuntimeError("Too many pending browser requests")
            self._pending_runtime_ids.add(request_id)
        try:
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
        except Exception:
            with self._runtime_condition:
                self._pending_runtime_ids.discard(request_id)
                self._runtime_results.pop(request_id, None)
                self._runtime_errors.pop(request_id, None)
            raise

    def _wait_for_runtime_result(self, request_id: str, *, timeout: float) -> Any:
        """Wait for a result posted by the browser runtime bridge."""
        with self._runtime_condition:
            try:
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
            finally:
                self._pending_runtime_ids.discard(request_id)
                self._pending_screenshot_ids.discard(request_id)
                self._screenshot_upload_ids.discard(request_id)

    def set_time(self, iso_string: str) -> None:
        """Jump the timeline to a specific ISO 8601 epoch and update the widget.

        Example: ``viewer.set_time(\"2024-03-15T03:00:00Z\")``
        """
        if not isinstance(iso_string, str):
            raise TypeError("iso_string must be a string")
        if not iso_string.strip():
            raise ValueError("iso_string must not be empty")
        iso_js = to_js_value(iso_string)
        self._send_command(f"viewer.clock.currentTime = Cesium.JulianDate.fromIso8601({iso_js});")
        self._send_command("if (viewer.timeline) viewer.timeline.updateFromClock();")

    def animate(self, on: bool = True) -> None:
        """Start or stop clock playback.

        Example: ``viewer.animate(on=False)`` to pause.
        """
        if not isinstance(on, bool):
            raise TypeError("on must be a bool")
        val = "true" if on else "false"
        self._send_command(f"viewer.clock.shouldAnimate = {val};")

    def set_multiplier(self, multiplier: float) -> None:
        """Change the clock playback speed.

        Example: ``viewer.set_multiplier(3600)`` for 1 hour per second.
        """
        if isinstance(multiplier, bool) or not isinstance(multiplier, (int, float)):
            raise TypeError("multiplier must be a finite number")
        if not math.isfinite(multiplier):
            raise ValueError("multiplier must be finite")
        self._send_command(f"viewer.clock.multiplier = {multiplier!r};")

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
        return base64.b64encode(self._screenshot_bytes(timeout=timeout)).decode("ascii")

    def _screenshot_bytes(self, *, timeout: float) -> bytes:
        """Return a validated live screenshot through the binary runtime route."""
        self._validate_runtime_timeout(timeout)

        request_id = uuid4().hex
        request_id_js = to_js_value(request_id)
        with self._runtime_condition:
            if self._server is None or self._closed:
                raise RuntimeError("The viewer must be running via show() before taking a screenshot")
            if len(self._pending_runtime_ids) >= _MAX_PENDING_RUNTIME_RESULTS:
                raise RuntimeError("Too many pending browser requests")
            if len(self._pending_screenshot_ids) >= _MAX_PENDING_SCREENSHOTS:
                raise RuntimeError("A screenshot request is already pending")
            self._pending_runtime_ids.add(request_id)
            self._pending_screenshot_ids.add(request_id)
        try:
            self._send_command(
                "(async () => {"
                "try {"
                "viewer.scene.requestRender();"
                "viewer.scene.render();"
                "const blob = await new Promise((resolve, reject) => {"
                "viewer.scene.canvas.toBlob((value) => {"
                "if (value) resolve(value);"
                "else reject(new Error('Failed to encode PNG screenshot'));"
                "}, 'image/png');"
                "});"
                f"await __cesiumkitPostScreenshot({request_id_js}, blob);"
                "} catch (error) {"
                "try {"
                f"await __cesiumkitPostResult({request_id_js}, null, String(error));"
                "} catch (reportError) {"
                "console.error('cesiumkit screenshot failure could not be reported:', reportError);"
                "}"
                "}"
                "})();"
            )
            result = self._wait_for_runtime_result(request_id, timeout=timeout)
        except Exception:
            with self._runtime_condition:
                self._pending_runtime_ids.discard(request_id)
                self._pending_screenshot_ids.discard(request_id)
                self._screenshot_upload_ids.discard(request_id)
                self._runtime_results.pop(request_id, None)
                self._runtime_errors.pop(request_id, None)
            raise
        if not isinstance(result, bytes):
            raise RuntimeError("Browser returned an invalid screenshot payload")
        return result

    @staticmethod
    def _is_valid_screenshot_png(data: bytes) -> bool:
        """Validate the structural PNG framing without decompressing image data."""
        if len(data) < 45 or not data.startswith(_PNG_SIGNATURE):
            return False

        offset = len(_PNG_SIGNATURE)
        saw_idat = False
        while offset < len(data):
            if offset + 12 > len(data):
                return False
            chunk_length = struct.unpack(">I", data[offset : offset + 4])[0]
            chunk_end = offset + 12 + chunk_length
            if chunk_end > len(data):
                return False
            chunk_type = data[offset + 4 : offset + 8]
            chunk_data = data[offset + 8 : offset + 8 + chunk_length]
            expected_crc = struct.unpack(">I", data[offset + 8 + chunk_length : chunk_end])[0]
            if zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF != expected_crc:
                return False

            if offset == len(_PNG_SIGNATURE):
                if chunk_type != b"IHDR" or chunk_length != 13:
                    return False
                width, height = struct.unpack(">II", chunk_data[:8])
                if width == 0 or height == 0 or width * height > _MAX_SCREENSHOT_PIXELS:
                    return False
                bit_depth, color_type, compression, filter_method, interlace = chunk_data[8:]
                valid_bit_depths = {
                    0: {1, 2, 4, 8, 16},
                    2: {8, 16},
                    3: {1, 2, 4, 8},
                    4: {8, 16},
                    6: {8, 16},
                }
                if (
                    bit_depth not in valid_bit_depths.get(color_type, set())
                    or compression != 0
                    or filter_method != 0
                    or interlace not in {0, 1}
                ):
                    return False
            elif chunk_type == b"IDAT":
                saw_idat = True
            elif chunk_type == b"IEND":
                return chunk_length == 0 and saw_idat and chunk_end == len(data)

            offset = chunk_end
        return False

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
        entity_id_js = to_js_value(entity_id)
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
        source_js = to_js_value(source)
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
        if isinstance(interval, bool) or not isinstance(interval, (int, float)):
            raise TypeError("interval must be a positive finite number")
        if not math.isfinite(interval) or interval <= 0:
            raise ValueError("interval must be a positive finite number")

        poller_id = uuid4().hex
        poller_id_js = to_js_value(poller_id)
        url_js = to_js_value(url)
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
        poller_id_js = to_js_value(poller_id)
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
        if isinstance(interval, bool) or not isinstance(interval, (int, float)):
            raise TypeError("interval must be a positive finite number")
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
                if getattr(value, "requires_await", False):
                    parts.append("baseLayer: false")
                else:
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

    def _build_data_source_entity_statements(self) -> list[list[str]]:
        """Build per-data-source entity attachment statements.

        Statements reference ``_ds``, a variable both the HTML template and
        the widget ESM declare per data source. Referencing the object (not
        ``dataSources.get(i)``) sidesteps Cesium's async collection add.
        """
        statements: list[list[str]] = []
        for ds in self._data_sources:
            ds_statements: list[str] = []
            entities = getattr(ds, "entities", None)
            for entity in entities or []:
                ds_statements.append(f"_ds.entities.add({entity.to_js()});")
            statements.append(ds_statements)
        return statements

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

    def _build_imagery_statements(self) -> list[str]:
        """Build JS statements that stack raster and WMTS imagery layers.

        The first local raster is the base layer (a Viewer constructor
        option); everything else lands here so layers accumulate in add
        order with their own opacity instead of replacing each other.
        """
        statements: list[str] = []
        configured_base_layer = self._viewer_options.get("base_layer")
        if configured_base_layer is not None and getattr(configured_base_layer, "requires_await", False):
            statements.append(
                "(async () => {"
                "try {"
                f"const provider = await {configured_base_layer.to_js()};"
                "viewer.imageryLayers.addImageryProvider(provider, 0);"
                "} catch (error) {"
                "console.error('Error loading imagery:', error);"
                "}"
                "})();"
            )
        base_assigned = False
        for index, spec in enumerate(self._imagery_layers):
            if spec["kind"] == "raster":
                url = f"/raster/{spec['id']}/{{z}}/{{x}}/{{y}}.png"
                options = [f"url: {to_js_value(url)}"]
                if spec["maximum_level"] is not None:
                    options.append(f"maximumLevel: {spec['maximum_level']}")
                if not base_assigned:
                    base_assigned = True
                    if spec["opacity"] != 1.0:
                        statements.append(f"viewer.imageryLayers.get(0).alpha = {spec['opacity']};")
                    continue
                var = f"_rasterLayer{index}"
                statements.append(
                    f"const {var} = viewer.imageryLayers.addImageryProvider("
                    f"new Cesium.UrlTemplateImageryProvider({{{', '.join(options)}}}));"
                )
                if spec["opacity"] != 1.0:
                    statements.append(f"{var}.alpha = {spec['opacity']};")
            else:
                options = [
                    f"url: {to_js_value(spec['url'])}",
                    f"layer: {to_js_value(spec['layer'])}",
                    f"style: {to_js_value(spec['style'])}",
                    f"tileMatrixSetID: {to_js_value(spec['tile_matrix_set'])}",
                    f"format: {to_js_value(spec['format'])}",
                ]
                if spec["maximum_level"] is not None:
                    options.append(f"maximumLevel: {spec['maximum_level']}")
                var = f"_wmtsLayer{index}"
                statements.append(
                    f"const {var} = viewer.imageryLayers.addImageryProvider("
                    f"new Cesium.WebMapTileServiceImageryProvider({{{', '.join(options)}}}));"
                )
                if spec["opacity"] != 1.0:
                    statements.append(f"{var}.alpha = {spec['opacity']};")
        return statements

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

    def _build_clustering_statements(self) -> list[str]:
        """Build JS statements for entity clustering configuration."""
        if self._clustering and hasattr(self._clustering, "to_js_statements"):
            return self._clustering.to_js_statements("viewer")
        return []

    def _build_terrain_statement(self) -> str | None:
        """Build the JS expression assigned to scene.terrainProvider."""
        if self._terrain_provider is None:
            return None
        return self._terrain_provider.to_js()

    # --- Output methods ---

    def _doc_parts(self) -> dict[str, Any]:
        """Return all serialized JS pieces of this viewer, for HTML or widgets.

        Keys are camelCase to match the widget ESM's ``state.*`` reads.
        """
        return {
            "viewerOptions": self._build_viewer_options_js(),
            "entities": self._build_entity_js_list(),
            "dataSources": self._build_data_source_js_list(),
            "dataSourceEntityStatements": self._build_data_source_entity_statements(),
            "tilesets": self._build_tileset_js_list(),
            "primitives": self._build_primitive_js_list(),
            "cameraOperations": self._build_camera_operations(),
            "eventHandlers": self._build_event_handler_js(),
            "sceneStatements": self._build_scene_statements(),
            "globeStatements": self._build_globe_statements(),
            "clockStatements": self._build_clock_statements(),
            "clusteringStatements": self._build_clustering_statements(),
            "terrainStatement": self._build_terrain_statement(),
            "imageryStatements": self._build_imagery_statements(),
            "customScripts": self._custom_scripts,
        }

    def _render_html(
        self,
        cesium_base_url: str | None = None,
        *,
        render_runtime_bridge: bool = False,
        session_token: str | None = None,
    ) -> str:
        """Render the full HTML document, optionally from a local Cesium build.

        Args:
            cesium_base_url: URL prefix of the directory containing Cesium.js.
                None loads Cesium from the CDN at the pinned DEFAULT_CESIUM_VERSION.
            render_runtime_bridge: Whether to include the local-server runtime
                bridge. Static HTML must not poll a server that does not exist.
            session_token: Per-server credential used by the runtime bridge.
        """
        doc = HtmlDocument(
            cesium_version=DEFAULT_CESIUM_VERSION,
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
            data_source_entity_statements=self._build_data_source_entity_statements(),
            tilesets=self._build_tileset_js_list(),
            primitives=self._build_primitive_js_list(),
            camera_operations=self._build_camera_operations(),
            event_handlers=self._build_event_handler_js(),
            scene_statements=self._build_scene_statements(),
            globe_statements=self._build_globe_statements(),
            clock_statements=self._build_clock_statements(),
            clustering_statements=self._build_clustering_statements(),
            imagery_statements=self._build_imagery_statements(),
            terrain_statement=self._build_terrain_statement(),
            custom_scripts=self._custom_scripts,
            render_runtime_bridge=render_runtime_bridge,
            session_token=session_token,
        )

    def to_html(self) -> str:
        """Render the complete standalone HTML document string."""
        return self._render_html()

    def save(self, path: str) -> None:
        """Save to an HTML file."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_html())

    def __enter__(self) -> Viewer:
        """Return this viewer and close its runtime resources on exit."""
        return self

    def __exit__(self, _exc_type: Any, _exc: Any, _traceback: Any) -> None:
        self.close()

    def _finalize_runtime(self, expected_server: Any | None = None) -> None:
        """Release a stopped server, its temporary directory, and rasters."""
        thread_id = threading.get_ident()
        server: Any = None
        tempdir: tempfile.TemporaryDirectory[str] | None = None
        with self._lifecycle_lock:
            if self._runtime_finalization_done.is_set():
                return
            if self._runtime_finalization_owner is not None:
                if self._runtime_finalization_owner == thread_id:
                    return
                wait_for_finalization = True
            elif expected_server is not None and self._server is not expected_server:
                return
            else:
                self._runtime_finalization_owner = thread_id
                server = self._server
                tempdir = self._server_tempdir
                self._closed = True
                wait_for_finalization = False

        if wait_for_finalization:
            self._runtime_finalization_done.wait()
            return

        cleanup_error: BaseException | None = None
        try:
            if server is not None:
                try:
                    server.server_close()
                except OSError:
                    pass
                except BaseException as exc:
                    cleanup_error = exc
            for raster in tuple(self._raster_sources.values()):
                closer = getattr(raster, "close", None)
                if callable(closer):
                    try:
                        closer()
                    except BaseException as exc:
                        if cleanup_error is None:
                            cleanup_error = exc
            if tempdir is not None:
                try:
                    tempdir.cleanup()
                except BaseException as exc:
                    if cleanup_error is None:
                        cleanup_error = exc
            try:
                with self._runtime_condition:
                    self._command_queue.clear()
                    self._command_sizes.clear()
                    self._command_log_bytes = 0
                    for request_id in self._pending_runtime_ids:
                        self._runtime_errors.setdefault(request_id, "Viewer closed")
                    self._runtime_condition.notify_all()
            except BaseException as exc:
                if cleanup_error is None:
                    cleanup_error = exc
        finally:
            with self._lifecycle_lock:
                self._server = None
                self._server_tempdir = None
                self._session_token = None
                self._runtime_finalization_owner = None
                self._runtime_finalization_done.set()
        if cleanup_error is not None:
            raise cleanup_error

    def close(self) -> None:
        """Stop the local server and release all viewer-owned resources.

        This method is idempotent. Closing a viewer is terminal: create a new
        viewer to start another local runtime after resources have been freed.
        """
        with self._lifecycle_lock:
            if self._closed and self._runtime_finalization_done.is_set():
                return
            self._closed = True
            server = self._server

        if server is not None:
            try:
                server.shutdown()
            except OSError:
                pass
        if server is not None and getattr(threading.current_thread(), "_cesiumkit_runtime_server", None) is server:
            # A callback may close its Viewer from this request handler. The
            # serve_forever() thread drains handlers after this one returns.
            return
        self._finalize_runtime(server)

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

        with self._lifecycle_lock:
            if self._closed:
                raise RuntimeError("Viewer is closed")
            if self._server is not None:
                raise RuntimeError("Viewer is already being shown")

        tempdir = tempfile.TemporaryDirectory(prefix="cesiumkit_")
        server: Any | None = None
        server_published = False
        cesium_base_url = vendor_base_url()
        session_token = secrets.token_urlsafe(32)
        try:
            html_path = os.path.join(tempdir.name, "index.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(
                    self._render_html(
                        cesium_base_url=cesium_base_url,
                        render_runtime_bridge=True,
                        session_token=session_token,
                    )
                )

            class BoundedThreadingHTTPServer(ThreadingHTTPServer):
                """Threading HTTP server with bounded, non-blocking overload handling."""

                def __init__(self, *args: Any, **kwargs: Any) -> None:
                    self._request_slots = threading.BoundedSemaphore(_MAX_RUNTIME_HTTP_THREADS)
                    super().__init__(*args, **kwargs)

                def process_request(self, request: Any, client_address: Any) -> None:
                    if not self._request_slots.acquire(blocking=False):
                        self._reject_overloaded_request(request)
                        return
                    try:
                        super().process_request(request, client_address)
                    except BaseException:
                        self._request_slots.release()
                        raise

                def process_request_thread(self, request: Any, client_address: Any) -> None:
                    current_thread = threading.current_thread()
                    setattr(current_thread, "_cesiumkit_runtime_server", self)
                    try:
                        super().process_request_thread(request, client_address)
                    finally:
                        delattr(current_thread, "_cesiumkit_runtime_server")
                        self._request_slots.release()

                @staticmethod
                def _reject_overloaded_request(request: Any) -> None:
                    body = b'{"error":"runtime server busy"}'
                    response = (
                        b"HTTP/1.1 503 Service Unavailable\r\n"
                        b"Content-Type: application/json\r\n"
                        b"Cache-Control: no-store\r\n"
                        b"Connection: close\r\n" + f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body
                    )
                    try:
                        deadline = time.monotonic() + _RUNTIME_OVERLOAD_DRAIN_SECONDS
                        request.settimeout(_RUNTIME_OVERLOAD_DRAIN_SECONDS)
                        request.sendall(response)
                        try:
                            request.shutdown(socket.SHUT_WR)
                        except OSError:
                            pass
                        try:
                            while True:
                                remaining = deadline - time.monotonic()
                                if remaining <= 0:
                                    break
                                request.settimeout(remaining)
                                if not request.recv(64 * 1024):
                                    break
                        except OSError:
                            pass
                    except OSError:
                        pass
                    finally:
                        request.close()

            class Handler(SimpleHTTPRequestHandler):
                _viewer: Any

                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=tempdir.name, **kwargs)

                def setup(self) -> None:
                    self.request.settimeout(_RUNTIME_CONNECTION_TIMEOUT_SECONDS)
                    super().setup()

                def parse_request(self) -> bool:
                    if not super().parse_request():
                        return False
                    if not self._host_is_valid():
                        self.send_error(421, "Invalid Host header")
                        return False
                    return True

                def _host_is_valid(self) -> bool:
                    hosts = self.headers.get_all("Host") or []
                    if len(hosts) != 1:
                        return False
                    port = int(getattr(self.server, "server_port"))
                    host = hosts[0].strip().lower()
                    return host in {f"127.0.0.1:{port}", f"localhost:{port}"}

                def translate_path(self, path):
                    # Serve the bundled Cesium build (if present) from the
                    # installed package, without copying it into the temp dir.
                    request_path = urlparse(path).path
                    if cesium_base_url and request_path.startswith(cesium_base_url + "/"):
                        vendor = vendor_dir()
                        if vendor is None:
                            return super().translate_path(path)
                        rel = request_path[len(cesium_base_url) :].lstrip("/")
                        vendor_root = os.path.realpath(str(vendor))
                        target = os.path.realpath(os.path.join(vendor_root, rel))
                        try:
                            is_vendor_path = os.path.commonpath([vendor_root, target]) == vendor_root
                        except ValueError:
                            # Windows raises when a crafted path resolves to a
                            # different drive. Treat it exactly like traversal.
                            return os.path.join(tempdir.name, ".cesiumkit-invalid-vendor-path")
                        if not is_vendor_path:
                            return super().translate_path(path)
                        return target
                    return super().translate_path(path)

                def copyfile(self, source: Any, outputfile: Any) -> None:
                    try:
                        super().copyfile(source, outputfile)
                    except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, TimeoutError):
                        return

                def do_GET(self):
                    parsed = urlparse(self.path)
                    if parsed.path == "/__cesiumkit_cmd":
                        try:
                            self._handle_command_poll(parsed)
                        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, TimeoutError):
                            return
                        return
                    if parsed.path.startswith("/raster/"):
                        try:
                            self._handle_raster_tile(parsed)
                        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, TimeoutError):
                            return
                        return
                    super().do_GET()

                def _handle_raster_tile(self, parsed: Any) -> None:
                    """Serve a Web Mercator tile from a registered raster source."""
                    if parsed.query:
                        self.send_error(400, "Raster tile query parameters are not supported")
                        return
                    parts = parsed.path.strip("/").split("/")
                    if len(parts) != 5 or parts[0] != "raster" or not parts[4].endswith(".png"):
                        self.send_error(400, "Invalid raster tile path")
                        return
                    _, source_id, z, x, filename = parts
                    y = filename[: -len(".png")]
                    coordinates = (z, x, y)
                    if not all(value.isascii() and value.isdecimal() for value in coordinates):
                        self.send_error(400, "Invalid raster tile coordinates")
                        return
                    if len(z) > 2 or len(x) > 10 or len(y) > 10:
                        self.send_error(404, "Tile out of range")
                        return
                    z_value, x_value, y_value = (int(value) for value in coordinates)
                    if z_value > 30 or x_value >= 1 << z_value or y_value >= 1 << z_value:
                        self.send_error(404, "Tile out of range")
                        return
                    source = self._viewer._raster_sources.get(source_id)
                    if source is None:
                        self.send_error(404, "Unknown raster source")
                        return
                    try:
                        body = source.tile(z_value, x_value, y_value)
                    except Exception:
                        logger.exception("Raster tile rendering failed")
                        self.send_error(500, "Raster tile rendering failed")
                        return
                    if body is None:
                        self.send_error(404, "Tile out of range")
                        return
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

                def do_POST(self):
                    parsed = urlparse(self.path)
                    if parsed.path == "/__cesiumkit_result" and not parsed.query:
                        try:
                            self._handle_runtime_result()
                        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, TimeoutError):
                            return
                        return
                    if parsed.path == "/__cesiumkit_screenshot" and not parsed.query:
                        try:
                            self._handle_screenshot_upload()
                        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, TimeoutError):
                            return
                        return
                    self.send_error(405)

                def _session_is_valid(self, token: Any) -> bool:
                    expected = self._viewer._session_token
                    return isinstance(token, str) and expected is not None and secrets.compare_digest(token, expected)

                def _handle_command_poll(self, parsed: Any) -> None:
                    params = parse_qs(parsed.query, keep_blank_values=True)
                    if set(params) != {"seq", "token"} or any(len(values) != 1 for values in params.values()):
                        self.send_error(400, "Invalid command request")
                        return
                    seq_text = params["seq"][0]
                    if not seq_text.isascii() or not seq_text.isdecimal() or len(seq_text) > 16:
                        self.send_error(400, "Invalid command sequence")
                        return
                    if not self._session_is_valid(params["token"][0]):
                        self.send_error(403, "Invalid runtime session")
                        return
                    client_seq = int(seq_text)
                    with self._viewer._runtime_condition:
                        cmd = next(
                            (item for item in self._viewer._command_queue if item["seq"] > client_seq),
                            None,
                        )
                    body = json.dumps(cmd or {}, separators=(",", ":")).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

                @staticmethod
                def _is_runtime_request_id(value: Any) -> bool:
                    return (
                        isinstance(value, str)
                        and len(value) == 32
                        and all(char in "0123456789abcdef" for char in value)
                    )

                def _record_screenshot_failure(self, request_id: str, message: str) -> None:
                    with self._viewer._runtime_condition:
                        if (
                            request_id in self._viewer._pending_screenshot_ids
                            and request_id not in self._viewer._runtime_results
                            and request_id not in self._viewer._runtime_errors
                        ):
                            self._viewer._runtime_errors[request_id] = message
                            self._viewer._runtime_condition.notify_all()

                def _handle_screenshot_upload(self) -> None:
                    """Accept one bounded PNG blob for an active screenshot request."""
                    content_type = self.headers.get("Content-Type", "")
                    if content_type.strip().lower() != "image/png":
                        self.send_error(415, "Expected image/png")
                        return
                    content_lengths = self.headers.get_all("Content-Length") or []
                    if len(content_lengths) != 1 or self.headers.get("Transfer-Encoding"):
                        self.send_error(400, "Invalid content length")
                        return
                    content_length_text = content_lengths[0]
                    if (
                        len(content_length_text) > 10
                        or not content_length_text.isascii()
                        or not content_length_text.isdecimal()
                    ):
                        self.send_error(400, "Invalid content length")
                        return
                    content_length = int(content_length_text)

                    tokens = self.headers.get_all("X-CesiumKit-Token") or []
                    request_ids = self.headers.get_all("X-CesiumKit-Request-Id") or []
                    if len(tokens) != 1 or len(request_ids) != 1:
                        self.send_error(400, "Invalid screenshot request")
                        return
                    if not self._session_is_valid(tokens[0]):
                        self.send_error(403, "Invalid runtime session")
                        return
                    request_id = request_ids[0]
                    if not self._is_runtime_request_id(request_id):
                        self.send_error(400, "Invalid screenshot request")
                        return

                    with self._viewer._runtime_condition:
                        if (
                            request_id not in self._viewer._pending_screenshot_ids
                            or request_id not in self._viewer._pending_runtime_ids
                            or request_id in self._viewer._runtime_results
                            or request_id in self._viewer._runtime_errors
                        ):
                            self.send_error(404, "Unknown screenshot request")
                            return
                        if request_id in self._viewer._screenshot_upload_ids:
                            self.send_error(409, "Screenshot upload already in progress")
                            return
                        self._viewer._screenshot_upload_ids.add(request_id)

                    try:
                        if content_length <= 0 or content_length > _MAX_SCREENSHOT_BYTES:
                            self._record_screenshot_failure(
                                request_id,
                                "Screenshot upload rejected: payload exceeds the 32 MiB limit",
                            )
                            self.send_error(413, "Invalid screenshot payload size")
                            return
                        try:
                            body = self.rfile.read(content_length)
                        except TimeoutError:
                            self._record_screenshot_failure(
                                request_id,
                                "Screenshot upload rejected: PNG payload timed out",
                            )
                            return
                        if len(body) != content_length:
                            self._record_screenshot_failure(
                                request_id,
                                "Screenshot upload rejected: incomplete PNG payload",
                            )
                            self.send_error(400, "Incomplete screenshot payload")
                            return
                        if not self._viewer._is_valid_screenshot_png(body):
                            self._record_screenshot_failure(
                                request_id,
                                "Screenshot upload rejected: invalid PNG payload",
                            )
                            self.send_error(400, "Invalid screenshot payload")
                            return

                        with self._viewer._runtime_condition:
                            if (
                                request_id not in self._viewer._pending_screenshot_ids
                                or request_id not in self._viewer._pending_runtime_ids
                                or request_id in self._viewer._runtime_results
                                or request_id in self._viewer._runtime_errors
                            ):
                                self.send_error(404, "Unknown screenshot request")
                                return
                            self._viewer._runtime_results[request_id] = body
                            self._viewer._runtime_condition.notify_all()
                        self._send_json_success()
                    finally:
                        with self._viewer._runtime_condition:
                            self._viewer._screenshot_upload_ids.discard(request_id)

                def _handle_runtime_result(self) -> None:
                    content_type = self.headers.get("Content-Type", "")
                    if content_type.split(";", 1)[0].strip().lower() != "application/json":
                        self.send_error(415, "Expected application/json")
                        return
                    tokens = self.headers.get_all("X-CesiumKit-Token") or []
                    if len(tokens) != 1:
                        self.send_error(400, "Invalid runtime session")
                        return
                    if not self._session_is_valid(tokens[0]):
                        self.send_error(403, "Invalid runtime session")
                        return
                    content_lengths = self.headers.get_all("Content-Length") or []
                    if len(content_lengths) != 1 or self.headers.get("Transfer-Encoding"):
                        self.send_error(400, "Invalid content length")
                        return
                    try:
                        content_length = int(content_lengths[0])
                    except ValueError:
                        self.send_error(400, "Invalid content length")
                        return
                    if content_length <= 0 or content_length > _MAX_RUNTIME_REQUEST_BYTES:
                        self.send_error(413, "Invalid result payload size")
                        return
                    try:
                        raw = self.rfile.read(content_length)
                        if len(raw) != content_length:
                            raise ValueError

                        def reject_json_constant(value: str) -> None:
                            raise ValueError(value)

                        data = json.loads(raw.decode("utf-8"), parse_constant=reject_json_constant)
                        if not isinstance(data, dict):
                            raise ValueError
                    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, TypeError, ValueError):
                        self.send_error(400, "Invalid result payload")
                        return
                    body_token = data.get("token")
                    if (
                        not isinstance(body_token, str)
                        or not self._session_is_valid(body_token)
                        or not secrets.compare_digest(tokens[0], body_token)
                    ):
                        self.send_error(403, "Invalid runtime session")
                        return

                    if "event" in data:
                        if set(data) != {"token", "event", "result"} or data["event"] != "click":
                            self.send_error(400, "Invalid runtime event")
                            return
                        result = data["result"]
                        if result is not None and not isinstance(result, str):
                            self.send_error(400, "Invalid runtime event")
                            return
                        self._viewer._handle_runtime_event("click", result)
                        self._send_json_success()
                        return

                    if set(data) != {"token", "requestId", "result", "error"}:
                        self.send_error(400, "Invalid result payload")
                        return
                    request_id = data["requestId"]
                    error = data["error"]
                    if not self._is_runtime_request_id(request_id) or error is not None and not isinstance(error, str):
                        self.send_error(400, "Invalid result payload")
                        return
                    with self._viewer._runtime_condition:
                        if (
                            request_id not in self._viewer._pending_runtime_ids
                            or request_id in self._viewer._runtime_results
                            or request_id in self._viewer._runtime_errors
                        ):
                            self.send_error(404, "Unknown runtime request")
                            return
                        if request_id in self._viewer._pending_screenshot_ids and error is None:
                            self.send_error(400, "Screenshot results must use binary upload")
                            return
                        if error is not None:
                            self._viewer._runtime_errors[request_id] = error
                        else:
                            self._viewer._runtime_results[request_id] = data["result"]
                        self._viewer._runtime_condition.notify_all()
                    self._send_json_success()

                def _send_json_success(self) -> None:
                    body = b'{"ok":true}'
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

                def log_message(self, format, *args):
                    pass

            Handler._viewer = self
            server = BoundedThreadingHTTPServer(("127.0.0.1", port), Handler)
            # Each accepted handler is synchronously drained by server_close().
            # The per-connection timeout bounds close() even for a partial body.
            server.daemon_threads = False
            server.block_on_close = True

            actual_port = server.server_address[1]
            url = f"http://127.0.0.1:{actual_port}/index.html"

            # Keep every action that can raise before the server is published.
            # A browser may connect now; the listening socket is already bound
            # and serve_forever() starts immediately after publication.
            if open_browser:
                webbrowser.open(url)

            print(f"Serving at {url}")
            print("Press Ctrl+C to stop the server.")

            with self._lifecycle_lock:
                if self._closed:
                    server.server_close()
                    server = None
                    raise RuntimeError("Viewer is closed")
                if self._server is not None:
                    server.server_close()
                    server = None
                    raise RuntimeError("Viewer is already being shown")
                # Clear the event before exposing the server. A concurrent
                # close() now waits for serve_forever() to observe shutdown,
                # instead of closing the socket before that loop starts.
                server._BaseServer__is_shut_down.clear()  # type: ignore[attr-defined]
                self._server = server
                self._server_tempdir = tempdir
                self._session_token = session_token
                server_published = True
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")
        finally:
            if server is not None and server_published:
                self._finalize_runtime(server)
            elif server is not None:
                server.server_close()
                tempdir.cleanup()
            else:
                tempdir.cleanup()

    def show_in_browser(self) -> None:
        """Alias for show(). Opens visualization via local HTTP server."""
        self.show()

    def _repr_html_(self) -> str:
        """Jupyter notebook display (HTML iframe)."""
        doc = HtmlDocument(
            cesium_version=DEFAULT_CESIUM_VERSION,
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


__all__ = [
    "Viewer",
]
