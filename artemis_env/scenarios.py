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
    if seed is None:
        seed = random.randint(0, 1000000)
    random.seed(seed)
    task_map = {
        "false_positive_triage": create_easy_scenario,
        "brute_force_defense": create_medium_scenario,
        "lateral_movement_detection": create_hard_scenario,
    }
    if not task_name or task_name not in task_map:
        task_name = random.choice(list(task_map.keys()))
    return task_map[task_name](seed)


# --- Tier 1: Easy Scenarios (False Positive Triage) ---

def create_easy_scenario_v0(now, seed) -> Scenario:
    alert1 = SecurityAlert(id="alert_001_sql_injection", alert_type=AlertType.SQL_INJECTION, severity=4, source_ip="10.0.0.50", destination_ip="10.0.0.100", alert_context="SQL Injection attempt: 'OR 1=1--'", timestamp=now - timedelta(minutes=15), status=AlertStatus.UNRESOLVED)
    alert2 = SecurityAlert(id="alert_002_shodan", alert_type=AlertType.BRUTE_FORCE, severity=3, source_ip="192.0.2.1", destination_ip="203.0.113.10", alert_context="Shodan research scanner.", timestamp=now - timedelta(minutes=10), status=AlertStatus.UNRESOLVED, failed_attempts=5, time_window="1 minute")
    alert3 = SecurityAlert(id="alert_003_travel_login", alert_type=AlertType.UNAUTHORIZED_LOGIN, severity=3, source_ip="203.0.203.0", destination_ip="172.16.0.5", source_user="james_smith", alert_context="Login from Shanghai.", timestamp=now - timedelta(minutes=5), status=AlertStatus.UNRESOLVED)
    context = AlertContextData(login_history=[LoginRecord(timestamp=now-timedelta(minutes=5), user="james_smith", ip_address="203.0.203.0", success=True)], anomalies=["10.0.0.50 is SEC-TEST-VLAN.", "192.0.2.1 is Shodan.", "james_smith is on travel."])
    gt = GroundTruth(false_positives=["alert_001_sql_injection", "alert_002_shodan"], real_threats=[], is_ambiguous=True, relevant_ips=["10.0.0.50", "192.0.2.1", "203.0.203.0"], relevant_users=["james_smith"])
    return Scenario(task_name="false_positive_triage", task_difficulty=TaskDifficulty.EASY, description="Filter obvious false positives.", initial_alerts=[alert1, alert2, alert3], context_data=context, ground_truth=gt)

def create_easy_scenario_v1(now, seed) -> Scenario:
    alert1 = SecurityAlert(id="alert_vpn_01", alert_type=AlertType.UNAUTHORIZED_LOGIN, severity=3, source_ip="10.8.0.2", destination_ip="10.0.0.5", source_user="alice_w", alert_context="VPN split-tunneling detected", timestamp=now - timedelta(minutes=15), status=AlertStatus.UNRESOLVED)
    alert2 = SecurityAlert(id="alert_data_exfil", alert_type=AlertType.FILE_ACCESS_ANOMALY, severity=5, source_ip="10.0.0.10", destination_ip="10.0.0.50", source_user="backup_svc", alert_context="Massive file read by backup service", timestamp=now - timedelta(minutes=5), status=AlertStatus.UNRESOLVED)
    context = AlertContextData(login_history=[], anomalies=["alice_w is allowed VPN split tunneling.", "backup_svc normally reads 100GB nightly."])
    gt = GroundTruth(false_positives=["alert_vpn_01", "alert_data_exfil"], real_threats=[], is_ambiguous=False, relevant_ips=["10.8.0.2", "10.0.0.10"], relevant_users=["alice_w", "backup_svc"])
    return Scenario(task_name="false_positive_triage", task_difficulty=TaskDifficulty.EASY, description="Filter obvious false positives (VPN & Backup).", initial_alerts=[alert1, alert2], context_data=context, ground_truth=gt)

