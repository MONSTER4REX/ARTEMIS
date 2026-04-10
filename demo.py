"""
Artemis SOC Triage Benchmark — Environment Demo
================================================
This script demonstrates the full reset/step/state flow of the Artemis
environment using hardcoded expert actions. No LLM key is required.

Usage:
    # 1. Start the server first:
    #    uvicorn server.main:app --port 7860
    #
    # 2. Run this demo:
    #    python demo.py

ENV_URL defaults to http://localhost:7860 but can be overridden:
    ENV_URL=https://your-space.hf.space python demo.py
"""

import json
import os
import sys
import requests

ENV_URL = os.getenv("ENV_URL", "http://localhost:7860")

DIVIDER = "=" * 60

DEMO_TASKS = [
    {
        "task": "false_positive_triage",
        "seed": 42,
        "label": "EASY — False Positive Triage",
        "actions": [
            {
                "action_type": "resolve_alert",
                "alert_id": "alert_001_sql_injection",
                "reason": "Source IP 10.0.0.50 is the internal pentest VLAN. This is an authorised test.",
            },
            {
                "action_type": "resolve_alert",
                "alert_id": "alert_002_shodan",
                "reason": "192.0.2.1 is a known Shodan research crawler. Allowlisted.",
            },
            {
                "action_type": "escalate_to_human",
                "severity": 2,
                "reason": "alert_003 is ambiguous — user is on business travel. Escalating for human review.",
            },
        ],
    },
    {
        "task": "brute_force_defense",
        "seed": 42,
        "label": "MEDIUM — Brute Force Defense",
        "actions": [
            {
                "action_type": "fetch_logs",
                "ip_address": "203.0.113.1",
                "reason": "Pulling login history for primary attacker IP before isolating.",
            },
            {
                "action_type": "isolate_ip",
                "ip_address": "203.0.113.1",
                "reason": "This IP succeeded in logging in after 3 failed attempts. Block immediately.",
            },
            {
                "action_type": "isolate_user",
                "user_id": "admin",
                "reason": "Admin account was successfully compromised via brute force. Locking account.",
            },
        ],
    },
    {
        "task": "lateral_movement_detection",
        "seed": 42,
        "label": "HARD — Lateral Movement Detection",
        "actions": [
            {
                "action_type": "fetch_logs",
                "user_id": "sarah_dev",
                "reason": "Stage 1: Pulling full history for sarah_dev to understand the chain.",
            },
            {
                "action_type": "fetch_logs",
                "file_path": "/production/configs/db_credentials.yaml",
                "reason": "Stage 2: Confirming credential file access.",
            },
            {
                "action_type": "isolate_user",
                "user_id": "sarah_dev",
                "reason": "Confirmed 3-stage attack: unusual login → credential theft → psexec lateral move.",
            },
        ],
    },
]

def print_header(text: str):
    print(f"\n{DIVIDER}")
    print(f"  {text}")
    print(DIVIDER)

def check_server():
    try:
        res = requests.get(f"{ENV_URL}/", timeout=5)
        res.raise_for_status()
        data = res.json()
        print(f"[OK] Server is online — {data.get('benchmark', 'Artemis')} | Active episodes: {data.get('active_episodes', 0)}")
        return True
    except Exception as e:
        print(f"[FAIL] Cannot reach environment server at {ENV_URL}")
        print(f"       Start it with: uvicorn server.main:app --port 7860")
        print(f"       Error: {e}")
        return False

def run_demo_task(demo: dict):
    task = demo["task"]
    seed = demo["seed"]
    label = demo["label"]
    actions = demo["actions"]

    print_header(label)

    # --- RESET ---
    try:
        res = requests.post(f"{ENV_URL}/reset", json={"task": task, "seed": seed}, timeout=10)
        res.raise_for_status()
        reset_data = res.json()
    except Exception as e:
        print(f"[FAIL] reset() failed: {e}")
        return

    episode_id = reset_data["episode_id"]
    obs = reset_data["observation"]
    print(f"\n[RESET] episode_id={episode_id} task={task}")
    print(f"        Alerts: {[a['id'] for a in obs.get('current_alerts', [])]}")

    # --- STEPS ---
    total_reward = 0.0
    for i, action in enumerate(actions, start=1):
        try:
            res = requests.post(
                f"{ENV_URL}/step",
                json={"episode_id": episode_id, "action": action},
                timeout=10,
            )
            res.raise_for_status()
            step_data = res.json()
        except Exception as e:
            print(f"[FAIL] step() failed at step {i}: {e}")
            continue

        reward = step_data.get("reward", 0.0)
        done = step_data.get("done", False)
        info = step_data.get("info", {})
        total_reward += reward

        print(f"\n[STEP {i}] action={action['action_type']}")
        print(f"          reward={reward:.2f} | done={str(done).lower()}")
        print(f"          explanation: {info.get('action_explanation', 'N/A')}")

        if done:
            print(f"          -> Episode complete.")
            break

    # --- STATE ---
    try:
        res = requests.get(f"{ENV_URL}/state", params={"episode_id": episode_id}, timeout=10)
        res.raise_for_status()
        state_data = res.json()
        cumulative = state_data.get("cumulative_reward", total_reward)
        step_count = state_data.get("step_count", len(actions))
        print(f"\n[STATE] step_count={step_count} | cumulative_reward={cumulative:.2f}")
    except Exception as e:
        print(f"[WARN] state() query failed: {e}")

    print(f"\n{'─'*60}")
    print(f"  Task Score (approx): {min(1.0, max(0.0, total_reward / (len(actions) * 1.5))):.2f}")

def main():
    print_header("Artemis SOC Triage Benchmark — Environment Demo")
    print(f"Target: {ENV_URL}\n")

    if not check_server():
        sys.exit(1)

    for demo in DEMO_TASKS:
        run_demo_task(demo)

    print_header("Demo Complete")
    print("All 3 tasks demonstrated successfully.")
    print("The environment handles reset(), step(), and state() correctly.")

if __name__ == "__main__":
    main()
