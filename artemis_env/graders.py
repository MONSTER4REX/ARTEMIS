from typing import Any, Dict, List, Tuple
from .models import (
    EpisodeState,
    GroundTruth,
    SOCAction,
)

SCORE_FLOOR = 0.01
SCORE_CEIL = 0.99

class TaskGrader:
    def __init__(self, scenario_ground_truth: GroundTruth):
        self.ground_truth = scenario_ground_truth
    def grade(self, action_history: List[Dict[str, Any]]) -> float:
        cumulative_reward = 0.0
        step_count = len(action_history)
        if step_count == 0:
            return SCORE_FLOOR
        for record in action_history:
            reward = record.get("reward", 0.0)
            cumulative_reward += reward
        max_possible_reward = step_count * 1.5
        score = cumulative_reward / max_possible_reward
        return max(SCORE_FLOOR, min(SCORE_CEIL, score))
def compute_final_score(state: EpisodeState) -> float:
    grader = TaskGrader(state.scenario.ground_truth)
    return grader.grade(state.actions_taken)