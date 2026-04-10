from __future__ import annotations
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple
from pydantic import BaseModel, Field, field_validator
class AlertType(str, Enum):
    SQL_INJECTION = "SQL_Injection"
    BRUTE_FORCE = "Brute_Force"
    UNAUTHORIZED_LOGIN = "Unauthorized_Login"
    FILE_ACCESS_ANOMALY = "File_Access_Anomaly"
    LATERAL_MOVEMENT = "Lateral_Movement"
class AlertStatus(str, Enum):
    UNRESOLVED = "unresolved"
    ISOLATED = "isolated"
    RESOLVED = "resolved"
class ActionType(str, Enum):
    RESOLVE_ALERT = "resolve_alert"
    ISOLATE_IP = "isolate_ip"
    ISOLATE_USER = "isolate_user"
    FETCH_LOGS = "fetch_logs"
    ESCALATE_TO_HUMAN = "escalate_to_human"
class TaskDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
class SecurityAlert(BaseModel):
    id: str = Field(..., description="Unique alert identifier, e.g. 'alert_001_sql_injection'")
    alert_type: AlertType = Field(..., description="Category of the alert")
    severity: int = Field(..., ge=1, le=5, description="Severity 1 (low) to 5 (critical)")
    source_ip: str = Field(..., description="IPv4 address of the alert source")
    destination_ip: str = Field(..., description="IPv4 address or resource identifier of the target")
    source_user: Optional[str] = Field(None, description="Username if applicable")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the alert was triggered",
    )
    alert_context: str = Field(..., description="Human-readable description of what happened")
    failed_attempts: Optional[int] = Field(None, description="Number of failed attempts (brute-force)")
    time_window: Optional[str] = Field(None, description="Temporal window for the event, e.g. '5 minutes'")
    status: AlertStatus = Field(default=AlertStatus.UNRESOLVED, description="Current triage status")
    model_config = {"use_enum_values": True}
class LoginRecord(BaseModel):
    timestamp: datetime
    user: str
    ip_address: str
    success: bool
    location: Optional[str] = None
class FileAccessRecord(BaseModel):
    timestamp: datetime
    user: str
    file_path: str
    action: str
class AlertContextData(BaseModel):
    login_history: List[LoginRecord] = Field(default_factory=list)
    file_access_logs: List[FileAccessRecord] = Field(default_factory=list)
    network_traffic: Dict[str, Any] = Field(default_factory=dict)
    anomalies: List[str] = Field(default_factory=list)
class SystemStatus(BaseModel):
    blocked_ips: List[str] = Field(default_factory=list)
    isolated_users: List[str] = Field(default_factory=list)
    resolved_alert_count: int = 0
    active_incidents: int = 0
class SOCObservation(BaseModel):
    current_alerts: List[SecurityAlert]
    alert_context: AlertContextData
    system_status: SystemStatus
    step_count: int = 0
    episode_id: str = ""
    task_name: str = ""
    task_difficulty: TaskDifficulty = TaskDifficulty.EASY
    time_elapsed: float = 0.0
    model_config = {"use_enum_values": True}
class SOCAction(BaseModel):
    action_type: ActionType = Field(..., description="Which action to perform")
    alert_id: Optional[str] = Field(None, description="Required for resolve_alert")
    ip_address: Optional[str] = Field(None, description="Required for isolate_ip")
    user_id: Optional[str] = Field(None, description="Required for isolate_user")
    file_path: Optional[str] = Field(None, description="Optional for fetch_logs")
    reason: str = Field(..., min_length=1, description="Justification for the action")
    severity: Optional[int] = Field(None, ge=1, le=5, description="Required for escalate_to_human")
    model_config = {"use_enum_values": True}
    @field_validator("severity")
    @classmethod
    def escalation_requires_severity(cls, v: Optional[int], info) -> Optional[int]:
        data = info.data
        if data.get("action_type") == ActionType.ESCALATE_TO_HUMAN and v is None:
            raise ValueError("severity is required for escalate_to_human actions")
        return v
class Reward(BaseModel):
    action_reward: float = Field(..., description="Base reward for the action")
    step_number: int = Field(..., ge=0)
    time_penalty: float = Field(default=0.0, description="Penalty for steps > 8")
    total_reward: float = Field(..., description="action_reward + time_penalty")
    explanation: str = Field(..., description="Human-readable reward rationale")
class ResetRequest(BaseModel):
    task: Optional[str] = Field(None, description="Task name; random if omitted")
    seed: Optional[int] = Field(None, description="RNG seed for reproducibility")
class ResetResult(BaseModel):
    observation: SOCObservation
    done: bool = False
    episode_id: str
class StepRequest(BaseModel):
    episode_id: str = Field(..., description="Episode to act in")
    action: SOCAction
class StepResult(BaseModel):
    observation: SOCObservation
    reward: float = Field(..., ge=-1.0, le=1.5)
    done: bool
    info: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
class StateRequest(BaseModel):
    episode_id: str
class StateResult(BaseModel):
    episode_id: str
    task_name: str
    step_count: int
    actions_taken: List[Dict[str, Any]] = Field(default_factory=list)
    cumulative_reward: float = 0.0
    current_observation: SOCObservation
class GroundTruth(BaseModel):
    false_positives: List[str] = Field(default_factory=list, description="Alert IDs that are false positives")
    real_threats: List[str] = Field(default_factory=list, description="Alert IDs that are genuine threats")
    attacker_ips: List[str] = Field(default_factory=list, description="Known attacker IP addresses")
    compromised_users: List[str] = Field(default_factory=list, description="Known compromised user accounts")
    lateral_movement_chain: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Ordered chain of lateral-movement events (hard task)",
    )
    optimal_actions: List[str] = Field(
        default_factory=list,
        description="Sequence of ideal action_types the agent should take",
    )
    is_ambiguous: bool = Field(default=False, description="Whether the scenario has genuinely ambiguous alerts")
    relevant_ips: List[str] = Field(default_factory=list, description="IPs relevant to the investigation")
    relevant_users: List[str] = Field(default_factory=list, description="Users relevant to the investigation")
    relevant_files: List[str] = Field(default_factory=list, description="File paths relevant to the investigation")
class Scenario(BaseModel):
    scenario_id: str = Field(default_factory=lambda: f"sc_{uuid.uuid4().hex[:12]}")
    task_name: str
    task_difficulty: TaskDifficulty
    description: str
    initial_alerts: List[SecurityAlert]
    context_data: AlertContextData
    ground_truth: GroundTruth
    max_steps: int = Field(default=8, description="Maximum steps before episode auto-terminates")
    model_config = {"use_enum_values": True}
class EpisodeState(BaseModel):
    episode_id: str = Field(default_factory=lambda: f"ep_{uuid.uuid4().hex[:12]}")
    scenario: Scenario
    current_step: int = 0
    actions_taken: List[Dict[str, Any]] = Field(default_factory=list)
    rewards: List[float] = Field(default_factory=list)
    blocked_ips: List[str] = Field(default_factory=list)
    isolated_users: List[str] = Field(default_factory=list)
    resolved_alerts: List[str] = Field(default_factory=list)
    done: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    fetched_log_keys: List[str] = Field(
        default_factory=list,
        description="Track which log fetches have been performed to avoid duplicate rewards",
    )
    model_config = {"use_enum_values": True}