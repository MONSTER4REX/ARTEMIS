from typing import Any, Dict, List, Tuple
from .models import (
    EpisodeState,
    GroundTruth,
    SOCAction,
)
class TaskGrader:
    def __init__(self, scenario_ground_truth: GroundTruth):
        self.ground_truth = scenario_ground_truth
    def grade(self, action_history: List[Dict[str, Any]]) -> float:
        cumulative_reward = 0.0
        step_count = len(action_history)
        if step_count == 0:
            return 0.0
        for record in action_history:
            reward = record.get("reward", 0.0)
            cumulative_reward += reward
        max_possible_reward = step_count * 1.5
        score = cumulative_reward / max_possible_reward
        return max(0.0, min(1.0, score))
def compute_final_score(state: EpisodeState) -> float:
    grader = TaskGrader(state.scenario.ground_truth)
    return grader.grade(state.actions_taken)