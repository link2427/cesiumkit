"""The main Viewer class — primary entry point for cesiumkit."""

from __future__ import annotations

import json
import tempfile
import webbrowser
from typing import Any

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

    # --- Entity convenience methods ---

    def add_entity(self, entity: Any = None, **kwargs: Any) -> Any:
        """Add an entity. Can pass an Entity instance or keyword args."""
        return self.entities.add(entity, **kwargs)

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
        The server runs in a background thread and shuts down on KeyboardInterrupt.

        Args:
            port: Port to serve on. 0 = auto-pick a free port.
            open_browser: Whether to automatically open the browser.
        """
        import os
        from http.server import HTTPServer, SimpleHTTPRequestHandler

        tmpdir = tempfile.mkdtemp(prefix="cesiumkit_")
        html_path = os.path.join(tmpdir, "index.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(self.to_html())

        class Handler(SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=tmpdir, **kwargs)

            def log_message(self, format, *args):
                pass  # Suppress request logs

        server = HTTPServer(("127.0.0.1", port), Handler)
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
