import cProfile
import unittest

from brain.network import ConnectomeNetwork, RuntimeCircuit, RuntimeEdge, RuntimeNode
from brain.sensory import BrainAdapter
from simulation.signals import SensoryFrame


class ConnectomeNetworkTest(unittest.TestCase):
    def setUp(self) -> None:
        circuit = RuntimeCircuit(
            dataset="male-cns:v1.0",
            nodes=(
                RuntimeNode(1, "ORN_DM1", "L", "acetylcholine"),
                RuntimeNode(2, "interneuron", "L", "gaba"),
                RuntimeNode(3, "DNp09", "L", "acetylcholine"),
                RuntimeNode(4, "DNa02", "L", "acetylcholine"),
                RuntimeNode(5, "DNa02", "R", "acetylcholine"),
            ),
            edges=(
                RuntimeEdge(1, 3, 50),
                RuntimeEdge(1, 4, 30),
                RuntimeEdge(2, 5, 40),
            ),
            sensory_inputs={"smell_left": (1,), "smell_right": (), "vision_left": (), "vision_right": ()},
            motor_roles={"forward_left": 3, "steering_high_left": 4, "steering_high_right": 5},
        )
        self.network = ConnectomeNetwork(circuit)

    def test_real_edge_weights_propagate_activity_to_named_motor_roles(self) -> None:
        snapshot = self.network.step({1: 1.0}, substeps=2)

        self.assertGreater(snapshot.activity_by_role["forward_left"], 0.0)
        self.assertGreater(snapshot.activity_by_role["steering_high_left"], 0.0)

    def test_hunger_scales_odor_input_without_a_behavior_threshold(self) -> None:
        adapter = BrainAdapter(self.network)
        sensory = SensoryFrame(smell_left=0.4, smell_right=0.0, vision_left=0.0, vision_right=0.0)

        low = adapter.encode(sensory, hunger=0.0)
        high = adapter.encode(sensory, hunger=1.0)

        self.assertGreater(high[1], low[1])
        self.assertGreater(low[1], 0.0)

    def test_steps_do_not_repeat_static_weight_logarithms(self) -> None:
        profile = cProfile.Profile()
        with profile:
            self.network.step({1: 0.6})
            self.network.step({1: 0.4})

        logarithms = sum(
            entry.callcount for entry in profile.getstats()
            if isinstance(entry.code, str) and "math.log1p" in entry.code
        )
        self.assertEqual(0, logarithms)


if __name__ == "__main__":
    unittest.main()
