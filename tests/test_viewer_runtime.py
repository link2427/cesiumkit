"""Focused tests for Viewer local-server lifecycle and runtime protocol."""

from __future__ import annotations

import base64
import json
import os
import socket
import socketserver
import struct
import tempfile
import threading
import time
import urllib.error
import urllib.request
import zlib
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

import cesiumkit
from cesiumkit import viewer as viewer_module

_ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


@contextmanager
def running_viewer(viewer: cesiumkit.Viewer) -> Iterator[tuple[cesiumkit.Viewer, str]]:
    thread = threading.Thread(
        target=viewer.show,
        kwargs={"port": 0, "open_browser": False},
        daemon=True,
    )
    thread.start()
    for _ in range(100):
        if viewer._server is not None:
            break
        time.sleep(0.01)
    else:
        pytest.fail("viewer server did not start")
    address = viewer._server.server_address
    try:
        yield viewer, f"http://{address[0]}:{address[1]}"
    finally:
        viewer.close()
        thread.join(timeout=2)
        assert not thread.is_alive()


def request(
    url: str,
    *,
    method: str = "GET",
    body: bytes | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, bytes]:
    req = urllib.request.Request(url, data=body, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=2) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def raw_post_response(address: tuple[str, int], path: str, headers: dict[str, str]) -> bytes:
    """Send POST headers only; suitable for rejected oversized payloads."""
    lines = [f"POST {path} HTTP/1.1", f"Host: {address[0]}:{address[1]}", "Connection: close"]
    lines.extend(f"{name}: {value}" for name, value in headers.items())
    with socket.create_connection(address, timeout=2) as client:
        client.sendall(("\r\n".join(lines) + "\r\n\r\n").encode())
        client.shutdown(socket.SHUT_WR)
        response = bytearray()
        while chunk := client.recv(64 * 1024):
            response.extend(chunk)
    return bytes(response)


def partial_runtime_result_request(address: tuple[str, int], token: str) -> socket.socket:
    """Open a result request that holds its handler in a body read."""
    client = socket.create_connection(address, timeout=2)
    client.sendall(
        b"POST /__cesiumkit_result HTTP/1.1\r\n"
        + f"Host: localhost:{address[1]}\r\n".encode()
        + b"Content-Type: application/json\r\n"
        + b"Content-Length: 1048576\r\n"
        + f"X-CesiumKit-Token: {token}\r\n".encode()
        + b"Connection: keep-alive\r\n\r\n"
    )
    return client


def png_with_text_payload(size: int) -> bytes:
    """Make a valid PNG whose ancillary chunk exceeds the JSON result cap."""
    payload = b"Comment\x00" + b"x" * size
    chunk = struct.pack(">I", len(payload)) + b"tEXt" + payload
    chunk += struct.pack(">I", zlib.crc32(chunk[4:]) & 0xFFFFFFFF)
    return _ONE_PIXEL_PNG[:-12] + chunk + _ONE_PIXEL_PNG[-12:]


class TestRuntimeBridgeRendering:
    def test_static_html_does_not_include_runtime_polling(self):
        html = cesiumkit.Viewer().to_html()
        assert "__cesiumkitPollCommands" not in html
        assert "__cesiumkitSessionToken" not in html


