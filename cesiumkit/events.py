"""Event handling for cesiumkit."""

from __future__ import annotations

from typing import Any

from cesiumkit.base import CesiumBase
from cesiumkit.enums import ScreenSpaceEventType
from cesiumkit.utils import JsCode


class EventHandler(CesiumBase):
    """An event handler binding a screen space event to a JS callback."""

    event_type: ScreenSpaceEventType
    handler: Any  # JsCode

    def _js_class_name(self) -> str:
        return "Cesium.ScreenSpaceEventHandler"

    def to_js(self, viewer_var: str = "viewer") -> str:
        handler_code = self.handler
        if isinstance(handler_code, JsCode):
            handler_code = handler_code.js_code

        return (
            f"new Cesium.ScreenSpaceEventHandler({viewer_var}.scene.canvas)"
            f".setInputAction({handler_code}, "
            f"Cesium.ScreenSpaceEventType.{self.event_type.value})"
        )
