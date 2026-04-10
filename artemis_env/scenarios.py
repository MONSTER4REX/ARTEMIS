import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from .models import (
    AlertContextData,
    AlertStatus,
    AlertType,
    FileAccessRecord,
    GroundTruth,
    LoginRecord,
    Scenario,
    SecurityAlert,
    TaskDifficulty,
)
def get_scenario(task_name: Optional[str] = None, seed: Optional[int] = None) -> Scenario:
    if seed is not None:
        random.seed(seed)
    task_map = {
        "false_positive_triage": create_easy_scenario,
        "brute_force_defense": create_medium_scenario,
        "lateral_movement_detection": create_hard_scenario,
    }
    if not task_name or task_name not in task_map:
        task_name = random.choice(list(task_map.keys()))
    return task_map[task_name](seed)
def create_easy_scenario(seed: Optional[int] = None) -> Scenario:
    now = datetime.now(timezone.utc)
    alert1 = SecurityAlert(
        id="alert_001_sql_injection",
        alert_type=AlertType.SQL_INJECTION,
        severity=4,
        source_ip="10.0.0.50",
        destination_ip="10.0.0.100",
        alert_context="SQL Injection attempt detected in HTTP POST parameters: 'OR 1=1--'",
        timestamp=now - timedelta(minutes=15),
        status=AlertStatus.UNRESOLVED
    )
    alert2 = SecurityAlert(
        id="alert_002_shodan",
        alert_type=AlertType.BRUTE_FORCE,
        severity=3,
        source_ip="192.0.2.1",
        destination_ip="203.0.113.10",
        alert_context="Multiple failed login attempts from a known research scanner IP (Shodan).",
        timestamp=now - timedelta(minutes=10),
        status=AlertStatus.UNRESOLVED,
        failed_attempts=5,
        time_window="1 minute"
    )
    alert3 = SecurityAlert(
        id="alert_003_travel_login",
        alert_type=AlertType.UNAUTHORIZED_LOGIN,
        severity=3,
        source_ip="203.0.203.0",
        destination_ip="172.16.0.5",
        source_user="james_smith",
        alert_context="Successful login from an unusual geo-location (Shanghai, CN).",
        timestamp=now - timedelta(minutes=5),
        status=AlertStatus.UNRESOLVED
    )
    context = AlertContextData(
        login_history=[
            LoginRecord(timestamp=now - timedelta(days=1), user="james_smith", ip_address="24.1.2.3", success=True, location="San Francisco, US"),
            LoginRecord(timestamp=now - timedelta(minutes=5), user="james_smith", ip_address="203.0.203.0", success=True, location="Shanghai, CN"),
        ],
        anomalies=[
            "Source 10.0.0.50 belongs to 'SEC-TEST-VLAN' (Internal Pentest Team).",
            "IP 192.0.2.1 is identified as Shodan.io research crawler in global threat feed.",
            "User 'james_smith' has 'Business Travel' status active through April 10."
        ]
    )
    ground_truth = GroundTruth(
        false_positives=["alert_001_sql_injection", "alert_002_shodan"],
        real_threats=[],
        is_ambiguous=True,
        relevant_ips=["10.0.0.50", "192.0.2.1", "203.0.203.0"],
        relevant_users=["james_smith"]
    )
    return Scenario(
        task_name="false_positive_triage",
        task_difficulty=TaskDifficulty.EASY,
        description="Filter obvious false positives from a dashboard.",
        initial_alerts=[alert1, alert2, alert3],
        context_data=context,
        ground_truth=ground_truth
    )
