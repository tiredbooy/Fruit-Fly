import asyncio
import json
from pathlib import Path
import tempfile
import unittest

from aiohttp.test_utils import TestClient, TestServer
from aiohttp import WSServerHandshakeError

from brain.gym_circuit import load_gym_circuits
from experiments.experiment_002 import create_gym
from frontend.gym_server import GymObservatoryServer, create_gym_app
from frontend.gym_telemetry import gym_frame_message, parse_gym_command
from frontend.server import ObservatoryConfig, create_app
from frontend.telemetry import TelemetryProtocolError, parse_client_command
from simulation.gym import GymSimulation

ROOT = Path(__file__).resolve().parents[2]


class GymProtocolTest(unittest.TestCase):
    def test_strict_population_command_and_schema_one_rejection(self):
        self.assertEqual(('population', 3), parse_gym_command('{"type":"set_population","count":3}'))
        for count in [True, 1.0, '2', None, 0, 11, float('nan')]:
            with self.assertRaises(TelemetryProtocolError):
                parse_gym_command(json.dumps({'type': 'set_population', 'count': count}))
        for text in ['{}', '[]', 'x' * 1025, '{"type":"set_population","count":1,"x":2}']:
            with self.assertRaises(TelemetryProtocolError):
                parse_gym_command(text)
        with self.assertRaises(TelemetryProtocolError):
            parse_client_command('{"type":"set_population","count":2}')


class GymServerTest(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.circuits = load_gym_circuits(ROOT)

    async def asyncSetUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        path = Path(self.temporary.name)
        (path / 'index.html').write_text('<main>gym</main>')
        self.gym = create_gym(*self.circuits, seed=7)
        self.client = TestClient(TestServer(create_gym_app(simulation=self.gym,
            config=ObservatoryConfig('compact', 'male-cns:v1.0', 30, path))))
        await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()
        self.temporary.cleanup()

    async def receive(self, socket, kind):
        for _ in range(20):
            message = await socket.receive_json(timeout=2)
            if message['type'] == kind:
                return message
        self.fail(f'Missing {kind}')

    async def test_real_http_ws_paused_population_and_reconnect_snapshot(self):
        self.assertEqual(200, (await self.client.get('/')).status)
        health = await (await self.client.get('/health')).json()
        self.assertEqual(3, health['schema'])
        socket = await self.client.ws_connect('/ws')
        hello = await self.receive(socket, 'hello')
        self.assertEqual('gym', hello['experiment'])
        self.assertEqual(3, hello['schema'])
        self.assertEqual(1, hello['population'])
        self.assertIn('resistance', hello['station'])
        self.assertEqual(10, len(hello['equipment']))
        self.assertEqual({'id', 'kind', 'x', 'y', 'heading', 'load', 'travel', 'grip_radius'},
                         set(hello['equipment'][0]))
        self.assertEqual('bench_press', hello['equipment'][0]['kind'])
        self.assertEqual('bicep_curl', hello['equipment'][1]['kind'])
        initial = await self.receive(socket, 'gym_frame')
        self.assertEqual(3, initial['schema'])
        self.assertEqual(1, initial['flies'][0]['frame']['schema'])
        self.assertEqual({'station_id', 'kind', 'phase', 'joint_position', 'joint_velocity',
            'repetitions', 'completed_sets', 'rep_in_set', 'recovery_remaining',
            'body_elevation', 'body_pitch', 'body_roll'}, set(initial['flies'][0]['exercise']))
        await socket.send_json({'type': 'set_running', 'running': False})
        self.assertFalse((await self.receive(socket, 'running'))['running'])
        step = self.gym.step_count
        await socket.send_json({'type': 'set_population', 'count': 3})
        self.assertEqual(3, (await self.receive(socket, 'population'))['count'])
        updated = await self.receive(socket, 'gym_frame')
        self.assertEqual(['fly-1', 'fly-2', 'fly-3'], [f['id'] for f in updated['flies']])
        await asyncio.sleep(.08)
        self.assertEqual(step, self.gym.step_count)
        observer = await self.client.ws_connect('/ws')
        self.assertEqual(3, (await self.receive(observer, 'hello'))['population'])
        self.assertFalse((await self.receive(observer, 'running'))['running'])
        self.assertEqual(3, (await self.receive(observer, 'population'))['count'])
        self.assertEqual(step, (await self.receive(observer, 'gym_frame'))['step'])
        await socket.send_json({'type': 'set_population', 'count': True})
        self.assertEqual('invalid_command', (await self.receive(socket, 'error'))['code'])
        await socket.close()
        await observer.close()

    async def test_same_origin_is_required(self):
        with self.assertRaises(WSServerHandshakeError):
            await self.client.ws_connect('/ws', headers={'Origin': 'https://bad.example'})

    async def test_legacy_lane_server_preserves_schema_two_for_health_hello_and_live_frames(self):
        await self.client.close()
        legacy = GymSimulation(self.gym.environment, self.gym.bank, 1)
        self.client = TestClient(TestServer(create_gym_app(simulation=legacy,
            config=ObservatoryConfig('compact', 'male-cns:v1.0', 30, Path(self.temporary.name)))))
        await self.client.start_server()
        health = await (await self.client.get('/health')).json()
        self.assertEqual(2, health['schema'])
        socket = await self.client.ws_connect('/ws')
        hello = await self.receive(socket, 'hello')
        self.assertEqual(2, hello['schema'])
        self.assertIn('station', hello)
        self.assertNotIn('equipment', hello)
        initial = await self.receive(socket, 'gym_frame')
        live = await self.receive(socket, 'gym_frame')
        self.assertGreater(live['step'], initial['step'])
        for frame in (initial, live):
            self.assertEqual(2, frame['schema'])
            self.assertEqual(1, frame['flies'][0]['frame']['schema'])
            self.assertNotIn('exercise', frame['flies'][0])
        self.assertGreater(live['flies'][0]['training']['total_work'], 0)
        await socket.close()

    async def test_command_arriving_during_population_broadcast_gets_its_own_ack(self):
        await self.client.close()
        broadcasting = asyncio.Event()
        release_broadcast = asyncio.Event()

        class ScheduledServer(GymObservatoryServer):
            async def _broadcast(self, message):
                if message.get('type') == 'population' and message.get('count') == 2:
                    broadcasting.set()
                    await release_broadcast.wait()
                await super()._broadcast(message)

        self.client = TestClient(TestServer(create_app(simulation=self.gym,
            config=ObservatoryConfig('compact', 'male-cns:v1.0', 30, Path(self.temporary.name)),
            server_type=ScheduledServer)))
        await self.client.start_server()
        socket = await self.client.ws_connect('/ws')
        await self.receive(socket, 'running')
        await self.receive(socket, 'population')
        await socket.send_json({'type': 'set_population', 'count': 2})
        await asyncio.wait_for(broadcasting.wait(), timeout=2)
        try:
            await socket.send_json({'type': 'set_population', 'count': 3})
            # Same socket ordering proves the count command was handled during the held broadcast.
            await socket.send_json({'type': 'set_running', 'running': True})
            await self.receive(socket, 'running')
        finally:
            release_broadcast.set()
        self.assertEqual(2, (await self.receive(socket, 'population'))['count'])
        self.assertEqual(3, (await self.receive(socket, 'population'))['count'])
        self.assertEqual(3, self.gym.population)
        await socket.close()
