"""Gym observer using the existing same-origin routes and connection lifecycle."""

import asyncio
from collections.abc import Callable
from dataclasses import asdict
from aiohttp import web

from frontend.gym_telemetry import gym_frame_message, parse_gym_command
from frontend.server import ObservatoryConfig, ObservatoryServer, create_app
from frontend.telemetry import TelemetryProtocolError
from simulation.gym import GymSimulation


class GymObservatoryServer(ObservatoryServer):
    """Apply count at the next clock boundary, including while physics is paused."""

    def __init__(self, simulation: GymSimulation, config: ObservatoryConfig,
                 persist_memory: Callable[[], None] | None = None) -> None:
        if config.backend != 'compact':
            raise ValueError('Gym requires the compact backend')
        super().__init__(simulation, config, persist_memory)
        self._schema = 3 if simulation.equipment is not None else 2
        self._latest_frame = gym_frame_message(simulation.snapshot(), schema=self._schema)

    def _hello_message(self) -> dict[str, object]:
        message = super()._hello_message()
        equipment = self.simulation.equipment
        message.update(schema=self._schema, experiment='gym', population=self.simulation.population,
                       station=asdict(self.simulation.station))
        if equipment is not None:
            message['equipment'] = [asdict(station) for station in equipment.stations]
        return message

    async def health(self, request: web.Request) -> web.Response:
        return web.json_response({'status': 'ready', 'schema': self._schema, 'backend': self.config.backend,
            'dataset': self.config.dataset, 'experiment': 'gym', 'population': self.simulation.population})

    async def _send_additional_initial_state(self, socket: web.WebSocketResponse) -> None:
        await socket.send_json({'type': 'population', 'count': self.simulation.population})

    async def _handle_command(self, socket: web.WebSocketResponse, text: str) -> None:
        try:
            kind, value = parse_gym_command(text)
        except TelemetryProtocolError:
            await self._send_command_error(socket)
            return
        if kind == 'population':
            self.simulation.request_population(value)
            return
        self.running = value
        await self._broadcast({'type': 'running', 'running': self.running})

    async def _send_command_error(self, socket: web.WebSocketResponse) -> None:
        await socket.send_json({'type': 'error', 'code': 'invalid_command',
                                'message': 'تعداد مگس‌ها را از ۱ تا ۱۰ وارد کنید.'})

    async def clock(self) -> None:
        loop = asyncio.get_running_loop()
        interval = 1.0 / self.config.fps
        deadline = loop.time() + interval
        saved_rewards = self._reward_events()
        while True:
            await asyncio.sleep(max(0.0, deadline - loop.time()))
            population_changed = self.simulation.apply_pending_population()
            if self.running:
                self.simulation.step(interval)
            if self.running or population_changed:
                self._latest_frame = gym_frame_message(self.simulation.snapshot(), schema=self._schema)
            # Complete the state boundary before yielding to another command handler.
            if population_changed:
                await self._broadcast({'type': 'population', 'count': self.simulation.population})
            if self.running or population_changed:
                await self._broadcast(self._latest_frame)
            rewards = self._reward_events()
            if rewards != saved_rewards and self.persist_memory is not None:
                try:
                    self.persist_memory()
                    saved_rewards = rewards
                except OSError:
                    self.running = False
                    await self._broadcast({'type': 'running', 'running': False})
                    await self._broadcast({'type': 'error', 'code': 'memory_save_failed',
                                          'message': 'ذخیره نشد؛ فضای دیسک را بررسی کنید.'})
            deadline += interval
            if deadline < loop.time() - interval:
                deadline = loop.time() + interval

    def _reward_events(self) -> int:
        return sum(fly.brain.food_learning.memory.reward_events + fly.brain.gym_learning.memory.reward_events
                   for fly in self.simulation.bank)


def create_gym_app(*, simulation: GymSimulation, config: ObservatoryConfig,
                   persist_memory: Callable[[], None] | None = None) -> web.Application:
    """Serve the composition's gym schema with the same-origin restrictions."""
    return create_app(simulation=simulation, config=config, persist_memory=persist_memory,
                      server_type=GymObservatoryServer)
