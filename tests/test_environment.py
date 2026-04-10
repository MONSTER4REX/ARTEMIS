import pytest
from artemis_env.environment import SOCEnv
from artemis_env.models import (
    ActionType,
    AlertStatus,
    SOCAction,
)
@pytest.fixture
def env():
    return SOCEnv()
def test_deterministic_reset(env):
    res1 = env.reset(task="false_positive_triage", seed=42)
    res2 = env.reset(task="false_positive_triage", seed=42)
    assert res1.episode_id != res2.episode_id
    alerts1 = [a.id for a in res1.observation.current_alerts]
    alerts2 = [a.id for a in res2.observation.current_alerts]
    assert alerts1 == alerts2
    assert len(res1.observation.alert_context.login_history) == len(res2.observation.alert_context.login_history)
def test_invalid_action_penalty(env):
    res = env.reset(task="false_positive_triage", seed=42)
    eid = res.episode_id
    action = SOCAction(
        action_type=ActionType.RESOLVE_ALERT,
        reason="No alert ID provided"
    )
    step_res = env.step(eid, action)
    assert step_res.reward == -0.5
    assert step_res.error is not None
    assert "alert_id is required" in step_res.error
    assert env.active_episodes[eid].current_step == 1
def test_correct_resolve_reward(env):
    res = env.reset(task="false_positive_triage", seed=42)
    eid = res.episode_id
    action = SOCAction(
        action_type=ActionType.RESOLVE_ALERT,
        alert_id="alert_001_sql_injection",
        reason="Internal testing server identified in context."
    )
    step_res = env.step(eid, action)
    assert step_res.reward == 1.0
    assert "Correctly dismissed" in step_res.info["action_explanation"]
    resolved_alert = next(a for a in step_res.observation.current_alerts if a.id == "alert_001_sql_injection")
    assert resolved_alert.status == AlertStatus.RESOLVED
def test_max_steps_termination(env):
    res = env.reset(task="false_positive_triage", seed=42)
    eid = res.episode_id
    for i in range(8):
        action = SOCAction(
            action_type=ActionType.FETCH_LOGS,
            ip_address="10.0.0.50",
            reason=f"Investigating step {i+1}"
        )
        step_res = env.step(eid, action)
        if i < 7:
            assert step_res.done is False
        else:
            assert step_res.done is True
def test_isolate_attacker_reward(env):
    res = env.reset(task="brute_force_defense", seed=42)
    eid = res.episode_id
    action = SOCAction(
        action_type=ActionType.ISOLATE_IP,
        ip_address="203.0.113.1",
        reason="Identified as source of coordinated brute force."
    )
    step_res = env.step(eid, action)
    assert step_res.reward == 1.2
    assert "203.0.113.1" in step_res.observation.system_status.blocked_ips