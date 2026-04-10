import os
import json
import requests
from openai import OpenAI

# --- Required Environment Variables ---
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4-0125-preview")
HF_TOKEN = os.getenv("HF_TOKEN")
ENV_URL = os.getenv("ENV_URL", "http://localhost:7860")

if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable is required")

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN)


# --- Standard OpenEnv Logging API ---

def log_start(task: str, env: str, model: str):
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error=None):
    error_str = "null"
    if error is not None:
        error_str = str(error).replace("\n", " ").replace("\r", " ").strip()
    print(
        f"[STEP] step={step} action={action} "
        f"reward={reward:.2f} done={str(done).lower()} "
        f"error={error_str}",
        flush=True,
    )


def log_end(success: bool, steps: int, rewards: list):
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} rewards={rewards_str}",
        flush=True,
    )


# --- Agent Logic ---

SYSTEM_PROMPT = (
    "You are an expert SOC analyst. Return ONLY a JSON object.\n"
    "Allowed action_types: resolve_alert, isolate_ip, isolate_user, "
    "fetch_logs, escalate_to_human.\n"
    'Format: {"action_type":"...","reason":"..."}\n'
    "Include alert_id, ip_address, user_id, or severity as needed."
)


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
            return json.loads(content)
        return {"action_type": "escalate_to_human", "reason": "empty response"}
    except Exception as e:
        return {"action_type": "escalate_to_human", "reason": str(e)}


def compact(obj: dict) -> str:
    """Single-line JSON string safe for stdout."""
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


# --- Episode Runner ---

def run_episode():
    task = "false_positive_triage"
    env = "artemis"
    max_steps = 8

    log_start(task=task, env=env, model=MODEL_NAME)

    rewards: list[float] = []
    steps = 0
    success = False

    try:
        reset_res = requests.post(
            f"{ENV_URL}/reset", json={"task": task}, timeout=15
        )
        reset_res.raise_for_status()
        reset_data = reset_res.json()
        episode_id = reset_data["episode_id"]
        observation = reset_data["observation"]

        for i in range(1, max_steps + 1):
            steps = i

            action_obj = get_llm_action(observation)
            action_str = compact(action_obj)

            step_res = requests.post(
                f"{ENV_URL}/step",
                json={"episode_id": episode_id, "action": action_obj},
                timeout=15,
            )
            step_res.raise_for_status()
            step_data = step_res.json()

            reward = float(step_data.get("reward", 0.0))
            done = bool(step_data.get("done", False))
            error = step_data.get("error", None)
            observation = step_data.get("observation", observation)

            rewards.append(reward)

            # [STEP] emitted immediately after env.step() returns
            log_step(steps, action_str, reward, done, error)

            if done:
                success = sum(rewards) > 0.0
                break

    except Exception as e:
        log_step(max(1, steps + 1), "error", 0.0, True, str(e))

    finally:
        # [END] always emitted, even on exception
        log_end(success=success, steps=steps, rewards=rewards)


if __name__ == "__main__":
    run_episode()