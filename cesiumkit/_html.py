"""HTML document assembly for cesiumkit."""

from __future__ import annotations

import html
from typing import Any

from cesiumkit._template import render_template


class HtmlDocument:
    """Assembles the full HTML output for a Viewer."""

    def __init__(
        self,
        cesium_version: str = "1.119",
        ion_token: str | None = None,
        width: str = "100%",
        height: str = "100%",
        title: str = "cesiumkit",
        container_id: str = "cesiumContainer",
    ) -> None:
        self.cesium_version = cesium_version
        self.ion_token = ion_token
        self.width = width
        self.height = height
        self.title = title
        self.container_id = container_id

    def render(
        self,
        viewer_options: str = "{}",
        entities: list[str] | None = None,
        data_sources: list[str] | None = None,
        tilesets: list[str] | None = None,
        camera_operations: list[str] | None = None,
        event_handlers: list[str] | None = None,
        scene_statements: list[str] | None = None,
        globe_statements: list[str] | None = None,
        clock_statements: list[str] | None = None,
        custom_scripts: list[str] | None = None,
    ) -> str:
        """Render the complete HTML string."""
        return render_template(
            "viewer.html.j2",
            title=self.title,
            cesium_version=self.cesium_version,
            ion_token=self.ion_token,
            container_id=self.container_id,
            width=self.width,
            height=self.height,
            viewer_options=viewer_options,
            entities=entities or [],
            data_sources=data_sources or [],
            tilesets=tilesets or [],
            camera_operations=camera_operations or [],
            event_handlers=event_handlers or [],
            scene_statements=scene_statements or [],
            globe_statements=globe_statements or [],
            clock_statements=clock_statements or [],
            custom_scripts=custom_scripts or [],
        )

    def render_jupyter(self, html_content: str, width: str = "100%", height: str = "600px") -> str:
        """Render the Jupyter iframe wrapper."""
        escaped = html.escape(html_content)
        return render_template(
            "jupyter.html.j2",
            html_content=escaped,
            width=width,
            height=height,
        )
