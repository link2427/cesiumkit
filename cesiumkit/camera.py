"""Camera operations and positioning for CesiumJS viewer."""

from __future__ import annotations

from typing import Any

from cesiumkit.base import CesiumBase
from cesiumkit._js_serializer import to_js_value, to_js_options


class CameraPosition(CesiumBase):
    """Represents a camera position with destination and orientation."""

    destination: Any = None
    orientation: Any = None

    def _js_class_name(self) -> str:
        return "CameraPosition"


class FlyToOptions(CesiumBase):
    """Options for camera flyTo operations."""

    destination: Any
    orientation: Any = None
    duration: float = 3.0
    maximum_height: float | None = None
    pitch_adjust_height: float | None = None
    fly_over_longitude: float | None = None
    fly_over_longitude_weight: float | None = None
    easing_function: str | None = None

    def _js_class_name(self) -> str:
        return "FlyToOptions"


class LookAtOptions(CesiumBase):
    """Options for camera lookAt operations."""

    target: Any
    offset: Any

    def _js_class_name(self) -> str:
        return "LookAtOptions"


class Camera:
    """Camera operations manager.

    Queues operations to be serialized as JS statements.
    Supports method chaining for a fluent API.
    """

    def __init__(self) -> None:
        self._operations: list[tuple[str, dict[str, Any]]] = []
        self.initial_view: CameraPosition | None = None

    def set_view(
        self, destination: Any, orientation: Any = None
    ) -> Camera:
        """Queue a setView operation."""
        opts: dict[str, Any] = {"destination": destination}
        if orientation is not None:
            opts["orientation"] = orientation
        self._operations.append(("setView", opts))
        return self

    def fly_to(
        self,
        destination: Any,
        orientation: Any = None,
        duration: float = 3.0,
        **kwargs: Any,
    ) -> Camera:
        """Queue a flyTo operation."""
        opts: dict[str, Any] = {"destination": destination, "duration": duration}
        if orientation is not None:
            opts["orientation"] = orientation
        opts.update(kwargs)
        self._operations.append(("flyTo", opts))
        return self

    def look_at(self, target: Any, offset: Any) -> Camera:
        """Queue a lookAt operation."""
        self._operations.append(("lookAt", {"target": target, "offset": offset}))
        return self

    def zoom_in(self, amount: float | None = None) -> Camera:
        """Queue a zoomIn operation."""
        self._operations.append(("zoomIn", {"amount": amount}))
        return self

    def zoom_out(self, amount: float | None = None) -> Camera:
        """Queue a zoomOut operation."""
        self._operations.append(("zoomOut", {"amount": amount}))
        return self

    def to_js_operations(self, viewer_var: str = "viewer") -> list[str]:
        """Return list of JS statements for all queued camera operations."""
        statements: list[str] = []

        if self.initial_view:
            opts: dict[str, Any] = {}
            if self.initial_view.destination:
                opts["destination"] = self.initial_view.destination
            if self.initial_view.orientation:
                opts["orientation"] = self.initial_view.orientation
            opts_js = to_js_options(opts, exclude_none=True)
            statements.append(f"{viewer_var}.camera.setView({opts_js});")

        for method, opts in self._operations:
            if method == "lookAt":
                target_js = to_js_value(opts["target"])
                offset_js = to_js_value(opts["offset"])
                statements.append(
                    f"{viewer_var}.camera.lookAt({target_js}, {offset_js});"
                )
            elif method in ("zoomIn", "zoomOut"):
                amount = opts.get("amount")
                if amount is not None:
                    statements.append(
                        f"{viewer_var}.camera.{method}({amount});"
                    )
                else:
                    statements.append(f"{viewer_var}.camera.{method}();")
            else:
                # setView, flyTo - take options object
                opts_js = to_js_options(opts, exclude_none=True)
                statements.append(
                    f"{viewer_var}.camera.{method}({opts_js});"
                )

        return statements
