"""The main Viewer class — primary entry point for cesiumkit."""

from __future__ import annotations

import json
import math
import tempfile
import threading
import time
import webbrowser
from collections import deque
from collections.abc import Iterable
from typing import Any
from uuid import uuid4

from cesiumkit._html import HtmlDocument
from cesiumkit._js_serializer import camelize, to_js_value
from cesiumkit.czml import CzmlDocument
from cesiumkit.enums import SceneMode, ScreenSpaceEventType
from cesiumkit.events import EventHandler
from cesiumkit.utils import JsCode


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
        cesium_version: str = "1.119",
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
        self.cesium_version = cesium_version
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
        }
        for key, val in opt_map.items():
            if val is not None:
                self._viewer_options[key] = val

        if scene_mode is not None:
            self._viewer_options["scene_mode"] = scene_mode
        if terrain_provider is not None:
            self._viewer_options["terrain_provider"] = terrain_provider
        if imagery_provider is not None:
            self._viewer_options["imagery_provider"] = imagery_provider

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
        self._event_handlers: list[EventHandler] = []
        self._custom_scripts: list[str] = []

        # Runtime command queue (for live viewer control)
        self._command_seq = 0
        self._command_queue: deque[dict[str, Any]] = deque()
        self._runtime_results: dict[str, Any] = {}
        self._runtime_errors: dict[str, str] = {}
        self._runtime_condition = threading.Condition()
        self._server: Any = None

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

    # --- Event handling ---

    def on(self, event_type: ScreenSpaceEventType, handler: JsCode | str) -> None:
        """Register a screen space event handler."""
        if isinstance(handler, str):
            handler = JsCode(handler)
        self._event_handlers.append(EventHandler(event_type=event_type, handler=handler))

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
            js_key = camelize(key)
            # Special handling for terrain_provider (async)
            if key == "terrain_provider" and hasattr(value, "to_js"):
                js_val = value.to_js()
                # If it's an async provider, we handle it separately
                parts.append(f"{js_key}: {js_val}")
            else:
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

    def _build_camera_operations(self) -> list[str]:
        """Build JS statements for camera operations."""
        return self.camera.to_js_operations("viewer")

    def _build_event_handler_js(self) -> list[str]:
        """Build JS expressions for event handlers."""
        return [eh.to_js("viewer") for eh in self._event_handlers]

    def _build_scene_statements(self) -> list[str]:
        """Build JS statements for scene configuration."""
        if self.scene_config and hasattr(self.scene_config, "to_js_statements"):
            return self.scene_config.to_js_statements("viewer")
        return []

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

    # --- Output methods ---

    def to_html(self) -> str:
        """Render the complete standalone HTML document string."""
        doc = HtmlDocument(
            cesium_version=self.cesium_version,
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
            camera_operations=self._build_camera_operations(),
            event_handlers=self._build_event_handler_js(),
            scene_statements=self._build_scene_statements(),
            globe_statements=self._build_globe_statements(),
            clock_statements=self._build_clock_statements(),
            custom_scripts=self._custom_scripts,
        )

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
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(self.to_html())

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=tmpdir, **kwargs)

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
                    request_id = data["requestId"]
                    if not isinstance(request_id, str):
                        raise TypeError
                except (json.JSONDecodeError, KeyError, TypeError):
                    self.send_error(400, "Invalid result payload")
                    return

                with self._viewer._runtime_condition:
                    if data.get("error") is not None:
                        self._viewer._runtime_errors[request_id] = str(data["error"])
                    else:
                        self._viewer._runtime_results[request_id] = data.get("result")
                    self._viewer._runtime_condition.notify_all()

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