class TestRuntimeServerProtocol:
    def test_authenticated_command_log_is_non_destructive(self):
        viewer = cesiumkit.Viewer()
        viewer.animate(False)
        with running_viewer(viewer) as (viewer, base_url):
            assert viewer._session_token is not None
            token = viewer._session_token
            command_url = f"{base_url}/__cesiumkit_cmd?seq=0&token={token}"
            status, body = request(command_url)
            assert status == 200
            first = json.loads(body)
            assert first["seq"] == 1
            assert "shouldAnimate" in first["js"]
            status, body = request(command_url)
            assert status == 200
            assert json.loads(body) == first
            assert len(viewer._command_queue) == 1

            assert request(f"{base_url}/__cesiumkit_cmd?seq=0")[0] == 400
            assert request(f"{base_url}/__cesiumkit_cmd?seq=0&token=wrong")[0] == 403
            assert request(f"{base_url}/__cesiumkit_cmd?seq=-1&token={token}")[0] == 400
            assert request(f"{base_url}/__cesiumkit_cmd?seq=1&token={token}") == (200, b"{}")
            assert request(f"{base_url}/__cesiumkit_cmd?seq={'9' * 5000}&token={token}")[0] == 400

    def test_command_log_has_bounded_retention(self):
        viewer = cesiumkit.Viewer()
        for index in range(1_025):
            viewer._send_command(f"command-{index}")
        assert len(viewer._command_queue) == 1_024
        assert viewer._command_queue[0]["seq"] == 2
        assert viewer._command_log_bytes <= 8 * 1_048_576
        with pytest.raises(ValueError, match="size limit"):
            viewer._send_command("x" * (1_048_576 + 1))

    def test_runtime_result_requires_json_token_and_pending_id(self):
        viewer = cesiumkit.Viewer()
        with running_viewer(viewer) as (viewer, base_url):
            token = viewer._session_token
            assert token is not None
            endpoint = f"{base_url}/__cesiumkit_result"
            valid_payload = {
                "token": token,
                "requestId": "a" * 32,
                "result": "ok",
                "error": None,
            }
            payload_bytes = json.dumps(valid_payload).encode()
            json_headers = {"Content-Type": "application/json", "X-CesiumKit-Token": token}

            assert request(endpoint, method="POST", body=payload_bytes)[0] == 415
            assert (
                request(
                    endpoint,
                    method="POST",
                    body=b"[" * 2_000 + b"]" * 2_000,
                    headers=json_headers,
                )[0]
                == 400
            )
            assert (
                request(
                    endpoint,
                    method="POST",
                    body=payload_bytes,
                    headers=json_headers,
                )[0]
                == 404
            )
            valid_payload["token"] = "wrong"
            assert (
                request(
                    endpoint,
                    method="POST",
                    body=json.dumps(valid_payload).encode(),
                    headers=json_headers,
                )[0]
                == 403
            )

            valid_payload["token"] = token
            with viewer._runtime_condition:
                viewer._pending_runtime_ids.add("a" * 32)
            assert (
                request(
                    endpoint,
                    method="POST",
                    body=json.dumps(valid_payload).encode(),
                    headers={"Content-Type": "application/json; charset=utf-8", "X-CesiumKit-Token": token},
                )[0]
                == 200
            )
            assert (
                request(
                    endpoint,
                    method="POST",
                    body=json.dumps(valid_payload).encode(),
                    headers=json_headers,
                )[0]
                == 404
            )
            assert viewer._wait_for_runtime_result("a" * 32, timeout=0) == "ok"

    def test_runtime_result_rejects_bad_header_token_before_reading_the_body(self):
        with running_viewer(cesiumkit.Viewer()) as (viewer, _):
            response = raw_post_response(
                viewer._server.server_address,
                "/__cesiumkit_result",
                {
                    "Content-Type": "application/json",
                    "Content-Length": "1048576",
                    "X-CesiumKit-Token": "wrong",
                },
            )
            assert b" 403 " in response
            for _ in range(100):
                if viewer._server._request_slots._value == viewer_module._MAX_RUNTIME_HTTP_THREADS:
                    break
                time.sleep(0.01)
            assert viewer._server._request_slots._value == viewer_module._MAX_RUNTIME_HTTP_THREADS

    def test_runtime_server_rejects_untrusted_host(self):
        with running_viewer(cesiumkit.Viewer()) as (viewer, base_url):
            port = viewer._server.server_address[1]
            assert request(f"{base_url}/index.html", headers={"Host": f"localhost:{port}"})[0] == 200
            assert request(f"{base_url}/index.html", headers={"Host": f"attacker.example:{port}"})[0] == 421

    def test_runtime_json_results_keep_the_one_mebibyte_cap(self):
        with running_viewer(cesiumkit.Viewer()) as (viewer, _):
            response = raw_post_response(
                viewer._server.server_address,
                "/__cesiumkit_result",
                {
                    "Content-Type": "application/json",
                    "Content-Length": str(viewer_module._MAX_RUNTIME_REQUEST_BYTES + 1),
                    "X-CesiumKit-Token": viewer._session_token,
                },
            )
            assert b" 413 " in response

    def test_partial_result_request_times_out_and_releases_its_handler(self, monkeypatch):
        monkeypatch.setattr(viewer_module, "_RUNTIME_CONNECTION_TIMEOUT_SECONDS", 0.05)
        with running_viewer(cesiumkit.Viewer()) as (viewer, _):
            token = viewer._session_token
            assert token is not None
            client = partial_runtime_result_request(viewer._server.server_address, token)
            try:
                client.settimeout(1)
                assert client.recv(1) == b""
                for _ in range(100):
                    if viewer._server._request_slots._value == viewer_module._MAX_RUNTIME_HTTP_THREADS:
                        break
                    time.sleep(0.01)
                assert viewer._server._request_slots._value == viewer_module._MAX_RUNTIME_HTTP_THREADS
            finally:
                client.close()

    def test_runtime_server_rejects_overload_without_waiting(self, monkeypatch):
        monkeypatch.setattr(viewer_module, "_MAX_RUNTIME_HTTP_THREADS", 2)
        with running_viewer(cesiumkit.Viewer()) as (viewer, _):
            token = viewer._session_token
            assert token is not None
            clients = [partial_runtime_result_request(viewer._server.server_address, token) for _ in range(2)]
            try:
                for _ in range(100):
                    if viewer._server._request_slots._value == 0:
                        break
                    time.sleep(0.01)
                assert viewer._server._request_slots._value == 0

                overloaded = socket.create_connection(viewer._server.server_address, timeout=2)
                try:
                    overloaded.settimeout(1)
                    started = time.monotonic()
                    overloaded.sendall(
                        (
                            f"GET /index.html HTTP/1.1\r\nHost: localhost:{viewer._server.server_address[1]}\r\n\r\n"
                        ).encode()
                    )
                    response = overloaded.recv(1024)
                    assert time.monotonic() - started < 1
                    assert b"503 Service Unavailable" in response
                finally:
                    overloaded.close()
            finally:
                for client in clients:
                    client.close()

    def test_overload_drain_has_an_absolute_deadline(self, monkeypatch):
        monkeypatch.setattr(viewer_module, "_MAX_RUNTIME_HTTP_THREADS", 1)
        monkeypatch.setattr(viewer_module, "_RUNTIME_OVERLOAD_DRAIN_SECONDS", 0.05)
        with running_viewer(cesiumkit.Viewer()) as (viewer, _):
            token = viewer._session_token
            assert token is not None
            active = partial_runtime_result_request(viewer._server.server_address, token)
            for _ in range(100):
                if viewer._server._request_slots._value == 0:
                    break
                time.sleep(0.01)
            assert viewer._server._request_slots._value == 0

            overloaded = socket.create_connection(viewer._server.server_address, timeout=2)
            stop_drip = threading.Event()

            def drip_bytes() -> None:
                while not stop_drip.is_set():
                    try:
                        overloaded.sendall(b"x")
                    except OSError:
                        return
                    time.sleep(0.01)

            drip_thread = threading.Thread(target=drip_bytes)
            drip_thread.start()
            time.sleep(0.1)
            active.close()
            close_thread = threading.Thread(target=viewer.close)
            close_thread.start()
            try:
                close_thread.join(timeout=1)
                assert not close_thread.is_alive()
            finally:
                stop_drip.set()
                overloaded.close()
                drip_thread.join(timeout=1)
                close_thread.join(timeout=1)

    def test_binary_screenshot_upload_accepts_png_larger_than_json_result_cap(self):
        viewer = cesiumkit.Viewer()
        request_id = "b" * 32
        png = png_with_text_payload(viewer_module._MAX_RUNTIME_REQUEST_BYTES + 1)
        assert len(png) > viewer_module._MAX_RUNTIME_REQUEST_BYTES
        with running_viewer(viewer) as (viewer, base_url):
            token = viewer._session_token
            assert token is not None
            with viewer._runtime_condition:
                viewer._pending_runtime_ids.add(request_id)
                viewer._pending_screenshot_ids.add(request_id)
            status, body = request(
                f"{base_url}/__cesiumkit_screenshot",
                method="POST",
                body=png,
                headers={
                    "Content-Type": "image/png",
                    "X-CesiumKit-Token": token,
                    "X-CesiumKit-Request-Id": request_id,
                },
            )
            assert status == 200
            assert json.loads(body) == {"ok": True}
            assert viewer._wait_for_runtime_result(request_id, timeout=0) == png

    def test_binary_screenshot_upload_rejects_invalid_or_unknown_requests(self):
        viewer = cesiumkit.Viewer()
        request_id = "c" * 32
        with running_viewer(viewer) as (viewer, base_url):
            token = viewer._session_token
            assert token is not None
            endpoint = f"{base_url}/__cesiumkit_screenshot"
            headers = {
                "Content-Type": "image/png",
                "X-CesiumKit-Token": token,
                "X-CesiumKit-Request-Id": request_id,
            }
            assert request(endpoint, method="POST", body=_ONE_PIXEL_PNG, headers={})[0] == 415
            assert (
                request(
                    endpoint,
                    method="POST",
                    body=_ONE_PIXEL_PNG,
                    headers={**headers, "X-CesiumKit-Token": "wrong"},
                )[0]
                == 403
            )
            assert request(endpoint, method="POST", body=_ONE_PIXEL_PNG, headers=headers)[0] == 404

            with viewer._runtime_condition:
                viewer._pending_runtime_ids.add(request_id)
                viewer._pending_screenshot_ids.add(request_id)
            invalid_png = b"not a PNG"
            assert request(endpoint, method="POST", body=invalid_png, headers=headers)[0] == 400
            with pytest.raises(RuntimeError, match="invalid PNG payload"):
                viewer._wait_for_runtime_result(request_id, timeout=0)

    def test_binary_screenshot_upload_over_limit_fails_pending_request(self):
        viewer = cesiumkit.Viewer()
        request_id = "d" * 32
        with running_viewer(viewer) as (viewer, _):
            token = viewer._session_token
            assert token is not None
            with viewer._runtime_condition:
                viewer._pending_runtime_ids.add(request_id)
                viewer._pending_screenshot_ids.add(request_id)
            response = raw_post_response(
                viewer._server.server_address,
                "/__cesiumkit_screenshot",
                {
                    "Content-Type": "image/png",
                    "Content-Length": str(viewer_module._MAX_SCREENSHOT_BYTES + 1),
                    "X-CesiumKit-Token": token,
                    "X-CesiumKit-Request-Id": request_id,
                },
            )
            assert b" 413 " in response
            with pytest.raises(RuntimeError, match="exceeds the 32 MiB limit"):
                viewer._wait_for_runtime_result(request_id, timeout=0)

    def test_binary_screenshot_upload_rejects_unbounded_content_length_digits(self):
        with running_viewer(cesiumkit.Viewer()) as (viewer, _):
            response = raw_post_response(
                viewer._server.server_address,
                "/__cesiumkit_screenshot",
                {
                    "Content-Type": "image/png",
                    "Content-Length": "9" * 5_000,
                },
            )
            assert b" 400 " in response

    def test_1920x1080_screenshot_uses_binary_browser_upload(self, playwright_browser, tmp_path):
        from cesiumkit._vendor import vendor_dir

        if vendor_dir() is None:
            pytest.skip("bundled Cesium build not present")
        viewer = cesiumkit.Viewer()
        with running_viewer(viewer) as (viewer, base_url):
            page = playwright_browser.new_page(viewport={"width": 1920, "height": 1080})
            try:
                page.goto(f"{base_url}/index.html", wait_until="domcontentloaded")
                page.wait_for_function("() => window.viewer && window.viewer.scene && window.viewer.scene.canvas")
                png = base64.b64decode(viewer.screenshot_base64(timeout=20), validate=True)
                assert png.startswith(b"\x89PNG\r\n\x1a\n")
                assert viewer._is_valid_screenshot_png(png)
                output = tmp_path / "screenshot.png"
                viewer.screenshot(output, timeout=20)
                assert viewer._is_valid_screenshot_png(output.read_bytes())
            finally:
                page.close()

    def test_runtime_event_queue_is_bounded(self):
        viewer = cesiumkit.Viewer()
        for index in range(300):
            viewer._handle_runtime_event("click", str(index))
        assert viewer._click_events.qsize() == viewer._click_events.maxsize
        assert viewer.wait_for_click(timeout=0) == "44"

    def test_client_disconnect_does_not_stop_runtime_server(self):
        viewer = cesiumkit.Viewer()
        viewer._send_command("x" * 1_048_576)
        with running_viewer(viewer) as (viewer, base_url):
            token = viewer._session_token
            assert token is not None
            address = viewer._server.server_address
            client = socket.create_connection(address, timeout=2)
            try:
                linger_format = "hh" if os.name == "nt" else "ii"
                client.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack(linger_format, 1, 0))
                client.sendall(
                    (
                        f"GET /__cesiumkit_cmd?seq=0&token={token} HTTP/1.1\r\n"
                        f"Host: {address[0]}\r\nConnection: close\r\n\r\n"
                    ).encode()
                )
            finally:
                client.close()
            time.sleep(0.1)
            status, _ = request(f"{base_url}/__cesiumkit_cmd?seq=0&token={token}")
            assert status == 200

    @pytest.mark.skipif(os.name != "nt", reason="Windows drive-path regression")
    def test_windows_malformed_vendor_drive_path_is_not_served(self, monkeypatch, tmp_path):
        import cesiumkit.viewer as viewer_module

        vendor = tmp_path / "vendor"
        vendor.mkdir()
        monkeypatch.setattr(viewer_module, "vendor_base_url", lambda: "/vendor/cesium")
        monkeypatch.setattr(viewer_module, "vendor_dir", lambda: vendor)
        with running_viewer(cesiumkit.Viewer()) as (_, base_url):
            assert request(f"{base_url}/vendor/cesium/D:/outside")[0] == 404


