"""Jupyter widget integration (anywidget).

``CesiumKitWidget`` renders a Viewer inside a notebook with a live
bidirectional command channel: Python sends commands (clock, selection,
screenshot) over the comm, the widget's JavaScript evaluates them against
``window.viewer`` and sends results/click events back.

Requires the ``[widget]`` extra (anywidget). Import lazily:

    from cesiumkit.widget import CesiumKitWidget
    widget = viewer.to_widget()
"""

from __future__ import annotations

import base64
import binascii
import logging
import math
import re
import threading
from collections.abc import Callable
from concurrent.futures import Future
from concurrent.futures import TimeoutError as FutureTimeoutError
from pathlib import Path
from typing import Any

import anywidget
import traitlets

from cesiumkit._deprecations import warn_deprecated
from cesiumkit._html import DEFAULT_CESIUM_VERSION
from cesiumkit._js_serializer import to_js_value

logger = logging.getLogger(__name__)

_MAX_PENDING_REQUESTS = 128

_ESM = r"""
function _loadStylesheet(url) {
    if (document.querySelector(`link[data-cesiumkit-css="${url}"]`)) return Promise.resolve();
    return new Promise((resolve, reject) => {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = url;
        link.dataset.cesiumkitCss = url;
        link.onload = () => resolve();
        link.onerror = () => reject(new Error('failed to load CesiumJS CSS from ' + url));
        document.head.appendChild(link);
    });
}

function _loadCesium(url, cssUrl) {
    const scriptReady = window.Cesium ? Promise.resolve() : new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = url;
        script.onload = () => resolve();
        script.onerror = () => reject(new Error('failed to load CesiumJS from ' + url));
        document.head.appendChild(script);
    });
    return Promise.all([scriptReady, _loadStylesheet(cssUrl)]);
}

function _evalAll(viewer, statements) {
    for (const stmt of statements || []) {
        eval(stmt);
    }
}

async function render({ model, el }) {
    const state = model.get('state');
    el.style.width = '100%';
    el.style.height = state.height || '600px';

    await _loadCesium(state.cesiumUrl, state.cesiumCssUrl);
    if (state.ionToken) {
        Cesium.Ion.defaultAccessToken = state.ionToken;
    }

    // Replicates the viewer.html.j2 fallback: no Ion token means use the
    // NaturalEarthII tiles bundled with Cesium's CDN build.
    const viewerOptions = Object.assign({}, eval('(' + state.viewerOptions + ')'));
    if (!state.ionToken) {
        if (viewerOptions.baseLayer === undefined) {
            const naturalEarthUrl = Cesium.buildModuleUrl('Assets/Textures/NaturalEarthII/') + '{z}/{x}/{reverseY}.jpg';
            viewerOptions.baseLayer = new Cesium.ImageryLayer(
                new Cesium.UrlTemplateImageryProvider({
                    url: naturalEarthUrl,
                    tilingScheme: new Cesium.GeographicTilingScheme(),
                    maximumLevel: 2,
                    credit: 'Natural Earth II'
                })
            );
        }
        if (viewerOptions.baseLayerPicker === undefined) viewerOptions.baseLayerPicker = false;
        if (viewerOptions.geocoder === undefined) viewerOptions.geocoder = false;
    }

    const viewer = new Cesium.Viewer(el, viewerOptions);
    window.viewer = viewer;

    if (state.terrainStatement) {
        (async () => {
            try {
                viewer.scene.terrainProvider = await eval(state.terrainStatement);
            } catch (error) {
                console.error('Error loading terrain:', error);
            }
        })();
    }

    _evalAll(viewer, state.clusteringStatements);
    _evalAll(viewer, state.sceneStatements);
    _evalAll(viewer, state.globeStatements);
    _evalAll(viewer, state.clockStatements);
    _evalAll(viewer, state.imageryStatements);
    _evalAll(viewer, state.cameraOperations);

    for (const entityJs of state.entities || []) {
        viewer.entities.add(eval(entityJs));
    }
    for (let i = 0; i < (state.dataSources || []).length; i++) {
        var _ds = eval(state.dataSources[i]);
        viewer.dataSources.add(_ds);
        for (const stmt of (state.dataSourceEntityStatements || [])[i] || []) {
            eval(stmt);
        }
    }
    for (const tilesetJs of state.tilesets || []) {
        (async () => {
            try {
                viewer.scene.primitives.add(await eval(tilesetJs));
            } catch (error) {
                console.error('Error loading tileset:', error);
            }
        })();
    }
    for (const primitiveJs of state.primitives || []) {
        viewer.scene.primitives.add(eval(primitiveJs));
    }
    _evalAll(viewer, state.eventHandlers);
    _evalAll(viewer, state.customScripts);

    // Bidirectional command bridge over the comm channel.
    const onCustomMessage = (msg) => {
        if (!msg || msg.type !== 'command') return;
        const respond = (result, error) => {
            model.send({ type: 'result', requestId: msg.requestId, result: result, error: error });
        };
        try {
            const value = eval(msg.js);
            Promise.resolve(value).then(
                (resolved) => respond(resolved ?? null, null),
                (err) => respond(null, String(err))
            );
        } catch (error) {
            respond(null, String(error));
        }
    };
    model.on('msg:custom', onCustomMessage);

    const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
    handler.setInputAction((click) => {
        const picked = viewer.scene.pick(click.position);
        model.send({
            type: 'event',
            event: 'click',
            result: picked && picked.id ? picked.id.id : null,
        });
    }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

    return () => {
        if (typeof model.off === 'function') {
            model.off('msg:custom', onCustomMessage);
        }
        if (!handler.isDestroyed()) handler.destroy();
        if (!viewer.isDestroyed()) viewer.destroy();
        if (window.viewer === viewer) delete window.viewer;
    };
}

export default { render };
"""

