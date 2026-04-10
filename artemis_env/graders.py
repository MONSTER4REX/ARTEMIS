from typing import Any, Dict, List, Tuple
from .models import (
    EpisodeState,
    GroundTruth,
    SOCAction,
)

SCORE_FLOOR = 0.01
SCORE_CEIL = 0.99

class FalsePositiveGrader:
    def __init__(self, state: EpisodeState):
        self.state = state
        self.ground_truth = state.scenario.ground_truth
        
    def grade(self) -> float:
        fps_to_dismiss = set(self.ground_truth.false_positives)
        resolved = set(self.state.resolved_alerts)
        
        correct_fps = len(fps_to_dismiss.intersection(resolved))
        incorrect_threats = len(set(self.ground_truth.real_threats).intersection(resolved))
        
        total_fps = max(1, len(fps_to_dismiss))
        base_score = (correct_fps / total_fps) * 0.7
        bonus = min(0.3, len(self.state.fetched_log_keys) * 0.1)
        penalty = incorrect_threats * 0.5
        
        return max(SCORE_FLOOR, min(SCORE_CEIL, base_score + bonus - penalty))

class BruteForceGrader:
    def __init__(self, state: EpisodeState):
        self.state = state
        self.ground_truth = state.scenario.ground_truth
        
    def grade(self) -> float:
        attackers = set(self.ground_truth.attacker_ips)
        compromised = set(self.ground_truth.compromised_users)
        
        blocked_ips = set(self.state.blocked_ips)
        isolated_users = set(self.state.isolated_users)
        
        correct_ips = len(attackers.intersection(blocked_ips))
        incorrect_ips = len(blocked_ips - attackers)
        
        correct_users = len(compromised.intersection(isolated_users))
        incorrect_users = len(isolated_users - compromised)
        
        ip_score = (correct_ips / max(1, len(attackers))) * 0.5
        user_score = (correct_users / max(1, len(compromised))) * 0.5
        penalty = (incorrect_ips + incorrect_users) * 0.2
        
        return max(SCORE_FLOOR, min(SCORE_CEIL, ip_score + user_score - penalty))

class LateralMovementGrader:
    def __init__(self, state: EpisodeState):
        self.state = state
        self.ground_truth = state.scenario.ground_truth
        
    def grade(self) -> float:
        attackers = set(self.ground_truth.attacker_ips)
        compromised = set(self.ground_truth.compromised_users)
        
        blocked_ips = set(self.state.blocked_ips)
        isolated_users = set(self.state.isolated_users)
        
        correct_ips = len(attackers.intersection(blocked_ips))
        correct_users = len(compromised.intersection(isolated_users))
        
        logs_score = min(0.4, len(self.state.fetched_log_keys) * 0.1)
        action_score = (correct_ips > 0) * 0.3 + (correct_users > 0) * 0.3
        
        return max(SCORE_FLOOR, min(SCORE_CEIL, logs_score + action_score))

def compute_final_score(state: EpisodeState) -> float:
    task_name = state.scenario.task_name
    if task_name == "false_positive_triage":
        return FalsePositiveGrader(state).grade()
    elif task_name == "brute_force_defense":
        return BruteForceGrader(state).grade()
    elif task_name == "lateral_movement_detection":
        return LateralMovementGrader(state).grade()
    
    # Fallback default grader
    cumulative_reward = sum(r.get("reward", 0.0) for r in state.actions_taken)
    max_possible_reward = max(1, len(state.actions_taken)) * 1.5
    score = cumulative_reward / max_possible_reward
    return max(SCORE_FLOOR, min(SCORE_CEIL, score))