def create_medium_scenario(seed: Optional[int] = None) -> Scenario:
    now = datetime.now(timezone.utc)
    attacker_ips = ["203.0.113.1", "203.0.113.2", "203.0.113.3", "203.0.113.4"]
    alert1 = SecurityAlert(
        id="alert_004_brute_force",
        alert_type=AlertType.BRUTE_FORCE,
        severity=5,
        source_ip="203.0.113.0/24",
        destination_ip="203.0.113.100",
        alert_context="Coordinated brute force attack detected from multiple source IPs in 203.0.113.0/24 subnet targeting admin account.",
        timestamp=now - timedelta(minutes=7),
        status=AlertStatus.UNRESOLVED,
        failed_attempts=15,
        time_window="5 minutes"
    )
    alert2 = SecurityAlert(
        id="alert_005_successful_login",
        alert_type=AlertType.UNAUTHORIZED_LOGIN,
        severity=4,
        source_ip="203.0.113.1",
        destination_ip="203.0.113.100",
        source_user="admin",
        alert_context="Successful login to 'admin' account from IP 203.0.113.1 following multiple failed attempts.",
        timestamp=now - timedelta(minutes=2),
        status=AlertStatus.UNRESOLVED
    )
    login_history = []
    for i, ip in enumerate(attacker_ips):
        for _ in range(3):
            login_history.append(LoginRecord(
                timestamp=now - timedelta(minutes=7-i),
                user="admin",
                ip_address=ip,
                success=False
            ))
    login_history.append(LoginRecord(
        timestamp=now - timedelta(minutes=2),
        user="admin",
        ip_address="203.0.113.1",
        success=True
    ))
    context = AlertContextData(
        login_history=sorted(login_history, key=lambda x: x.timestamp),
        anomalies=[
            "Multiple failed login attempts from same subnet within short window.",
            "Successful login from IP with prior failures."
        ]
    )
    ground_truth = GroundTruth(
        false_positives=[],
        real_threats=["alert_004_brute_force", "alert_005_successful_login"],
        attacker_ips=attacker_ips,
        compromised_users=["admin"],
        relevant_ips=attacker_ips,
        relevant_users=["admin"]
    )
    return Scenario(
        task_name="brute_force_defense",
        task_difficulty=TaskDifficulty.MEDIUM,
        description="Detect and respond to a coordinated multi-source Brute Force attack.",
        initial_alerts=[alert1, alert2],
        context_data=context,
        ground_truth=ground_truth
    )
def create_hard_scenario(seed: Optional[int] = None) -> Scenario:
    now = datetime.now(timezone.utc)
    alert1 = SecurityAlert(
        id="alert_006_unusual_login",
        alert_type=AlertType.UNAUTHORIZED_LOGIN,
        severity=3,
        source_ip="192.168.50.100",
        destination_ip="10.0.0.5",
        source_user="sarah_dev",
        alert_context="Successful login from unmanaged internal VPN IP 192.168.50.100.",
        timestamp=now - timedelta(minutes=25),
        status=AlertStatus.UNRESOLVED
    )
    alert2 = SecurityAlert(
        id="alert_007_file_access_anomaly",
        alert_type=AlertType.FILE_ACCESS_ANOMALY,
        severity=4,
        source_ip="10.0.0.5",
        destination_ip="FS-PROD-01",
        source_user="sarah_dev",
        alert_context="User 'sarah_dev' accessed '/production/configs/db_credentials.yaml' which is outside their normal scope.",
        timestamp=now - timedelta(minutes=15),
        status=AlertStatus.UNRESOLVED
    )
    alert3 = SecurityAlert(
        id="alert_008_lateral_movement",
        alert_type=AlertType.LATERAL_MOVEMENT,
        severity=5,
        source_ip="10.0.0.5",
        destination_ip="10.0.0.20 (Customer-DB)",
        source_user="admin_svc",
        alert_context="Lateral movement attempt: User 'sarah_dev' attempted psexec to 10.0.0.20 using 'admin_svc' credentials.",
        timestamp=now - timedelta(minutes=5),
        status=AlertStatus.UNRESOLVED
    )
    context = AlertContextData(
        login_history=[
            LoginRecord(timestamp=now - timedelta(minutes=25), user="sarah_dev", ip_address="192.168.50.100", success=True),
        ],
        file_access_logs=[
            FileAccessRecord(timestamp=now - timedelta(minutes=15), user="sarah_dev", file_path="/production/configs/db_credentials.yaml", action="download"),
        ],
        network_traffic={
            "10.0.0.5": "Unusual outbound connection to 10.0.0.20 on port 445 (SMB)."
        },
        anomalies=[
            "User 'sarah_dev' never accesses production DB credentials.",
            "Account 'admin_svc' credentials found in db_credentials.yaml.",
            "SMB traffic from dev workstation to production database is highly unusual."
        ]
    )
    ground_truth = GroundTruth(
        false_positives=[],
        real_threats=["alert_006_unusual_login", "alert_007_file_access_anomaly", "alert_008_lateral_movement"],
        attacker_ips=["192.168.50.100"],
        compromised_users=["sarah_dev"],
        relevant_ips=["192.168.50.100", "10.0.0.5", "10.0.0.20"],
        relevant_users=["sarah_dev", "admin_svc"],
        relevant_files=["/production/configs/db_credentials.yaml"],
        lateral_movement_chain=[
            {"stage": 1, "type": "Initial Access", "alert": "alert_006_unusual_login"},
            {"stage": 2, "type": "Credential Access", "alert": "alert_007_file_access_anomaly"},
            {"stage": 3, "type": "Lateral Movement", "alert": "alert_008_lateral_movement"},
        ]
    )
    return Scenario(
        task_name="lateral_movement_detection",
        task_difficulty=TaskDifficulty.HARD,
        description="Detect and respond to a multi-stage lateral movement attack.",
        initial_alerts=[alert1, alert2, alert3],
        context_data=context,
        ground_truth=ground_truth
    )