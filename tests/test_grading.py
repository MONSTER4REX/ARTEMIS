import pytest
from artemis_env.environment import SOCEnv
from artemis_env.models import ActionType, SOCAction
from artemis_env.graders import compute_final_score

@pytest.fixture
def env():
    return SOCEnv()

def test_perfect_easy_task(env):
    res = env.reset(task="false_positive_triage", seed=42)
    eid = res.episode_id
    
    env.step(eid, SOCAction(
        action_type=ActionType.RESOLVE_ALERT,
        alert_id="alert_001_sql_injection",
        reason="Testing source IP."
    ))
    env.step(eid, SOCAction(
        action_type=ActionType.RESOLVE_ALERT,
        alert_id="alert_002_shodan",
        reason="Known research scanner."
    ))
    
    state = env.active_episodes[eid]
    score = compute_final_score(state)
    assert score > 0.8

def test_poor_performance_score(env):
    res = env.reset(task="brute_force_defense", seed=42)
    eid = res.episode_id
    
    env.step(eid, SOCAction(
        action_type=ActionType.RESOLVE_ALERT,
        alert_id="alert_004_brute_force",
        reason="Incorrectly resolving real threat."
    ))
    
    state = env.active_episodes[eid]
    score = compute_final_score(state)
    assert score == 0.0

def test_medium_task_isolation(env):
    res = env.reset(task="brute_force_defense", seed=42)
    eid = res.episode_id
    
    env.step(eid, SOCAction(
        action_type=ActionType.ISOLATE_IP,
        ip_address="203.0.113.1",
        reason="Malicious source."
    ))
    
    state = env.active_episodes[eid]
    score = compute_final_score(state)
    assert score > 0.5
