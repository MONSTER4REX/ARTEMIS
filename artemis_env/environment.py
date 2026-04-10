import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from .graders import compute_final_score
from .models import (
    ActionType,
    AlertStatus,
    AlertType,
    EpisodeState,
    GroundTruth,
    ResetResult,
    Scenario,
    SOCObservation,
    SOCAction,
    StepResult,
    SystemStatus,
    TaskDifficulty,
)
from .reward_engine import compute_reward
from .scenarios import get_scenario
from .validators import validate_action
class SOCEnv:
    def __init__(self):
        self.active_episodes: Dict[str, EpisodeState] = {}
        self.max_episodes = 500
    def reset(self, task: Optional[str] = None, seed: Optional[int] = None) -> ResetResult:
        self._cleanup_stale_episodes()
        scenario = get_scenario(task_name=task, seed=seed)
        episode_id = f"ep_{uuid.uuid4().hex[:12]}"
        state = EpisodeState(
            episode_id=episode_id,
            scenario=scenario
        )
        self.active_episodes[episode_id] = state
        obs = self._build_observation(state)
        return ResetResult(
            observation=obs,
            done=False,
            episode_id=episode_id
        )
    def step(self, episode_id: str, action: SOCAction) -> StepResult:
        if episode_id not in self.active_episodes:
            return StepResult(
                observation=self._empty_observation(),
                reward=0.0,
                done=True,
                error=f"Episode ID '{episode_id}' not found. It may have expired."
            )
        state = self.active_episodes[episode_id]
        state.last_accessed_at = datetime.now(timezone.utc)
        state.current_step += 1
        if state.done or state.current_step > state.scenario.max_steps:
             state.done = True
             final_score = compute_final_score(state)
             return StepResult(
                observation=self._build_observation(state),
                reward=0.0,
                done=True,
                score=final_score,
                info={"message": "Episode already finished."}
            )
        is_valid, error_msg = validate_action(action, state)
        if not is_valid:
            state.actions_taken.append({
                "step": state.current_step,
                "action": action.model_dump(),
                "reward": -0.5,
                "valid": False,
                "error": error_msg
            })
            return StepResult(
                observation=self._build_observation(state),
                reward=-0.5,
                done=False,
                error=error_msg
            )
        reward_detail = compute_reward(action, state)
        reward_val = reward_detail.total_reward
        self._apply_action_effects(action, state)
        state.actions_taken.append({
            "step": state.current_step,
            "action": action.model_dump(),
            "reward": reward_val,
            "explanation": reward_detail.explanation,
            "valid": True
        })
        state.rewards.append(reward_val)
        if self._is_task_complete(state):
            state.done = True
        final_score = compute_final_score(state) if state.done else None
        return StepResult(
            observation=self._build_observation(state),
            reward=reward_val,
            done=state.done,
            score=final_score,
            info={
                "action_explanation": reward_detail.explanation,
                "step_reward": reward_val
            }
        )
    def get_state(self, episode_id: str) -> Dict[str, Any]:
        if episode_id not in self.active_episodes:
            return None
        state = self.active_episodes[episode_id]
        final_score = compute_final_score(state) if state.done else None
        return {
            "episode_id": episode_id,
            "task_name": state.scenario.task_name,
            "step_count": state.current_step,
            "actions_taken": state.actions_taken,
            "cumulative_reward": sum(state.rewards),
            "score": final_score,
            "done": state.done,
            "current_observation": self._build_observation(state),
        }
    def _apply_action_effects(self, action: SOCAction, state: EpisodeState):
        if action.action_type == ActionType.RESOLVE_ALERT:
            state.resolved_alerts.append(action.alert_id)
        elif action.action_type == ActionType.ISOLATE_IP:
            state.blocked_ips.append(action.ip_address)
        elif action.action_type == ActionType.ISOLATE_USER:
            state.isolated_users.append(action.user_id)
    def _build_observation(self, state: EpisodeState) -> SOCObservation:
        visible_alerts = []
        for alert in state.scenario.initial_alerts:
            final_alert = alert.model_copy()
            if alert.id in state.resolved_alerts:
                final_alert.status = AlertStatus.RESOLVED
            elif alert.source_ip in state.blocked_ips:
                final_alert.status = AlertStatus.ISOLATED
            visible_alerts.append(final_alert)
        sys_status = SystemStatus(
            blocked_ips=state.blocked_ips,
            isolated_users=state.isolated_users,
            resolved_alert_count=len(state.resolved_alerts),
            active_incidents=len(state.scenario.ground_truth.real_threats) - len(set(state.resolved_alerts) & set(state.scenario.ground_truth.real_threats))
        )
        return SOCObservation(
            current_alerts=visible_alerts,
            alert_context=state.scenario.context_data,
            system_status=sys_status,
            step_count=state.current_step,
            episode_id=state.episode_id,
            task_name=state.scenario.task_name,
            task_difficulty=state.scenario.task_difficulty,
            time_elapsed=(datetime.now(timezone.utc) - state.created_at).total_seconds()
        )
    def _empty_observation(self) -> SOCObservation:
        return SOCObservation(
            current_alerts=[],
            alert_context=AlertContextData(),
            system_status=SystemStatus()
        )
    def _is_task_complete(self, state: EpisodeState) -> bool:
        if state.current_step >= state.scenario.max_steps:
             return True
        real_threats = set(state.scenario.ground_truth.real_threats)
        if real_threats and real_threats.issubset(set(state.resolved_alerts)):
            return True
        return False
    def _cleanup_stale_episodes(self):
        now = datetime.now(timezone.utc)
        to_delete = []
        for eid, estate in self.active_episodes.items():
            if (now - estate.last_accessed_at).total_seconds() > 3600:
                to_delete.append(eid)
        for eid in to_delete:
            del self.active_episodes[eid]
        if len(self.active_episodes) > self.max_episodes:
             sorted_episodes = sorted(self.active_episodes.items(), key=lambda x: x[1].created_at)
             for i in range(len(sorted_episodes) - self.max_episodes):
                 del self.active_episodes[sorted_episodes[i][0]]