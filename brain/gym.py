"""Independent food and synthetic gym cue learning feeding one neural network."""

from brain.learning import MushroomBodyLearning
from brain.network import NeuralNetwork
from brain.sensory import BrainAdapter
from simulation.signals import LearningSnapshot, NeuralSnapshot, SensoryFrame


class GymBrainAdapter:
    """Cue-specific salience affects sensory encoding, never the motor readout."""

    def __init__(self, network: NeuralNetwork, food_learning: MushroomBodyLearning,
                 gym_learning: MushroomBodyLearning, learning_enabled: bool = True) -> None:
        self.network = network
        self.food_learning = food_learning
        self.gym_learning = gym_learning
        self.learning_enabled = learning_enabled
        self.food_adapter = BrainAdapter(network, food_learning if learning_enabled else None)

    def step(self, sensory: SensoryFrame, hunger: float, gym_odor: tuple[float, float]) -> NeuralSnapshot:
        self.food_learning.recall(smell_left=sensory.smell_left, smell_right=sensory.smell_right)
        self.gym_learning.recall(smell_left=gym_odor[0], smell_right=gym_odor[1])
        encoded = self.food_adapter.encode(sensory, hunger)
        gain = self.gym_learning.learned_salience if self.learning_enabled else 1.0
        for channel, value in zip(('gym_left', 'gym_right'), gym_odor, strict=True):
            for body_id in self.network.circuit.sensory_inputs[channel]:
                encoded[body_id] = min(1.0, value * gain)
        return self.network.step(encoded)

    def learn(self, food_reward: float, gym_reward: float, gym_sets: int = 1) -> LearningSnapshot:
        if not self.learning_enabled:
            return LearningSnapshot(reward=food_reward)
        food = self.food_learning.reinforce(food_reward)
        for _ in range(gym_sets):
            self.gym_learning.reinforce(gym_reward)
        return LearningSnapshot(food.reward, food.association_strength, food.mean_eligibility,
                                food.active_kcs, food.changed)