def create_easy_scenario_v2(now, seed) -> Scenario:
    alert1 = SecurityAlert(id="alert_dev_scan", alert_type=AlertType.BRUTE_FORCE, severity=4, source_ip="10.10.10.10", destination_ip="10.0.0.100", alert_context="Nessus scan from Dev subnet.", timestamp=now - timedelta(minutes=15), status=AlertStatus.UNRESOLVED, failed_attempts=50)
    context = AlertContextData(anomalies=["10.10.10.10 is the authorized Nessus scanner."])
    gt = GroundTruth(false_positives=["alert_dev_scan"], real_threats=[], is_ambiguous=False, relevant_ips=["10.10.10.10"], relevant_users=[])
    return Scenario(task_name="false_positive_triage", task_difficulty=TaskDifficulty.EASY, description="Filter Nessus scan false positive.", initial_alerts=[alert1], context_data=context, ground_truth=gt)

def create_easy_scenario(seed: Optional[int] = None) -> Scenario:
    now = datetime.now(timezone.utc)
    v = (seed or 0) % 3
    if v == 0: return create_easy_scenario_v0(now, seed)
    if v == 1: return create_easy_scenario_v1(now, seed)
    return create_easy_scenario_v2(now, seed)


# --- Tier 2: Medium Scenarios (Brute Force Defense) ---

def create_medium_scenario_v0(now, seed) -> Scenario:
    attacker_ips = ["203.0.113.1", "203.0.113.2"]
    alert1 = SecurityAlert(id="alert_004_brute_force", alert_type=AlertType.BRUTE_FORCE, severity=5, source_ip="203.0.113.0/24", destination_ip="203.0.113.100", alert_context="Coordinated brute force.", timestamp=now - timedelta(minutes=7), status=AlertStatus.UNRESOLVED, failed_attempts=15)
    alert2 = SecurityAlert(id="alert_005_successful_login", alert_type=AlertType.UNAUTHORIZED_LOGIN, severity=4, source_ip="203.0.113.1", destination_ip="203.0.113.100", source_user="admin", alert_context="Successful login from attacker.", timestamp=now - timedelta(minutes=2), status=AlertStatus.UNRESOLVED)
    login_history = [LoginRecord(timestamp=now-timedelta(minutes=2), user="admin", ip_address="203.0.113.1", success=True)]
    context = AlertContextData(login_history=login_history, anomalies=["Multiple failed logins from subnet.", "Successful login from attacker IP."])
    gt = GroundTruth(false_positives=[], real_threats=["alert_004_brute_force", "alert_005_successful_login"], attacker_ips=attacker_ips, compromised_users=["admin"], relevant_ips=attacker_ips, relevant_users=["admin"])
    return Scenario(task_name="brute_force_defense", task_difficulty=TaskDifficulty.MEDIUM, description="Detect SSH brute force.", initial_alerts=[alert1, alert2], context_data=context, ground_truth=gt)

def create_medium_scenario_v1(now, seed) -> Scenario:
    attacker_ips = ["198.51.100.5"]
    alert1 = SecurityAlert(id="alert_rdp_spray", alert_type=AlertType.BRUTE_FORCE, severity=4, source_ip="198.51.100.5", destination_ip="10.0.0.200", alert_context="Password spraying against RDP.", timestamp=now - timedelta(minutes=10), status=AlertStatus.UNRESOLVED, failed_attempts=20)
    alert2 = SecurityAlert(id="alert_rdp_success", alert_type=AlertType.UNAUTHORIZED_LOGIN, severity=5, source_ip="198.51.100.5", destination_ip="10.0.0.200", source_user="hr_manager", alert_context="RDP login successful.", timestamp=now - timedelta(minutes=1), status=AlertStatus.UNRESOLVED)
    login_history = [LoginRecord(timestamp=now-timedelta(minutes=1), user="hr_manager", ip_address="198.51.100.5", success=True)]
    context = AlertContextData(login_history=login_history, anomalies=["Dictionary attack detected."])
    gt = GroundTruth(false_positives=[], real_threats=["alert_rdp_spray", "alert_rdp_success"], attacker_ips=attacker_ips, compromised_users=["hr_manager"], relevant_ips=attacker_ips, relevant_users=["hr_manager"])
    return Scenario(task_name="brute_force_defense", task_difficulty=TaskDifficulty.MEDIUM, description="Detect RDP password spray.", initial_alerts=[alert1, alert2], context_data=context, ground_truth=gt)

