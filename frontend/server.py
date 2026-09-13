"""Same-origin HTTP and WebSocket observer around an existing simulation."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

from aiohttp import WSMsgType, web

from frontend.telemetry import (
    SCHEMA_VERSION,
    TelemetryProtocolError,
    frame_message,
    hello_message,
    parse_client_command,
)
from simulation.loop import Simulation


@dataclass(frozen=True, slots=True)
class ObservatoryConfig:
    backend: str
    dataset: str
    fps: float
    dist_path: Path

    def __post_init__(self) -> None:
        if self.backend not in {"compact", "full"}:
            raise ValueError("Unknown brain backend")
        if self.fps <= 0.0:
            raise ValueError("Frame rate must be greater than zero")


class ObservatoryServer:
    """Coordinate one simulation clock and its read-only browser observers."""

    def __init__(
        self,
        simulation: Simulation,
        config: ObservatoryConfig,
        persist_memory: Callable[[], None] | None = None,
    ) -> None:
        self.simulation = simulation
        self.config = config
        self.persist_memory = persist_memory
        self.running = True
        self._clients: set[web.WebSocketResponse] = set()
        self._latest_frame: dict[str, object] | None = None

    async def health(self, request: web.Request) -> web.Response:
        return web.json_response(
            {
                "status": "ready",
                "schema": SCHEMA_VERSION,
                "backend": self.config.backend,
                "dataset": self.config.dataset,
            }
        )

    async def index(self, request: web.Request) -> web.FileResponse:
        return web.FileResponse(self.config.dist_path / "index.html")

    async def favicon(self, request: web.Request) -> web.FileResponse:
        return web.FileResponse(self.config.dist_path / "favicon.svg")

    async def websocket(self, request: web.Request) -> web.WebSocketResponse:
        origin = request.headers.get("Origin")
        allowed_origins = {f"http://{request.host}", f"https://{request.host}"}
        if origin is not None and origin not in allowed_origins:
            raise web.HTTPForbidden(text="Cross-origin WebSocket access is forbidden")
        socket = web.WebSocketResponse(max_msg_size=1_024, heartbeat=30.0)
        await socket.prepare(request)
        self._clients.add(socket)
        await socket.send_json(self._hello_message())
        await socket.send_json({"type": "running", "running": self.running})
        await self._send_additional_initial_state(socket)
        if self._latest_frame is not None:
            await socket.send_json(self._latest_frame)
        try:
            async for message in socket:
                if message.type is WSMsgType.TEXT:
                    await self._handle_command(socket, message.data)
                elif message.type in {WSMsgType.ERROR, WSMsgType.CLOSE}:
                    break
                else:
                    await self._send_command_error(socket)
        finally:
            self._clients.discard(socket)
        return socket

    def _hello_message(self) -> dict[str, object]:
        return hello_message(
                backend=self.config.backend,
                dataset=self.config.dataset,
                fps=self.config.fps,
                world_width=self.simulation.environment.width,
                world_height=self.simulation.environment.height,
        )

    async def _send_additional_initial_state(self, socket: web.WebSocketResponse) -> None:
        pass

    async def clock(self) -> None:
        loop = asyncio.get_running_loop()
        interval = 1.0 / self.config.fps
        deadline = loop.time() + interval
        while True:
            await asyncio.sleep(max(0.0, deadline - loop.time()))
            if not self.running:
                deadline = loop.time() + interval
                continue
            frame = self.simulation.step(interval)
            if frame.learning.changed and self.persist_memory is not None:
                self.persist_memory()
            self._latest_frame = frame_message(frame)
            await self._broadcast(self._latest_frame)
            deadline += interval
            if deadline < loop.time() - interval:
                deadline = loop.time() + interval

    async def close(self) -> None:
        if self.persist_memory is not None:
            self.persist_memory()
        for socket in tuple(self._clients):
            await socket.close(code=1001, message=b"server shutdown")
        self._clients.clear()

    async def _handle_command(
        self,
        socket: web.WebSocketResponse,
        text: str,
    ) -> None:
        try:
            self.running = parse_client_command(text)
        except TelemetryProtocolError:
            await self._send_command_error(socket)
            return
        await self._broadcast({"type": "running", "running": self.running})

    async def _send_command_error(self, socket: web.WebSocketResponse) -> None:
        await socket.send_json(
            {
                "type": "error",
                "code": "invalid_command",
                "message": "Only pause and resume commands are accepted",
            }
        )

    async def _broadcast(self, message: dict[str, object]) -> None:
        for socket in tuple(self._clients):
            if socket.closed:
                self._clients.discard(socket)
                continue
            try:
                await socket.send_json(message)
            except (ConnectionResetError, BrokenPipeError):
                # A peer may disconnect after the closed check while the send yields.
                self._clients.discard(socket)


def create_app(
    *,
    simulation: Simulation,
    config: ObservatoryConfig,
    persist_memory: Callable[[], None] | None = None,
    server_type: type[ObservatoryServer] = ObservatoryServer,
) -> web.Application:
    index = config.dist_path / "index.html"
    if not index.is_file():
        raise FileNotFoundError("Browser assets are missing; run 'make frontend-build' first")

    server = server_type(simulation, config, persist_memory)
    app = web.Application(client_max_size=1_024)
    app.router.add_get("/health", server.health)
    app.router.add_get("/ws", server.websocket)
    app.router.add_get("/", server.index)
    favicon = config.dist_path / "favicon.svg"
    if favicon.is_file():
        app.router.add_get("/favicon.svg", server.favicon)
    assets = config.dist_path / "assets"
    if assets.is_dir():
        app.router.add_static("/assets/", assets, show_index=False)

    async def lifecycle(application: web.Application):
        task = asyncio.create_task(server.clock())
        yield
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        await server.close()

    app.cleanup_ctx.append(lifecycle)
    return app
