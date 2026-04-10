from typing import Dict, List, Tuple
from .models import (
    ActionType,
    EpisodeState,
    GroundTruth,
    Reward,
    SOCAction,
)
def compute_reward(action: SOCAction, state: EpisodeState) -> Reward:
    ground_truth = state.scenario.ground_truth
    action_reward = 0.0
    explanation = ""
    if action.action_type == ActionType.RESOLVE_ALERT:
        if action.alert_id in ground_truth.false_positives:
            action_reward = 1.0
            explanation = f"Correctly dismissed false positive alert '{action.alert_id}'."
        elif action.alert_id in ground_truth.real_threats:
            action_reward = -0.5
            explanation = f"Incorrectly dismissed real threat alert '{action.alert_id}'."
        elif ground_truth.is_ambiguous and action.alert_id in [a.id for a in state.scenario.initial_alerts]:
            action_reward = 0.5
            explanation = f"Resolved ambiguous alert '{action.alert_id}' based on travel context."
        else:
            action_reward = 0.0
            explanation = f"Resolved existing alert '{action.alert_id}'."
    elif action.action_type == ActionType.ISOLATE_IP:
        if action.ip_address in ground_truth.attacker_ips:
            action_reward = 1.0
            if state.current_step <= 3:
                action_reward += 0.2
                explanation = f"Fast isolation of malicious attacker IP '{action.ip_address}' (Bonus +0.2)."
            else:
                explanation = f"Correctly isolated malicious attacker IP '{action.ip_address}'."
        else:
            action_reward = -0.3
            explanation = f"Incorrectly isolated legitimate IP '{action.ip_address}' (False Positive Isolation)."
    elif action.action_type == ActionType.ISOLATE_USER:
        if action.user_id in ground_truth.compromised_users:
            action_reward = 1.0
            explanation = f"Correctly isolated compromised user account '{action.user_id}'."
        else:
            action_reward = -0.3
            explanation = f"Incorrectly isolated legitimate user account '{action.user_id}'."
    elif action.action_type == ActionType.FETCH_LOGS:
        is_relevant = False
        log_key = f"{action.ip_address}:{action.user_id}:{action.file_path}"
        if log_key not in state.fetched_log_keys:
            if action.ip_address in ground_truth.relevant_ips:
                is_relevant = True
            if action.user_id in ground_truth.relevant_users:
                is_relevant = True
            if action.file_path in ground_truth.relevant_files:
                is_relevant = True
            if is_relevant:
                action_reward = 0.3
                explanation = f"Fetched relevant evidence for investigation (IP: {action.ip_address}, User: {action.user_id}, File: {action.file_path})."
                state.fetched_log_keys.append(log_key)
            else:
                action_reward = 0.1
                explanation = f"Fetched additional logs for investigation."
        else:
            action_reward = 0.0
            explanation = f"Already fetched these logs."
    elif action.action_type == ActionType.ESCALATE_TO_HUMAN:
        if ground_truth.is_ambiguous:
            action_reward = 0.8
            explanation = f"Correctly escalated genuinely ambiguous scenario to human analyst."
        else:
            action_reward = 0.3
            explanation = f"Escalated investigation to human (safe but less efficient than correct action)."
    time_penalty = 0.0
    if state.current_step > 8:
        time_penalty = -0.1
    total_reward = action_reward + time_penalty
    return Reward(
        action_reward=action_reward,
        step_number=state.current_step,
        time_penalty=time_penalty,
        total_reward=total_reward,
        explanation=explanation
    )