def create_medium_scenario_v2(now, seed) -> Scenario:
    attacker_ips = ["185.0.0.5"]
    alert1 = SecurityAlert(id="alert_cred_stuffing", alert_type=AlertType.BRUTE_FORCE, severity=5, source_ip="185.0.0.5", destination_ip="10.0.0.50", alert_context="Credential stuffing via leaked DB.", timestamp=now - timedelta(minutes=5), status=AlertStatus.UNRESOLVED, failed_attempts=100)
    context = AlertContextData(login_history=[], anomalies=["Large volume of logins for non-existent users."])
    gt = GroundTruth(false_positives=[], real_threats=["alert_cred_stuffing"], attacker_ips=attacker_ips, compromised_users=[], relevant_ips=attacker_ips, relevant_users=[])
    return Scenario(task_name="brute_force_defense", task_difficulty=TaskDifficulty.MEDIUM, description="Detect credential stuffing.", initial_alerts=[alert1], context_data=context, ground_truth=gt)

def create_medium_scenario(seed: Optional[int] = None) -> Scenario:
    now = datetime.now(timezone.utc)
    v = (seed or 0) % 3
    if v == 0: return create_medium_scenario_v0(now, seed)
    if v == 1: return create_medium_scenario_v1(now, seed)
    return create_medium_scenario_v2(now, seed)


# --- Tier 3: Hard Scenarios (Lateral Movement Detection) ---

def create_hard_scenario_v0(now, seed) -> Scenario:
    alert1 = SecurityAlert(id="alert_006_unusual_login", alert_type=AlertType.UNAUTHORIZED_LOGIN, severity=3, source_ip="192.168.50.100", destination_ip="10.0.0.5", source_user="sarah_dev", alert_context="VPN login.", timestamp=now - timedelta(minutes=25), status=AlertStatus.UNRESOLVED)
    alert2 = SecurityAlert(id="alert_007_file_access", alert_type=AlertType.FILE_ACCESS_ANOMALY, severity=4, source_ip="10.0.0.5", destination_ip="FS-PROD-01", source_user="sarah_dev", alert_context="Accessed db_credentials.yaml", timestamp=now - timedelta(minutes=15), status=AlertStatus.UNRESOLVED)
    alert3 = SecurityAlert(id="alert_008_lat_move", alert_type=AlertType.LATERAL_MOVEMENT, severity=5, source_ip="10.0.0.5", destination_ip="10.0.0.20", source_user="admin_svc", alert_context="psexec attempt.", timestamp=now - timedelta(minutes=5), status=AlertStatus.UNRESOLVED)
    context = AlertContextData(
        login_history=[LoginRecord(timestamp=now - timedelta(minutes=25), user="sarah_dev", ip_address="192.168.50.100", success=True)],
        file_access_logs=[FileAccessRecord(timestamp=now - timedelta(minutes=15), user="sarah_dev", file_path="/production/configs/db_credentials.yaml", action="download")],
        anomalies=["User never accesses prod DB configs."]
    )
    gt = GroundTruth(false_positives=[], real_threats=["alert_006_unusual_login", "alert_007_file_access", "alert_008_lat_move"], attacker_ips=["192.168.50.100"], compromised_users=["sarah_dev"], relevant_ips=["192.168.50.100", "10.0.0.5"], relevant_users=["sarah_dev", "admin_svc"], relevant_files=["/production/configs/db_credentials.yaml"])
    return Scenario(task_name="lateral_movement_detection", task_difficulty=TaskDifficulty.HARD, description="Detect multi-stage lateral movement.", initial_alerts=[alert1, alert2, alert3], context_data=context, ground_truth=gt)

