import random
import unittest

from brain.network import ConnectomeNetwork, RuntimeCircuit, RuntimeEdge, RuntimeNode
from brain.learning import LearningCircuit, LearningConfig, LearningEdge, MushroomBodyLearning
from brain.memory import MemoryState
from brain.readout import MotorReadout
from brain.sensory import BrainAdapter
from simulation.loop import Simulation
from world.environment import Environment
from world.fly import FlyBody, Physiology
from world.food import Food, FoodSpawnConfig, FoodSpawner
from world.sensors import SensorRig


class SimulationLoopTest(unittest.TestCase):
    def test_food_appears_only_after_the_spawn_delay(self) -> None:
        environment = Environment(
            20.0,
            12.0,
            None,
            food_spawner=FoodSpawner(
                random.Random(7),
                FoodSpawnConfig(
                    minimum_spawn_delay=0.2,
                    maximum_spawn_delay=0.2,
                    inaccessible_probability=0.0,
                    minimum_fly_distance=0.0,
                ),
            ),
        )
        simulation = self._simulation_without_learning(environment)

        waiting = simulation.step(0.1)
        spawned = simulation.step(0.1)

        self.assertIsNone(waiting.food)
        self.assertEqual(0.0, waiting.sensory.smell_left)
        self.assertIsNotNone(spawned.food)

    def test_eaten_dynamic_food_is_removed_after_one_reward(self) -> None:
        environment = Environment(
            20.0,
            12.0,
            Food(0.0, 0.0),
            food_spawner=FoodSpawner(
                random.Random(9),
                FoodSpawnConfig(
                    minimum_spawn_delay=1.0,
                    maximum_spawn_delay=1.0,
                ),
            ),
        )
        simulation = self._simulation_without_learning(environment)

        eaten = simulation.step(0.1)
        waiting = simulation.step(0.1)

        self.assertTrue(eaten.ate)
        self.assertEqual(1.0, eaten.learning.reward)
        self.assertIsNone(eaten.food)
        self.assertFalse(waiting.ate)
        self.assertEqual(0.0, waiting.learning.reward)

    def test_step_returns_real_telemetry_and_advances_the_body(self) -> None:
        circuit = RuntimeCircuit(
            dataset="male-cns:v1.0",
            nodes=(
                RuntimeNode(1, "ORN_DM1", "L", "acetylcholine"),
                RuntimeNode(2, "DNp09", "L", "acetylcholine"),
            ),
            edges=(RuntimeEdge(1, 2, 50),),
            sensory_inputs={"smell_left": (1,), "smell_right": (), "vision_left": (), "vision_right": ()},
            motor_roles={"forward_left": 2},
        )
        network = ConnectomeNetwork(circuit)
        simulation = Simulation(
            environment=Environment(20.0, 12.0, Food(3.0, 0.0)),
            body=FlyBody(0.0, 0.0, 0.0),
            physiology=Physiology(hunger=0.5),
            sensors=SensorRig(),
            brain=BrainAdapter(network),
            readout=MotorReadout(),
        )

        frame = simulation.step(0.1)

        self.assertEqual(1, frame.step)
        self.assertGreater(frame.body.x, 0.0)
        self.assertGreater(frame.sensory.smell_left, 0.0)
        self.assertIn("forward_left", frame.neural.activity_by_role)

    def test_food_contact_rewards_eligible_odor_memory_without_direct_motor_logic(self) -> None:
        runtime = RuntimeCircuit(
            dataset="male-cns:v1.0",
            nodes=(
                RuntimeNode(1, "ORN_DM1", "L", "acetylcholine"),
                RuntimeNode(2, "DNp09", "L", "acetylcholine"),
            ),
            edges=(RuntimeEdge(1, 2, 50),),
            sensory_inputs={"smell_left": (1,), "smell_right": (), "vision_left": (), "vision_right": ()},
            motor_roles={"forward_left": 2},
        )
        learning = LearningCircuit(
            dataset="male-cns:v1.0",
            source_weights_sha256="abc",
            projection_neurons={"L": 10, "R": 20},
            mbon01_neurons={"L": 100, "R": 200},
            pam01_neurons=(300,),
            pn_kc_edges=(LearningEdge(10, 11, 40), LearningEdge(20, 21, 40)),
            plastic_edges=(LearningEdge(11, 100, 20), LearningEdge(21, 200, 20)),
        )
        memory = MemoryState.fresh(
            dataset="male-cns:v1.0",
            weights_sha256="abc",
            model="pam01-kc-mbon01-v1",
            plastic_edges=((11, 100, 20), (21, 200, 20)),
        )
        learner = MushroomBodyLearning(
            learning,
            memory,
            LearningConfig(eligibility_decay=0.5, learning_rate=0.5, active_kc_fraction=1.0),
        )
        simulation = Simulation(
            environment=Environment(20.0, 12.0, Food(0.0, 0.0)),
            body=FlyBody(0.0, 0.0, 0.0, maximum_speed=0.0),
            physiology=Physiology(hunger=0.5),
            sensors=SensorRig(),
            brain=BrainAdapter(ConnectomeNetwork(runtime), learner),
            readout=MotorReadout(),
        )

        frame = simulation.step(0.1)

        self.assertTrue(frame.ate)
        self.assertEqual(1.0, frame.learning.reward)
        self.assertTrue(frame.learning.changed)
        self.assertGreater(frame.learning.association_strength, 0.0)

    def _simulation_without_learning(self, environment: Environment) -> Simulation:
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
        return Simulation(
            environment=environment,
            body=FlyBody(0.0, 0.0, 0.0, maximum_speed=0.0),
            physiology=Physiology(hunger=0.5),
            sensors=SensorRig(),
            brain=BrainAdapter(ConnectomeNetwork(circuit)),
            readout=MotorReadout(),
        )


if __name__ == "__main__":
    unittest.main()