class TestViewerLifecycle:
    def test_browser_open_failure_cleans_unpublished_server(self, monkeypatch):
        def fail_to_open(_url: str) -> bool:
            raise RuntimeError("browser launch failed")

        monkeypatch.setattr(viewer_module.webbrowser, "open", fail_to_open)
        viewer = cesiumkit.Viewer()
        with pytest.raises(RuntimeError, match="browser launch failed"):
            viewer.show(open_browser=True)
        assert viewer._server is None
        assert viewer._server_tempdir is None
        assert viewer._session_token is None
        assert not viewer._closed

    def test_close_during_startup_never_serves_a_closed_socket(self, monkeypatch):
        viewer = cesiumkit.Viewer()
        entered_serve_forever = threading.Event()
        release_serve_forever = threading.Event()
        errors: list[BaseException] = []
        original_serve_forever = socketserver.BaseServer.serve_forever

        def delayed_serve_forever(server, *args, **kwargs):
            entered_serve_forever.set()
            assert release_serve_forever.wait(2)
            return original_serve_forever(server, *args, **kwargs)

        monkeypatch.setattr(socketserver.BaseServer, "serve_forever", delayed_serve_forever)

        def run_show() -> None:
            try:
                viewer.show(port=0, open_browser=False)
            except BaseException as exc:  # pragma: no cover - asserted below
                errors.append(exc)

        show_thread = threading.Thread(target=run_show)
        show_thread.start()
        assert entered_serve_forever.wait(2)

        close_thread = threading.Thread(target=viewer.close)
        close_thread.start()
        try:
            time.sleep(0.05)
            assert close_thread.is_alive()
            release_serve_forever.set()
            close_thread.join(timeout=2)
            show_thread.join(timeout=2)
            assert not close_thread.is_alive()
            assert not show_thread.is_alive()
            assert errors == []
        finally:
            release_serve_forever.set()
            viewer.close()
            close_thread.join(timeout=2)
            show_thread.join(timeout=2)

    def test_close_drains_accepted_handlers_before_resource_cleanup(self):
        class BlockingRaster:
            def __init__(self) -> None:
                self.entered = threading.Event()
                self.release = threading.Event()
                self.close_calls = 0

            def tile(self, _z: int, _x: int, _y: int) -> bytes:
                self.entered.set()
                if not self.release.wait(timeout=2):
                    raise TimeoutError("test did not release the raster request")
                return _ONE_PIXEL_PNG

            def close(self) -> None:
                self.close_calls += 1

        viewer = cesiumkit.Viewer()
        raster = BlockingRaster()
        viewer._raster_sources["blocked"] = raster
        close_errors: list[BaseException] = []
        request_errors: list[BaseException] = []
        with running_viewer(viewer) as (viewer, base_url):
            tempdir = viewer._server_tempdir
            assert tempdir is not None
            tempdir_path = Path(tempdir.name)

            def fetch_blocked_tile() -> None:
                try:
                    status, body = request(f"{base_url}/raster/blocked/0/0/0.png")
                    assert status == 200
                    assert body == _ONE_PIXEL_PNG
                except BaseException as exc:  # pragma: no cover - asserted below
                    request_errors.append(exc)

            request_thread = threading.Thread(target=fetch_blocked_tile)
            request_thread.start()
            assert raster.entered.wait(timeout=2)

            def request_close() -> None:
                try:
                    viewer.close()
                except BaseException as exc:  # pragma: no cover - asserted below
                    close_errors.append(exc)

            close_thread = threading.Thread(target=request_close)
            close_thread.start()
            try:
                close_thread.join(timeout=0.1)
                assert close_thread.is_alive()
                assert tempdir_path.exists()
                assert raster.close_calls == 0
            finally:
                raster.release.set()
            close_thread.join(timeout=2)
            request_thread.join(timeout=2)
            assert not close_thread.is_alive()
            assert not request_thread.is_alive()
            assert close_errors == []
            assert request_errors == []
            for _ in range(100):
                if not tempdir_path.exists():
                    break
                time.sleep(0.01)
            assert not tempdir_path.exists()
            assert raster.close_calls == 1

    def test_close_from_click_handler_defers_drain_until_handler_returns(self):
        viewer = cesiumkit.Viewer()
        viewer.on_click(lambda _entity_id: viewer.close())
        with running_viewer(viewer) as (viewer, base_url):
            token = viewer._session_token
            tempdir = viewer._server_tempdir
            assert token is not None
            assert tempdir is not None
            tempdir_path = Path(tempdir.name)
            status, _ = request(
                f"{base_url}/__cesiumkit_result",
                method="POST",
                body=json.dumps({"token": token, "event": "click", "result": None}).encode(),
                headers={"Content-Type": "application/json", "X-CesiumKit-Token": token},
            )
            assert status == 200
            for _ in range(100):
                if not tempdir_path.exists():
                    break
                time.sleep(0.01)
            assert not tempdir_path.exists()

    def test_close_is_idempotent_and_cleans_server_tempdir(self):
        viewer = cesiumkit.Viewer()
        with running_viewer(viewer) as (viewer, _):
            tempdir = viewer._server_tempdir
            assert tempdir is not None
            tempdir_path = Path(tempdir.name)
            assert tempdir_path.is_dir()
        assert viewer._server is None
        assert not tempdir_path.exists()
        viewer.close()
        with pytest.raises(RuntimeError, match="closed"):
            viewer.show(open_browser=False)

    def test_context_manager_closes_owned_rasters_once(self):
        class ClosableRaster:
            def __init__(self) -> None:
                self.calls = 0

            def close(self) -> None:
                self.calls += 1

        raster = ClosableRaster()
        with cesiumkit.Viewer() as viewer:
            viewer._raster_sources["test"] = raster
        assert raster.calls == 1
        viewer.close()
        assert raster.calls == 1

    def test_concurrent_close_waits_for_resource_cleanup(self):
        class BlockingRaster:
            def __init__(self) -> None:
                self.entered = threading.Event()
                self.release = threading.Event()
                self.close_calls = 0

            def close(self) -> None:
                self.close_calls += 1
                self.entered.set()
                if not self.release.wait(timeout=2):
                    raise TimeoutError("test did not release raster cleanup")

        viewer = cesiumkit.Viewer()
        raster = BlockingRaster()
        viewer._raster_sources["blocked"] = raster
        errors: list[BaseException] = []

        def request_close() -> None:
            try:
                viewer.close()
            except BaseException as exc:  # pragma: no cover - asserted below
                errors.append(exc)

        first_close = threading.Thread(target=request_close)
        second_close = threading.Thread(target=request_close)
        first_close.start()
        assert raster.entered.wait(timeout=2)
        second_close.start()
        try:
            second_close.join(timeout=0.1)
            assert second_close.is_alive()
        finally:
            raster.release.set()
        first_close.join(timeout=2)
        second_close.join(timeout=2)
        assert not first_close.is_alive()
        assert not second_close.is_alive()
        assert errors == []
        assert raster.close_calls == 1

    def test_close_finishes_cleanup_when_a_raster_close_fails(self):
        class FailingRaster:
            def __init__(self) -> None:
                self.close_calls = 0

            def close(self) -> None:
                self.close_calls += 1
                raise RuntimeError("raster cleanup failed")

        class ClosableRaster:
            def __init__(self) -> None:
                self.close_calls = 0

            def close(self) -> None:
                self.close_calls += 1

        viewer = cesiumkit.Viewer()
        failing_raster = FailingRaster()
        closable_raster = ClosableRaster()
        viewer._raster_sources["failing"] = failing_raster
        viewer._raster_sources["closable"] = closable_raster
        tempdir = tempfile.TemporaryDirectory()
        tempdir_path = Path(tempdir.name)
        viewer._server_tempdir = tempdir
        viewer._pending_runtime_ids.add("pending")

        with pytest.raises(RuntimeError, match="raster cleanup failed"):
            viewer.close()

        assert failing_raster.close_calls == 1
        assert closable_raster.close_calls == 1
        assert not tempdir_path.exists()
        assert viewer._runtime_errors["pending"] == "Viewer closed"
        viewer.close()
        assert failing_raster.close_calls == 1
        assert closable_raster.close_calls == 1

    def test_show_rejects_duplicate_server(self):
        with running_viewer(cesiumkit.Viewer()) as (viewer, _):
            with pytest.raises(RuntimeError, match="already being shown"):
                viewer.show(open_browser=False)