def create_hard_scenario_v1(now, seed) -> Scenario:
    alert1 = SecurityAlert(id="alert_supply_01", alert_type=AlertType.UNAUTHORIZED_LOGIN, severity=4, source_ip="172.16.0.50", destination_ip="10.0.0.10", source_user="vendor_acct", alert_context="Login from third-party vendor network.", timestamp=now - timedelta(minutes=40), status=AlertStatus.UNRESOLVED)
    alert2 = SecurityAlert(id="alert_supply_02", alert_type=AlertType.LATERAL_MOVEMENT, severity=5, source_ip="10.0.0.10", destination_ip="10.0.0.15", source_user="sysadmin", alert_context="SSH pivot from vendor gateway to core router.", timestamp=now - timedelta(minutes=10), status=AlertStatus.UNRESOLVED)
    context = AlertContextData(
        login_history=[LoginRecord(timestamp=now - timedelta(minutes=40), user="vendor_acct", ip_address="172.16.0.50", success=True)],
        anomalies=["Vendor terminal pivoting to core router."]
    )
    gt = GroundTruth(false_positives=[], real_threats=["alert_supply_01", "alert_supply_02"], attacker_ips=["172.16.0.50"], compromised_users=["vendor_acct"], relevant_ips=["172.16.0.50", "10.0.0.10"], relevant_users=["vendor_acct", "sysadmin"])
    return Scenario(task_name="lateral_movement_detection", task_difficulty=TaskDifficulty.HARD, description="Detect supply chain pivot.", initial_alerts=[alert1, alert2], context_data=context, ground_truth=gt)

def create_hard_scenario_v2(now, seed) -> Scenario:
    alert1 = SecurityAlert(id="alert_insider_01", alert_type=AlertType.FILE_ACCESS_ANOMALY, severity=4, source_ip="10.0.0.55", destination_ip="FS-HR", source_user="mike_hr", alert_context="Mass download of employee PII.", timestamp=now - timedelta(minutes=30), status=AlertStatus.UNRESOLVED)
    alert2 = SecurityAlert(id="alert_insider_02", alert_type=AlertType.LATERAL_MOVEMENT, severity=5, source_ip="10.0.0.55", destination_ip="10.0.0.99", source_user="mike_hr", alert_context="Data copied to FTP staging server.", timestamp=now - timedelta(minutes=5), status=AlertStatus.UNRESOLVED)
    context = AlertContextData(
        file_access_logs=[FileAccessRecord(timestamp=now - timedelta(minutes=30), user="mike_hr", file_path="/hr/pii_master.csv", action="download")],
        anomalies=["Data staging to external facing FTP server."]
    )
    gt = GroundTruth(false_positives=[], real_threats=["alert_insider_01", "alert_insider_02"], attacker_ips=["10.0.0.55"], compromised_users=["mike_hr"], relevant_ips=["10.0.0.55", "10.0.0.99"], relevant_users=["mike_hr"], relevant_files=["/hr/pii_master.csv"])
    return Scenario(task_name="lateral_movement_detection", task_difficulty=TaskDifficulty.HARD, description="Detect insider threat data staging.", initial_alerts=[alert1, alert2], context_data=context, ground_truth=gt)

def create_hard_scenario(seed: Optional[int] = None) -> Scenario:
    now = datetime.now(timezone.utc)
    v = (seed or 0) % 3
    if v == 0: return create_hard_scenario_v0(now, seed)
    if v == 1: return create_hard_scenario_v1(now, seed)
    return create_hard_scenario_v2(now, seed)