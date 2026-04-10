import os
import sys
import json
import requests
from openai import OpenAI

SCORE_FLOOR = 0.01
SCORE_CEIL = 0.99

# --- Required Environment Variables ---
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4-0125-preview")
HF_TOKEN = os.getenv("HF_TOKEN")
ENV_URL = os.getenv("ENV_URL", "http://localhost:7860")

if HF_TOKEN is None:
    print("[FATAL] HF_TOKEN environment variable is required", flush=True)
    sys.exit(1)

try:
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)
except TypeError as e:
    print(
        f"[FATAL] OpenAI client init failed (likely openai/httpx version mismatch): {e}",
        flush=True,
    )
    sys.exit(1)
except Exception as e:
    print(f"[FATAL] OpenAI client init failed: {e}", flush=True)
    sys.exit(1)


# --- Standard OpenEnv Logging API ---

def log_start(task: str, env: str, model: str):
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, score=None, error=None):
    error_str = "null"
    if error is not None:
        error_str = str(error).replace("\n", " ").replace("\r", " ").strip()
    score_str = f" score={score:.4f}" if score is not None else ""
    print(
        f"[STEP] step={step} action={action} "
        f"reward={reward:.4f} done={str(done).lower()}{score_str} "
        f"error={error_str}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float):
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.4f}",
        flush=True,
    )


def clamp_score(v: float) -> float:
    return max(SCORE_FLOOR, min(SCORE_CEIL, v))


# --- Agent Logic ---

SYSTEM_PROMPT = """You are an expert SOC analyst. Analyze the observation and choose the absolute best action.
Return ONLY a JSON object. No markdown formatting.
Allowed action_types: resolve_alert, isolate_ip, isolate_user, fetch_logs, escalate_to_human.
Fields to include based on action_type:
- resolve_alert: "alert_id", "reason"
- isolate_ip: "ip_address", "reason"
- isolate_user: "user_id", "reason"
- fetch_logs: "ip_address" OR "user_id" OR "file_path", "reason"
- escalate_to_human: "severity" (integer 1-5), "reason"

STRATEGY HANDBOOK:
1. False Positive Triage: If an alert is a known scanner (Shodan, Nessus), internal pentest, or authorized VPN, use resolve_alert.
2. Brute Force: If an IP has many failed attempts, use isolate_ip on that attacker IP. If there's a successful login from that IP, use isolate_user too!
3. Lateral Movement: If you see unusual file access (credentials, staging) or lateral movement (psexec, SSH pivots), use isolate_user and isolate_ip.
4. Investigation: Always use fetch_logs first if an IP or User is suspicious but not fully confirmed.

Return exactly this JSON format: {"action_type":"...","reason":"..."}
"""

FALLBACK_ACTION = {
    "action_type": "escalate_to_human",
    "reason": "Agent fallback: unable to determine action",
    "severity": 3,
}


def get_llm_action(observation: dict) -> dict:
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": json.dumps(observation, separators=(",", ":")),
                },
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if content:
            parsed = json.loads(content)
            if parsed.get("action_type") == "escalate_to_human" and "severity" not in parsed:
                parsed["severity"] = 3
            if "reason" not in parsed or not parsed["reason"]:
                parsed["reason"] = "LLM action"
            return parsed
        return dict(FALLBACK_ACTION)
    except Exception as e:
        fallback = dict(FALLBACK_ACTION)
        fallback["reason"] = f"LLM error: {str(e)[:200]}"
        return fallback


def compact(obj: dict) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


# --- Episode Runner ---

ALL_TASKS = [
    "false_positive_triage",
    "brute_force_defense",
    "lateral_movement_detection",
]


def run_episode(task: str) -> float:
    env_name = "artemis"
    max_steps = 8

    log_start(task=task, env=env_name, model=MODEL_NAME)

    rewards: list[float] = []
    steps = 0
    success = False
    score = SCORE_FLOOR
    episode_id = None

    try:
        reset_res = requests.post(
            f"{ENV_URL}/reset", json={"task": task}, timeout=30
        )
        reset_res.raise_for_status()
        reset_data = reset_res.json()
        episode_id = reset_data["episode_id"]
        observation = reset_data["observation"]

        for i in range(1, max_steps + 1):
            steps = i

            action_obj = get_llm_action(observation)
            action_str = compact(action_obj)

            try:
                step_res = requests.post(
                    f"{ENV_URL}/step",
                    json={"episode_id": episode_id, "action": action_obj},
                    timeout=30,
                )
                step_res.raise_for_status()
                step_data = step_res.json()
            except Exception as step_err:
                log_step(steps, action_str, 0.0, False, error=str(step_err))
                continue

            reward = float(step_data.get("reward", 0.0))
            done = bool(step_data.get("done", False))
            error = step_data.get("error", None)
            observation = step_data.get("observation", observation)
            step_score = step_data.get("score", None)

            rewards.append(reward)

            log_step(steps, action_str, reward, done, score=step_score, error=error)

            if done:
                if step_score is not None:
                    score = clamp_score(float(step_score))
                success = sum(rewards) > 0.0
                break

        # Fetch graded score from the /grade endpoint if we have an episode
        if episode_id is not None:
            try:
                grade_res = requests.post(
                    f"{ENV_URL}/grade",
                    json={"episode_id": episode_id},
                    timeout=10,
                )
                if grade_res.status_code == 200:
                    grade_score = grade_res.json().get("score", None)
                    if grade_score is not None:
                        score = clamp_score(float(grade_score))
            except Exception:
                pass

    except Exception as e:
        log_step(max(1, steps + 1), "error", 0.0, True, error=str(e))

    finally:
        score = clamp_score(score)
        log_end(success=success, steps=steps, score=score)
        print(f"[SCORE] task={task} score={score:.4f}", flush=True)

    return score


def main():
    print(f"[INFO] Running {len(ALL_TASKS)} tasks against {ENV_URL}", flush=True)
    scores = {}
    for task in ALL_TASKS:
        task_score = run_episode(task)
        scores[task] = task_score
    print("[SUMMARY]", flush=True)
    for t, s in scores.items():
        print(f"  {t}: {s:.4f}", flush=True)


if __name__ == "__main__":
    main()