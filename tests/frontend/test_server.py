import asyncio
from pathlib import Path
import random
import tempfile
import unittest

from aiohttp import WSMsgType, WSServerHandshakeError
from aiohttp.test_utils import TestClient, TestServer

from brain.network import ConnectomeNetwork, RuntimeCircuit, RuntimeNode
from brain.readout import MotorReadout
from brain.sensory import BrainAdapter
from frontend.server import ObservatoryConfig, create_app
from simulation.loop import Simulation
from world.environment import Environment
from world.fly import FlyBody, Physiology
from world.food import FoodSpawnConfig, FoodSpawner
from world.sensors import SensorRig


class ObservatoryServerTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.dist = Path(self.temporary.name)
        (self.dist / "assets").mkdir()
        (self.dist / "index.html").write_text("<main>observatory</main>")
        self.simulation = self._simulation()
        app = create_app(
            simulation=self.simulation,
            config=ObservatoryConfig(
                backend="compact",
                dataset="male-cns:v1.0",
                fps=30.0,
                dist_path=self.dist,
            ),
        )
        self.client = TestClient(TestServer(app))
        await self.client.start_server()

    async def asyncTearDown(self) -> None:
        await self.client.close()
        self.temporary.cleanup()

    async def test_health_reports_the_authoritative_runtime(self) -> None:
        response = await self.client.get("/health")

        self.assertEqual(200, response.status)
        self.assertEqual(
            {
                "status": "ready",
                "schema": 1,
                "backend": "compact",
                "dataset": "male-cns:v1.0",
            },
            await response.json(),
        )

    async def test_websocket_sends_hello_and_live_frame(self) -> None:
        socket = await self.client.ws_connect("/ws")

        hello = await socket.receive_json(timeout=1.0)
        frame = await socket.receive_json(timeout=1.0)

        self.assertEqual("hello", hello["type"])
        self.assertEqual("compact", hello["backend"])
        self.assertEqual("frame", frame["type"])
        self.assertGreaterEqual(frame["step"], 1)
        await socket.close()

    async def test_pause_and_resume_change_only_the_simulation_clock(self) -> None:
        socket = await self.client.ws_connect("/ws")
        await socket.receive_json(timeout=1.0)
        await socket.send_json({"type": "set_running", "running": False})
        state = await self._receive_type(socket, "running")
        paused_step = self.simulation.step_count

        await asyncio.sleep(0.09)

        self.assertFalse(state["running"])
        self.assertEqual(paused_step, self.simulation.step_count)
        await socket.send_json({"type": "set_running", "running": True})
        resumed = await self._receive_type(socket, "running")
        await asyncio.sleep(0.09)
        self.assertTrue(resumed["running"])
        self.assertGreater(self.simulation.step_count, paused_step)
        await socket.close()

    async def test_invalid_command_returns_error_event(self) -> None:
        socket = await self.client.ws_connect("/ws")
        await socket.receive_json(timeout=1.0)

        await socket.send_str('{"type":"set_motor","turn":1}')
        error = await self._receive_type(socket, "error")

        self.assertEqual("invalid_command", error["code"])
        await socket.close()

    async def test_cross_origin_websocket_is_rejected(self) -> None:
        with self.assertRaises(WSServerHandshakeError) as captured:
            await self.client.ws_connect(
                "/ws",
                headers={"Origin": "https://malicious.example"},
            )

        self.assertEqual(403, captured.exception.status)

    async def _receive_type(self, socket, expected: str) -> dict[str, object]:
        for _ in range(10):
            message = await socket.receive(timeout=1.0)
            self.assertEqual(WSMsgType.TEXT, message.type)
            document = message.json()
            if document.get("type") == expected:
                return document
        self.fail(f"WebSocket did not produce {expected}")

    def _simulation(self) -> Simulation:
        circuit = RuntimeCircuit(
            dataset="male-cns:v1.0",
            nodes=(RuntimeNode(1, "ORN_DM1", "L", "acetylcholine"),),
            edges=(),
            sensory_inputs={
                "smell_left": (1,),
                "smell_right": (),
                "vision_left": (),
                "vision_right": (),
            },
            motor_roles={},
        )
        environment = Environment(
            20.0,
            12.0,
            None,
            food_spawner=FoodSpawner(
                random.Random(7),
                FoodSpawnConfig(minimum_spawn_delay=1.0, maximum_spawn_delay=1.0),
            ),
        )
        return Simulation(
            environment=environment,
            body=FlyBody(0.0, 0.0, 0.0),
            physiology=Physiology(hunger=0.5),
            sensors=SensorRig(),
            brain=BrainAdapter(ConnectomeNetwork(circuit)),
            readout=MotorReadout(),
        )


class ObservatoryAssetValidationTest(unittest.TestCase):
    def test_missing_frontend_build_has_an_actionable_error(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        path = Path(temporary.name) / "missing"

        with self.assertRaisesRegex(FileNotFoundError, "make frontend-build"):
            create_app(
                simulation=ObservatoryServerTest._simulation(self),
                config=ObservatoryConfig(
                    backend="compact",
                    dataset="male-cns:v1.0",
                    fps=10.0,
                    dist_path=path,
                ),
            )


if __name__ == "__main__":
    unittest.main()
