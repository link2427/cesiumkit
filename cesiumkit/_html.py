"""HTML document assembly for cesiumkit."""

from __future__ import annotations

from urllib.parse import urlsplit

from cesiumkit._template import render_template

# The CesiumJS release cesiumkit generates JavaScript against. This is the
# version bundled by scripts/fetch_cesium.py and served locally by show();
# static HTML export and Jupyter embedding fall back to the CDN.
DEFAULT_CESIUM_VERSION = "1.144"

_CDN_CESIUM_BASE = "https://cesium.com/downloads/cesiumjs/releases"


class HtmlDocument:
    """Assembles the full HTML output for a Viewer."""

    def __init__(
        self,
        cesium_version: str = DEFAULT_CESIUM_VERSION,
        cesium_base_url: str | None = None,
        ion_token: str | None = None,
        width: str = "100%",
        height: str = "100%",
        title: str = "cesiumkit",
        container_id: str = "cesiumContainer",
    ) -> None:
        self.cesium_version = cesium_version
        # URL prefix of the directory containing Cesium.js (and Widgets/,
        # Assets/). None means "load from the CDN".
        self.cesium_base_url = cesium_base_url
        self.ion_token = ion_token
        self.width = width
        self.height = height
        self.title = title
        self.container_id = container_id

    def _cesium_js_url(self) -> str:
        """URL of Cesium.js: local vendor build when available, else CDN."""
        if self.cesium_base_url:
            return f"{self._validated_cesium_base_url()}/Cesium.js"
        return f"{_CDN_CESIUM_BASE}/{self.cesium_version}/Build/Cesium/Cesium.js"

    def _cesium_css_url(self) -> str:
        """URL of widgets.css, matching the Cesium.js location."""
        if self.cesium_base_url:
            return f"{self._validated_cesium_base_url()}/Widgets/widgets.css"
        return f"{_CDN_CESIUM_BASE}/{self.cesium_version}/Build/Cesium/Widgets/widgets.css"

    def _validated_cesium_base_url(self) -> str:
        """Return a script-safe Cesium base URL.

        Relative paths and HTTP(S) URLs are supported. Rejecting executable URL
        schemes keeps an untrusted base URL from becoming a script source.
        """
        if self.cesium_base_url is None:
            raise ValueError("cesium_base_url is required")
        scheme = urlsplit(self.cesium_base_url).scheme.lower()
        if scheme and scheme not in {"http", "https"}:
            raise ValueError("cesium_base_url must be a relative, HTTP, or HTTPS URL")
        return self.cesium_base_url.rstrip("/")

    def render(
        self,
        viewer_options: str = "{}",
        entities: list[str] | None = None,
        data_sources: list[str] | None = None,
        data_source_entity_statements: list[list[str]] | None = None,
        tilesets: list[str] | None = None,
        primitives: list[str] | None = None,
        camera_operations: list[str] | None = None,
        event_handlers: list[str] | None = None,
        scene_statements: list[str] | None = None,
        globe_statements: list[str] | None = None,
        clock_statements: list[str] | None = None,
        clustering_statements: list[str] | None = None,
        imagery_statements: list[str] | None = None,
        terrain_statement: str | None = None,
        custom_scripts: list[str] | None = None,
        render_runtime_bridge: bool = False,
        session_token: str | None = None,
    ) -> str:
        """Render the complete HTML string."""
        if render_runtime_bridge and session_token is None:
            raise ValueError("session_token is required when render_runtime_bridge is enabled")
        return render_template(
            "viewer.html.j2",
            title=self.title,
            cesium_js_url=self._cesium_js_url(),
            cesium_css_url=self._cesium_css_url(),
            ion_token=self.ion_token,
            container_id=self.container_id,
            width=self.width,
            height=self.height,
            viewer_options=viewer_options,
            entities=entities or [],
            data_sources=data_sources or [],
            data_source_entity_statements=data_source_entity_statements or [],
            tilesets=tilesets or [],
            primitives=primitives or [],
            camera_operations=camera_operations or [],
            event_handlers=event_handlers or [],
            scene_statements=scene_statements or [],
            globe_statements=globe_statements or [],
            clock_statements=clock_statements or [],
            clustering_statements=clustering_statements or [],
            imagery_statements=imagery_statements or [],
            terrain_statement=terrain_statement,
            custom_scripts=custom_scripts or [],
            render_runtime_bridge=render_runtime_bridge,
            session_token=session_token,
        )

    def render_jupyter(self, html_content: str, width: str = "100%", height: str = "600px") -> str:
        """Render the Jupyter iframe wrapper."""
        return render_template(
            "jupyter.html.j2",
            html_content=html_content,
            width=width,
            height=height,
        )
