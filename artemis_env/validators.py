from typing import Optional, Tuple
from .models import (
    ActionType,
    AlertStatus,
    EpisodeState,
    SOCAction,
)
def validate_action(action: SOCAction, state: EpisodeState) -> Tuple[bool, Optional[str]]:
    if action.action_type == ActionType.RESOLVE_ALERT:
        if not action.alert_id:
            return False, "alert_id is required for resolve_alert actions."
        alert_exists = any(a.id == action.alert_id for a in state.scenario.initial_alerts)
        if not alert_exists:
            return False, f"Alert ID '{action.alert_id}' not found in current scenario."
        if action.alert_id in state.resolved_alerts:
            return False, f"Alert '{action.alert_id}' has already been resolved."
    elif action.action_type == ActionType.ISOLATE_IP:
        if not action.ip_address:
            return False, "ip_address is required for isolate_ip actions."
        relevant_ip = False
        if any(a.source_ip == action.ip_address for a in state.scenario.initial_alerts):
            relevant_ip = True
        if any(l.ip_address == action.ip_address for l in state.scenario.context_data.login_history):
            relevant_ip = True
        if not relevant_ip:
             return False, f"IP address '{action.ip_address}' is not found in alerts or logs."
        if action.ip_address in state.blocked_ips:
            return False, f"IP address '{action.ip_address}' is already blocked."
    elif action.action_type == ActionType.ISOLATE_USER:
        if not action.user_id:
            return False, "user_id is required for isolate_user actions."
        relevant_user = False
        if any(a.source_user == action.user_id for a in state.scenario.initial_alerts):
            relevant_user = True
        if any(l.user == action.user_id for l in state.scenario.context_data.login_history):
            relevant_user = True
        if any(l.user == action.user_id for l in state.scenario.context_data.file_access_logs):
            relevant_user = True
        if not relevant_user:
            return False, f"User ID '{action.user_id}' not found in alerts or logs."
        if action.user_id in state.isolated_users:
            return False, f"User account '{action.user_id}' is already isolated."
    elif action.action_type == ActionType.FETCH_LOGS:
        if not any([action.ip_address, action.user_id, action.file_path]):
            return False, "At least one parameter (ip_address, user_id, or file_path) is required for fetch_logs."
    elif action.action_type == ActionType.ESCALATE_TO_HUMAN:
        if action.severity is None:
            return False, "severity (1-5) is required for escalate_to_human actions."
    return True, None