_CSS = """
:host {
    display: block;
    width: 100%;
}
"""


class CesiumKitWidget(anywidget.AnyWidget):
    """A Jupyter widget rendering a cesiumkit Viewer with live control."""

    _esm = _ESM
    _css = _CSS

    state = traitlets.Dict({}).tag(sync=True)

    def __init__(
        self,
        viewer: Any,
        *,
        height: str = "600px",
        cesium_version: str | None = None,
    ) -> None:
        super().__init__()
        if cesium_version is None:
            resolved_cesium_version = DEFAULT_CESIUM_VERSION
        else:
            if not isinstance(cesium_version, str):
                raise TypeError("cesium_version must be a Cesium release string or None")
            if re.fullmatch(r"[0-9]+\.[0-9]+(?:\.[0-9]+)?", cesium_version) is None:
                raise ValueError("cesium_version must contain only numeric release components")
            warn_deprecated(
                "CesiumKitWidget(cesium_version=...)",
                alternative="omit cesium_version to use the tested bundled release",
            )
            resolved_cesium_version = cesium_version
        self._viewer = viewer
        self._pending: dict[str, Future] = {}
        self._condition = threading.Condition()
        self._click_callbacks: list[Callable[[Any], None]] = []
        self._request_counter = 0
        parts = viewer._doc_parts()
        self.state = {
            "ionToken": viewer.ion_token or "",
            "cesiumUrl": (
                f"https://cesium.com/downloads/cesiumjs/releases/{resolved_cesium_version}/Build/Cesium/Cesium.js"
            ),
            "cesiumCssUrl": (
                f"https://cesium.com/downloads/cesiumjs/releases/{resolved_cesium_version}/Build/Cesium/Widgets/widgets.css"
            ),
            "height": height,
            **parts,
        }
        self.on_msg(self._on_widget_message)

    # --- Command bridge (Python -> JS) ---

    def _send_command(self, js: str, timeout: float = 10.0) -> Any:
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            raise TypeError("timeout must be a finite non-negative number")
        if not math.isfinite(timeout) or timeout < 0:
            raise ValueError("timeout must be a finite non-negative number")
        future: Future = Future()
        with self._condition:
            if len(self._pending) >= _MAX_PENDING_REQUESTS:
                raise RuntimeError("too many pending widget requests")
            self._request_counter += 1
            request_id = f"w{self._request_counter}"
            self._pending[request_id] = future
        try:
            self.send({"type": "command", "requestId": request_id, "js": js})
        except BaseException:
            with self._condition:
                self._pending.pop(request_id, None)
            raise
        try:
            return future.result(timeout=timeout)
        except FutureTimeoutError as exc:
            with self._condition:
                self._pending.pop(request_id, None)
            raise TimeoutError(f"widget command timed out: {js[:80]}") from exc

    def _on_widget_message(self, widget: Any, content: dict[str, Any], buffers: list[bytes]) -> None:
        del widget, buffers  # on_msg callback signature; unused by the handler
        msg_type = content.get("type")
        if msg_type == "result":
            request_id = content.get("requestId")
            if request_id is None:
                return
            with self._condition:
                future = self._pending.pop(request_id, None)
                if future is not None:
                    if content.get("error") is not None:
                        future.set_exception(RuntimeError(content["error"]))
                    else:
                        future.set_result(content.get("result"))
                self._condition.notify_all()
        elif msg_type == "event" and content.get("event") == "click":
            for callback in tuple(self._click_callbacks):
                try:
                    callback(content.get("result"))
                except Exception:
                    logger.exception("Unhandled exception in cesiumkit widget click callback")

    # --- Runtime control (mirrors the show() server commands) ---

    def set_time(self, iso: str) -> None:
        """Set the clock to an ISO-8601 time."""
        if not isinstance(iso, str) or not iso:
            raise TypeError("iso must be a non-empty ISO-8601 string")
        self._send_command(f"viewer.clock.currentTime = Cesium.JulianDate.fromIso8601({to_js_value(iso)});")

    def set_multiplier(self, multiplier: float) -> None:
        """Set the clock multiplier (simulation speed)."""
        if isinstance(multiplier, bool) or not isinstance(multiplier, (int, float)):
            raise TypeError("multiplier must be a finite number")
        if not math.isfinite(multiplier):
            raise ValueError("multiplier must be finite")
        self._send_command(f"viewer.clock.multiplier = {multiplier!r};")

    def animate(self, on: bool) -> None:
        """Start or stop the clock animation."""
        if not isinstance(on, bool):
            raise TypeError("on must be a bool")
        self._send_command(f"viewer.clock.shouldAnimate = {'true' if on else 'false'};")

    def get_current_time(self, timeout: float = 10.0) -> str:
        """Return the current clock time as ISO-8601."""
        return self._send_command(
            "Cesium.JulianDate.toIso8601(viewer.clock.currentTime)",
            timeout=timeout,
        )

    def on_click(self, callback: Callable[[Any], None]) -> None:
        """Register a callback invoked with the clicked entity id (or None)."""
        if not callable(callback):
            raise TypeError("callback must be callable")
        self._click_callbacks.append(callback)

    def screenshot(self, path: str) -> None:
        """Save a PNG screenshot of the live canvas."""
        data_url = self._send_command(
            "(function(){const canvas = viewer.scene.canvas;return canvas.toDataURL('image/png').split(',')[1];})()"
        )
        if not isinstance(data_url, str):
            raise RuntimeError("widget returned an invalid screenshot payload")
        try:
            image = base64.b64decode(data_url, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise RuntimeError("widget returned malformed screenshot data") from exc
        if not image.startswith(b"\x89PNG\r\n\x1a\n"):
            raise RuntimeError("widget returned a non-PNG screenshot")
        Path(path).write_bytes(image)

    def close(self) -> None:
        """Close the widget and fail any commands still awaiting a browser reply."""
        with self._condition:
            pending = tuple(self._pending.values())
            self._pending.clear()
        for future in pending:
            if not future.done():
                future.set_exception(RuntimeError("widget closed"))
        super().close()


__all__ = [
    "CesiumKitWidget",
]
