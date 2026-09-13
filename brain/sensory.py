"""Map physical sensor channels onto official MaleCNS sensory body IDs."""

from __future__ import annotations

from brain.modulation import hunger_odor_gain
from brain.learning import MushroomBodyLearning
from brain.network import ConnectomeNetwork
from brain.memory import MemoryState
from simulation.signals import LearningSnapshot, NeuralSnapshot, RewardSignal, SensoryFrame


class BrainAdapter:
    def __init__(
        self,
        network: ConnectomeNetwork,
        learning: MushroomBodyLearning | None = None,
    ) -> None:
        self.network = network
        self.learning = learning

    def encode(self, sensory: SensoryFrame, hunger: float) -> dict[int, float]:
        learned_salience = self.learning.learned_salience if self.learning else 1.0
        gain = hunger_odor_gain(hunger) * learned_salience
        channels = {
            "smell_left": min(1.0, sensory.smell_left * gain),
            "smell_right": min(1.0, sensory.smell_right * gain),
            "vision_left": sensory.vision_left,
            "vision_right": sensory.vision_right,
        }
        encoded: dict[int, float] = {}
        for channel, value in channels.items():
            for body_id in self.network.circuit.sensory_inputs.get(channel, ()):
                encoded[body_id] = value
        return encoded

    def step(self, sensory: SensoryFrame, hunger: float) -> NeuralSnapshot:
        if self.learning is not None:
            self.learning.recall(
                smell_left=sensory.smell_left,
                smell_right=sensory.smell_right,
            )
        return self.network.step(self.encode(sensory, hunger))

    def learn(self, reward: RewardSignal) -> LearningSnapshot:
        if self.learning is None:
            return LearningSnapshot(reward=reward.amount)
        state = self.learning.reinforce(reward.amount)
        return LearningSnapshot(
            reward=state.reward,
            association_strength=state.association_strength,
            mean_eligibility=state.mean_eligibility,
            active_kcs=state.active_kcs,
            changed=state.changed,
        )

    @property
    def memory(self) -> MemoryState | None:
        return self.learning.memory if self.learning else None
