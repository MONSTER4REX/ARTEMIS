# PRODUCT REQUIREMENTS DOCUMENT (PRD)
## SOC Analyst Triage Environment
### OpenEnv Hackathon Submission

**Document Version:** 1.0  
**Last Updated:** April 5, 2026  
**Status:** Draft - Ready for Implementation  
**Owner:** Development Team  
**Stakeholders:** Hackathon Judges, Security Research Community

---

## TABLE OF CONTENTS

1. Executive Summary
2. Product Vision & Goals
3. Problem Statement & Motivation
4. Target Users & Personas
5. Product Overview
6. Detailed Functional Requirements
7. Non-Functional Requirements
8. System Architecture
9. Data Models & Specifications
10. API Endpoint Specifications
11. Task Definitions & Scenarios
12. Grading & Scoring System
13. Reward Function Design
14. Environment State Management
15. Testing Strategy
16. Deployment Strategy
17. Success Metrics & KPIs
18. Timeline & Milestones
19. Risks & Mitigation Plan
20. Appendices

---

## 1. EXECUTIVE SUMMARY

This document specifies the complete requirements for building "SOC Analyst Triage Environment," a real-world simulation where AI agents learn to triage security alerts in a Security Operations Center (SOC) setting. The environment implements the full OpenEnv specification and is designed to serve as a benchmark for evaluating autonomous agent decision-making in cybersecurity contexts.

### Key Objectives

The primary objective is to create a deployable, reproducible environment that allows AI agents to practice security alert triage at three difficulty levels: false positive dismissal (easy), brute force attack detection and blocking (medium), and multi-stage lateral movement detection (hard). The environment will be deployed to Hugging Face Spaces and will include a complete baseline inference script demonstrating how agents interact with it.

### Target Hackathon Criteria

This project is designed to maximize scores across all five evaluation categories: real-world utility (30%), task and grader quality (25%), environment design (20%), code quality and spec compliance (15%), and creativity and novelty (10%).

### Deliverables at a Glance

The submission will include: a fully functional SOC environment implementing the OpenEnv API specification, three well-calibrated tasks with deterministic graders, a baseline inference script using OpenAI client, complete Docker containerization, deployment to Hugging Face Spaces with a working URL, comprehensive README with all required documentation, and this PRD document covering all implementation details.

---

## 2. PRODUCT VISION & GOALS

### Vision Statement

To create the OpenEnv ecosystem's first production-grade cybersecurity agent benchmark, enabling researchers and enterprises to train, evaluate, and validate AI agents for security operations before deploying them to real SOC environments.

### Primary Goals

The environment will establish a common benchmark for measuring agent performance in security alert triage, reducing the gap between agent capability and real-world SOC applicability. It will provide partial credit rewards that enable agents to learn from near-correct actions, implement deterministic grading that guarantees reproducible evaluation, and model realistic multi-stage attack scenarios that go beyond simple pattern matching.

### Success Criteria

Success is achieved when judges confirm the environment deploys cleanly, the three tasks are solvable with clear difficulty progression, baseline inference runs without error and produces reproducible scores, the OpenEnv specification is fully satisfied with documented validation, and the environment receives positive feedback for real-world applicability and design creativity.

---

## 3. PROBLEM STATEMENT & MOTIVATION

### The SOC Alert Fatigue Crisis

Security Operations Centers (SOCs) worldwide are drowning in alerts. A typical enterprise with 5,000+ employees receives between 10,000 and 1,000,000 security alerts daily. Approximately 80-90% of these alerts are false positives or low-priority notifications that don't represent genuine security threats. Human SOC analysts spend 70-80% of their time dismissing false alerts, which means they have minimal time and mental energy for actual threat investigation.

This inefficiency creates three critical problems. First, real attacks are missed because analysts are fatigued by false positives. Second, alert response time increases because analysts are overwhelmed, allowing attackers more time to move laterally through networks. Third, enterprises spend massive resources on both alert generation infrastructure and human analysts, yet fail to detect many sophisticated attacks.

### Why AI Agents Are the Solution

Large language models (LLMs) like GPT-4, Claude, and Qwen have demonstrated remarkable capability in reasoning about complex, contextual scenarios with partial information. These models can read alert descriptions, synthesize historical context, and make reasonable triage decisions. However, there is currently no standard way to evaluate these agents in a realistic SOC context.

Existing benchmarks are either too simplistic (binary classification tasks) or too artificial (CTF-style puzzles). There is no open-source, reproducible environment where researchers can train and evaluate SOC agents at scale. This creates a gap between academic interest in security automation and practical deployment.

### Market Opportunity

Companies like Microsoft, Google, Amazon, Cloudflare, and dozens of mid-market security vendors are actively investing in AI-powered SOC automation. They need a way to validate agents before deploying them. Enterprises would use a standardized SOC environment to evaluate agents from different vendors. This environment becomes a reference benchmark for the security community.

---

## 4. TARGET USERS & PERSONAS

### Primary Users

The primary users are AI researchers and engineers building security automation agents. They want a realistic, well-designed environment to train and evaluate their agents. They need reproducible, deterministic grading to compare agent performance across runs and across different model architectures.

### Secondary Users

Security researchers building behavioral models of attacks will use this environment to understand multi-stage attack signatures. Enterprise security teams will use it to validate agents before deploying them in production SOCs. Hackathon judges will use it to evaluate this submission against other environments based on realism, design quality, and implementation.

### User Personas

**Dr. Research** is an AI researcher at a major tech company. She is building a custom multi-agent system for security automation. She needs an environment to evaluate her agents' alert triage decisions and wants fine-grained reward signals to guide learning. She will run the environment 1,000+ times and expects it to be fast and reliable.

**Alice the SecOps Manager** works at a mid-sized SaaS company. She has a small SOC team that is overloaded with alerts. She is evaluating whether to deploy an AI agent to help with triage. She needs to see the agent work on realistic scenarios before risking production deployment. She will run the environment 10-20 times with different agent implementations.

**Judge** is evaluating this hackathon submission. Judge wants to verify that the environment deploys cleanly, the tasks are well-designed with clear difficulty progression, the grading is deterministic and reproducible, and the environment models real-world SOC operations faithfully. Judge will spend 1-2 hours evaluating the submission.

---

## 5. PRODUCT OVERVIEW

### What is the SOC Analyst Environment?

The SOC Analyst Environment is a simulated Security Operations Center dashboard accessible via a REST API. An agent receives a set of security alerts with contextual information (login history, file access logs, network traffic patterns). The agent must take actions to triage these alerts: dismissing false positives, isolating attack sources, fetching additional logs for investigation, or escalating to human analysts. The environment computes rewards based on whether the agent's actions were appropriate, and returns updated observations after each action.

### Core Mechanics

The environment operates on an episode-based model. Each episode corresponds to one security incident scenario. The agent starts with a `reset()` call, which initializes a scenario and returns the initial observation (the alerts and context). For up to eight steps, the agent can call `step()` with an action. The environment returns an updated observation, a reward score, and a boolean indicating whether the episode is complete. After the episode ends, the environment computes a final score between 0.0 and 1.0 reflecting overall performance.

### Integration Points

The environment integrates with the LLM via a baseline inference script. The script is not part of the environment itself; instead, it demonstrates how to use the environment. The script calls the environment's REST API endpoints, parses observations, prompts an LLM for decisions, and logs results in a standardized format for evaluation.

### Scope & Limitations

The environment simulates alert triage, not full incident response. It does not model real network traffic, does not require agents to write code, and does not simulate the effects of agent actions on actual systems. The environment is fast (millisecond-scale) and does not require GPU resources. It is fully deterministic: the same agent running the same scenario will always produce the same observation sequence.

---

## 6. DETAILED FUNCTIONAL REQUIREMENTS

### 6.1 Core Environment Interface

The environment must implement the full OpenEnv specification. This means it must expose three primary methods: `reset()`, `step(action)`, and `state()`. All interactions are asynchronous and accessed via REST API endpoints.

The `reset()` method initializes a new episode. It accepts an optional task identifier and an optional seed for reproducibility. It returns a `ResetResult` containing an initial observation, a done flag (always false on reset), and an episode ID for tracking. The observation includes the current list of alerts with full context, the system status (which IPs are blocked, which users are isolated), and the current step count.

The `step(action)` method processes an agent action. It accepts a structured `SOCAction` object specifying the action type, relevant parameters (e.g., IP address to isolate), a reason string for logging, and optional severity level. It returns a `StepResult` containing the new observation, a numerical reward, a done flag indicating episode completion, and metadata. The method must validate actions (e.g., cannot isolate a non-existent IP) and return zero or negative reward for invalid actions.

The `state()` method returns the current state of the environment without modifying it. This is used for inspection and debugging. It returns the full internal state including all scenario metadata, agent actions taken so far, and computed rewards.

### 6.2 Action Types

The environment supports five distinct action types, each with specific parameters and validation logic.

**resolve_alert** marks an alert as resolved. Parameters: alert_id (required, must exist), reason (required, free-form text explaining the dismissal). Validation: alert_id must be in the current alert list. Reward logic: positive reward if the alert is actually a false positive, negative reward if it is a real threat that should not be dismissed.

**isolate_ip** blocks traffic from an IP address. Parameters: ip_address (required, valid IPv4 format), reason (required). Validation: ip_address must appear as a source in some alert. Reward logic: positive reward if the IP is actually malicious, negative reward if the IP is legitimate (false positive isolation).

**isolate_user** locks a user account. Parameters: user_id (required, must exist in logs), reason (required). Validation: user_id must appear in the scenario context. Reward logic: positive reward if the user is compromised, negative reward if the user is legitimate. Typically used in lateral movement scenarios.

**fetch_logs** requests historical logs. Parameters: ip_address (optional), user_id (optional), file_path (optional, for file access logs). At least one parameter must be provided. Validation: the provided IP/user/file must exist in the scenario. Reward logic: modest positive reward (0.1-0.3) for gathering evidence, as investigation is always reasonable but not required for success.

**escalate_to_human** escalates the incident to a human analyst. Parameters: severity (required, 1-5 scale), reason (required). Validation: none, always valid. Reward logic: context-dependent. If the scenario is genuinely ambiguous, escalation receives positive reward. If the scenario is clearly solvable by the agent, escalation receives modest positive reward (0.3-0.5) to avoid discouraging safe behavior, but less than taking the correct action.

### 6.3 Observation Structure

The observation is a structured object that the agent sees after each action. It includes the following components.

**current_alerts** is a list of SecurityAlert objects. Each alert has: id (unique string), alert_type (e.g., "Brute Force", "SQL Injection"), severity (1-5), source_ip, destination_ip, source_user (if applicable), timestamp, alert_context (brief description), and status (unresolved, isolated, or resolved).

**alert_context** is a dictionary containing historical information relevant to the alerts. It includes login_history (list of recent logins with timestamp, user, IP, success/failure), file_access_logs (list of recent file accesses with user, file path, action, timestamp), network_traffic (summary of traffic patterns), and anomalies (detected anomalies like unusual access patterns).

**system_status** is a dictionary describing the current state: blocked_ips (list of IPs currently blocked), isolated_users (list of users currently isolated), which_alerts_resolved (count of resolved alerts), active_incidents (count of still-active threat scenarios).

**step_count** is the current step number (1-8).

**episode_info** includes episode_id (unique identifier), task_name (e.g., "brute_force_defense"), task_difficulty (easy, medium, or hard), and time_elapsed (for tracking performance).

### 6.4 Reward Function

The reward function provides signal across the entire trajectory, not just at the end of the episode. It includes partial credit for near-correct actions and penalties for clearly harmful behavior. Reward values range from -1.0 to +1.0.

**Base Reward Computation:** For each action, compute a base_reward between -1.0 and +1.0 based on the action type and scenario ground truth. Sum base_rewards across all steps. Normalize to [0.0, 1.0] by dividing by the maximum possible reward.

**Action-Specific Rewards:**

- **resolve_alert**: If the alert is a false positive, +1.0. If it is a real threat being incorrectly dismissed, -0.5. If reasoning is weak but conclusion is correct, +0.7.
- **isolate_ip**: If the IP is malicious, +1.0. Bonus +0.2 if isolated within first 3 steps (time-sensitive). If the IP is legitimate, -0.3. If the IP doesn't exist, -0.5.
- **isolate_user**: If the user is compromised, +1.0. If the user is legitimate, -0.3.
- **fetch_logs**: Always +0.1 to +0.3 depending on relevance (fetching logs for the attacked IP is more valuable than arbitrary logs).
- **escalate_to_human**: If scenario is ambiguous, +0.8. Otherwise, +0.3 (safe but not ideal).

**Step Penalty**: For each step after step 8, apply a -0.1 penalty to reward (to incentivize speed without demanding perfection).

**Episode Reward**: Normalize the sum of step rewards to [0.0, 1.0].

---

## 7. NON-FUNCTIONAL REQUIREMENTS

### 7.1 Performance Requirements

The environment must respond to API calls in under 500 milliseconds per action. The `reset()` call must return in under 100 milliseconds. The entire inference script running three tasks (one easy, one medium, one hard) with up to 8 steps per task must complete in under 20 minutes on a machine with 2 vCPU and 8GB RAM.

### 7.2 Scalability Requirements

The environment must support concurrent episodes (multiple agents running in parallel). It must handle at least 100 concurrent API calls without degradation. State for each episode must be isolated so that concurrent episodes do not interfere with each other.

### 7.3 Reliability & Availability

The environment must be stateless except for temporary episode storage. There is no persistent database required. Each episode data can be garbage-collected after it completes. The environment must be fault-tolerant: if an agent sends an invalid action, the environment must gracefully return an error without crashing. The environment must log all API calls for debugging and audit purposes.

### 7.4 Determinism & Reproducibility

The environment must be fully deterministic. Given the same scenario ID and random seed, the environment will always return the same observation sequence. Agents calling the environment with the same initial observation will always see the same reward for the same action. This is critical for reproducible research.

### 7.5 Documentation & Usability

All endpoints must be fully documented with request/response examples. The code must be well-commented, especially around reward computation and grading logic. The README must include setup instructions, example usage, and expected performance metrics.

---

## 8. SYSTEM ARCHITECTURE

### 8.1 Architecture Overview

The system consists of three loosely coupled layers: the environment layer (the simulation engine), the API layer (REST API exposing the environment), and the agent layer (the inference script that uses the API).

The environment layer is a pure Python module with no external dependencies beyond standard library. It contains the core simulation logic: scenario generation, state management, action validation, reward computation, and episode tracking. The environment is instantiated once per server instance and maintains internal state for active episodes.

The API layer is a FastAPI application that exposes the environment via HTTP endpoints. FastAPI is used for its speed, async support, and automatic OpenAPI documentation. The API layer translates HTTP requests to environment method calls and translates environment responses to JSON.

The agent layer is a standalone Python script (the baseline inference script) that runs independently. It calls the API endpoints, receives observations, prompts an LLM for decisions, parses LLM responses, and sends actions back to the API. The script is self-contained and does not require importing the environment code.

### 8.2 Component Diagram

```
┌─────────────────────────────────────────────────┐
│ Hugging Face Spaces Container                   │
├─────────────────────────────────────────────────┤
│  FastAPI Server                                 │
│  ├─ POST /reset    -> env.reset()               │
│  ├─ POST /step     -> env.step(action)          │
│  ├─ GET  /state    -> env.state()               │
│  └─ GET  /docs     -> OpenAPI spec              │
├─────────────────────────────────────────────────┤
│  SOCEnv (Environment Layer)                     │
│  ├─ Scenario Manager                            │
│  ├─ State Manager                               │
│  ├─ Grader                                      │
│  ├─ Reward Computer                             │
│  └─ Alert Generator                             │
└─────────────────────────────────────────────────┘
         ↑
         │ HTTP API calls
         ↓
┌─────────────────────────────────────────────────┐
│ Local Machine (Judge or Researcher)             │
├─────────────────────────────────────────────────┤
│  Baseline Inference Script                      │
│  ├─ LLM Client (OpenAI)                        │
│  ├─ Environment Client                          │
│  └─ Logging & Evaluation                        │
└─────────────────────────────────────────────────┘
```

### 8.3 Module Structure

```
soc-analyst-env/
├── artemis_env/
│   ├── __init__.py                 # Package initialization
│   ├── environment.py              # Main SOCEnv class
│   ├── models.py                   # Pydantic data models
│   ├── scenarios.py                # Scenario generators
│   ├── graders.py                  # Task graders
│   ├── reward_engine.py            # Reward computation
│   └── validators.py               # Action validation
├── server/
│   ├── app.py                      # FastAPI application
│   ├── Dockerfile                  # Container definition
│   └── requirements.txt             # Python dependencies
├── inference.py                    # Baseline agent script
├── openenv.yaml                    # OpenEnv metadata
├── README.md                        # User documentation
└── tests/
    ├── test_environment.py         # Unit tests
    ├── test_api.py                 # API integration tests
    └── test_grading.py             # Grader validation
```

---

## 9. DATA MODELS & SPECIFICATIONS

### 9.1 Pydantic Models

All data is defined using Pydantic v2 models for type safety and JSON serialization.

**SecurityAlert Model**
```
id: str (unique identifier, e.g., "alert_001")
alert_type: Literal["SQL_Injection", "Brute_Force", "Unauthorized_Login", "File_Access_Anomaly", "Lateral_Movement"]
severity: int (1-5, where 5 is critical)
source_ip: str (IPv4 address)
destination_ip: str (IPv4 address or network resource identifier)
source_user: Optional[str] (username if applicable)
timestamp: datetime (when alert was triggered)
alert_context: str (brief description of what happened)
failed_attempts: Optional[int] (for brute force alerts)
time_window: Optional[str] (for temporal attacks, e.g., "5 minutes")
status: Literal["unresolved", "isolated", "resolved"]
```

**SOCObservation Model**
```
current_alerts: List[SecurityAlert]
alert_context: Dict[str, Any] (contains login_history, file_access_logs, network_traffic)
system_status: Dict[str, Any] (contains blocked_ips, isolated_users)
step_count: int
episode_id: str
task_name: str
task_difficulty: Literal["easy", "medium", "hard"]
time_elapsed: float (seconds since episode start)
```

**SOCAction Model**
```
action_type: Literal["resolve_alert", "isolate_ip", "isolate_user", "fetch_logs", "escalate_to_human"]
alert_id: Optional[str] (required for resolve_alert)
ip_address: Optional[str] (required for isolate_ip)
user_id: Optional[str] (required for isolate_user)
reason: str (always required)
severity: Optional[int] (required for escalate_to_human, 1-5 scale)
```

**ResetResult Model**
```
observation: SOCObservation
done: bool (always false on reset)
episode_id: str
```

**StepResult Model**
```
observation: SOCObservation
reward: float (-1.0 to +1.0)
done: bool
info: Dict[str, Any] (optional metadata)
error: Optional[str] (null if no error, otherwise error message)
```

**Reward Model**
```
action_reward: float (base reward for this action)
step_number: int
time_penalty: float (penalty for step count > 8)
total_reward: float (action_reward + time_penalty)
explanation: str (human-readable explanation of reward)
```

### 9.2 Ground Truth Scenario Model

Each scenario includes metadata and ground truth for grading.

**Scenario Model**
```
scenario_id: str
task_name: str
task_difficulty: Literal["easy", "medium", "hard"]
description: str
initial_alerts: List[SecurityAlert]
context_data: Dict[str, Any]
ground_truth: Dict[str, Any]
  ├─ false_positives: List[str] (alert IDs that are false positives)
  ├─ real_threats: List[str] (alert IDs that are real)
  ├─ attacker_ips: List[str]
  ├─ compromised_users: List[str]
  ├─ lateral_movement_chain: List[Dict] (for hard task, chain of events)
  └─ optimal_actions: List[str] (expected agent actions)
```

---

## 10. API ENDPOINT SPECIFICATIONS

### 10.1 POST /reset

**Purpose:** Initialize a new episode.

**Request:**
```json
{
  "task": "optional_task_name",
  "seed": 42
}
```

**Response (200 OK):**
```json
{
  "observation": {
    "current_alerts": [...],
    "alert_context": {...},
    "system_status": {...},
    "step_count": 0,
    "episode_id": "ep_abc123",
    "task_name": "brute_force_defense",
    "task_difficulty": "medium",
    "time_elapsed": 0.0
  },
  "done": false,
  "episode_id": "ep_abc123"
}
```

**Response (400 Bad Request):** If invalid task name or parameters.

### 10.2 POST /step

**Purpose:** Execute an action in the current episode.

**Request:**
```json
{
  "episode_id": "ep_abc123",
  "action": {
    "action_type": "isolate_ip",
    "ip_address": "203.0.113.1",
    "reason": "Brute force attack from this IP with 15 failed attempts"
  }
}
```

**Response (200 OK):**
```json
{
  "observation": {
    "current_alerts": [...],
    "alert_context": {...},
    "system_status": {
      "blocked_ips": ["203.0.113.1"],
      "isolated_users": []
    },
    "step_count": 1,
    "episode_id": "ep_abc123"
  },
  "reward": 1.0,
  "done": false,
  "info": {
    "action_explanation": "Correctly isolated attacker IP",
    "step_elapsed_ms": 45
  },
  "error": null
}
```

**Response (400 Bad Request):** If episode_id is invalid or action is malformed.

**Response (422 Unprocessable Entity):** If action is valid but semantically invalid (e.g., trying to isolate non-existent IP).

### 10.3 GET /state

**Purpose:** Inspect the current state of an episode.

**Request:**
```
GET /state?episode_id=ep_abc123
```

**Response (200 OK):**
```json
{
  "episode_id": "ep_abc123",
  "task_name": "brute_force_defense",
  "step_count": 3,
  "actions_taken": [
    {
      "step": 1,
      "action": {...},
      "reward": 1.0
    },
    ...
  ],
  "cumulative_reward": 2.5,
  "current_observation": {...}
}
```

**Response (404 Not Found):** If episode_id does not exist.

### 10.4 GET /docs

**Purpose:** OpenAPI documentation.

This is automatically generated by FastAPI. The endpoint returns the OpenAPI 3.0 specification in JSON format, which can be viewed in Swagger UI at `/docs`.

---

## 11. TASK DEFINITIONS & SCENARIOS

### 11.1 Easy Task: False Positive Triage

**Objective:** Dismiss a known false positive alert while leaving real alerts unresolved.

**Scenario Description:** The agent receives a dashboard with three alerts: (1) a SQL injection alert from an internal testing server, (2) a brute force attempt from a known bot, and (3) a legitimate password reset request that was flagged as unusual activity. The agent must correctly dismiss the obvious false positives while leaving the legitimate alert unresolved.

**Alert Details:**

Alert 1 (False Positive): SQL Injection Detection from 10.0.0.50 (internal testing IP). Context indicates this is the company's automated testing suite running routine penetration tests. Alert severity is high, but source IP matches the approved testing range. Alert ID: "alert_001_sql_injection".

Alert 2 (False Positive): Brute Force from 192.0.2.1 (external). Context shows this is a known scanner (Shodan bot) that periodically attempts login. Company has allowlisted this IP for research purposes. Alert ID: "alert_002_shodan".

Alert 3 (Ambiguous): Unauthorized Login from 203.0.203.0 (external). User logged in from a location they have never accessed before (Shanghai). However, context shows the user is on approved business travel. This alert is technically valid but not a threat given context. Alert ID: "alert_003_travel_login".

**Success Criteria:** Agent should dismiss alerts 1 and 2 as false positives. Alert 3 can be resolved or escalated; both are acceptable. Agent must not incorrectly dismiss a real alert.

**Grading Logic:**
- Correctly dismiss alert 1: +1.0
- Correctly dismiss alert 2: +1.0
- Either resolve or escalate alert 3: +0.5 (ambiguous case, either action is reasonable)
- Incorrect dismissal of any alert: -0.5 per incorrect action
- Final score: (sum of rewards) / 3.0 clamped to [0, 1]

**Expected Difficulty:** This task is designed to be solvable by baseline models with high accuracy (>80%). The false positives are clearly marked in the alert context.

### 11.2 Medium Task: Brute Force Attack Detection & Response

**Objective:** Identify a brute force attack and take appropriate defensive action.

**Scenario Description:** The agent receives a dashboard with alerts indicating a coordinated brute force attack against the admin account. The attack has two stages: (1) rapid failed login attempts from multiple source IPs over 5 minutes, followed by (2) a successful login from one of the attack IPs. The agent must recognize the attack signature, isolate the attacking IP(s), and optionally investigate the successful login.

**Alert Details:**

Alert 1: Brute Force Attack Alert. 15 failed login attempts to admin account in 5 minutes from IPs 203.0.113.1, 203.0.113.2, 203.0.113.3, 203.0.113.4. Each IP attempted 3-4 logins. Alert context includes the login_history showing the failed attempts and a brief description of the attack pattern. Alert severity: critical (5). Alert ID: "alert_004_brute_force".

Alert 2: Successful Login to admin account from 203.0.113.1 at 23:45:32 UTC. This IP is the same as one of the brute force sources. Alert severity: high (4). Alert ID: "alert_005_successful_login".

Alert 3: (Optional) Subsequent actions by admin user (file access, API calls) that may be suspicious depending on the user's normal behavior.

**Success Criteria:** Agent should isolate at least the attacking IP (203.0.113.1). Isolating all four attacker IPs is better. The agent should recognize that this is a coordinated multi-source attack, not random activity. The agent should understand that the successful login is suspicious and warrants investigation.

**Grading Logic:**
- Isolate correct IP (203.0.113.1): +1.0 points
- Isolate additional attack IPs (2-4 total): +0.2 per additional IP (max +0.6)
- Isolate wrong IP: -0.3
- Fetch logs to investigate successful login: +0.3 (investigation is good practice)
- Resolve brute force alert with good reasoning: +0.5
- Escalate to human: +0.6 (reasonable but not ideal)
- Final score: sum of rewards, normalized to [0, 1]

**Expected Difficulty:** Medium. Requires the agent to: (1) recognize the brute force pattern, (2) understand that multiple IPs indicate coordination, (3) take defensive action. Baseline models should achieve >70% accuracy.

### 11.3 Hard Task: Multi-Stage Lateral Movement Detection

**Objective:** Detect and respond to a sophisticated lateral movement attack that unfolds in stages.

**Scenario Description:** The agent faces a complex scenario involving an account compromise that evolves over multiple steps. The attack begins with a successful login from an unusual location, progresses to sensitive file access, and includes lateral movement to other systems. The agent must synthesize multiple alerts across different systems, recognize the pattern as a coordinated attack (not independent incidents), and take appropriate action without creating false positives.

**Attack Timeline & Alerts:**

Stage 1 (Alert 1): Unusual Login. User "james_smith" logs in from Shanghai at 22:30 UTC. User normally logs in from San Francisco (9:30 PM PST). Context shows user is on approved business travel. Alert severity: medium (3). Alert ID: "alert_006_unusual_login".

Stage 2 (Alert 2): Sensitive File Access. 10 minutes after the Shanghai login, the same user accesses "/sensitive/financial_data/2024_Q4_budget.xlsx" — a file the user normally never accesses. Timestamp: 22:40 UTC. Alert severity: high (4). Alert ID: "alert_007_file_access_anomaly".

Stage 3 (Alert 3): Lateral Movement. 15 minutes after the file access, the user account is observed making API calls to "api.internal-db.example.com" from a different source IP (192.168.100.50). This source IP is not associated with the user's normal machine. Alert severity: critical (5). Alert ID: "alert_008_lateral_movement".

Stage 4 (Optional Alert): Follow-up actions such as credential gathering attempts or additional file accesses.

**Context & Distractors:**

The scenario includes distractors to test the agent's ability to filter signal from noise. For example: (1) There may be a separate brute force alert from an external IP unrelated to the main attack. (2) There may be legitimate file accesses by other users around the same time, which should not be conflated with the attack. (3) The unusual login by itself is not a threat (users travel). The combination of unusual login + sensitive file access + lateral movement is suspicious.

**Success Criteria:** Agent must recognize that these three events form a coherent attack pattern suggesting account compromise. Agent must either (1) isolate the user account, (2) fetch comprehensive logs to investigate, or (3) escalate with appropriate severity. The agent should NOT incorrectly dismiss any of the three alerts as false positives.

**Grading Logic:**
- Recognize multi-stage pattern and take action (isolate or investigate): +1.0
- Isolate the compromised user: +1.0
- Fetch logs across multiple sources to investigate: +0.5 per fetch
- Escalate to human with high severity: +0.8
- Investigate first three stages, then identify lateral movement: +0.7
- Miss the lateral movement or fail to synthesize the pattern: 0.0
- Incorrectly dismiss any of the three alerts: -0.5
- Final score: sum of rewards, normalized to [0, 1]

**Expected Difficulty:** Hard. Requires: (1) multi-step temporal reasoning, (2) understanding that seemingly independent events form a pattern, (3) risk judgment (balancing false positives against missed detections). Baseline models should achieve 40-60% accuracy.

---

## 12. GRADING & SCORING SYSTEM

### 12.1 Deterministic Grading Framework

All grading is deterministic and reproducible. Each scenario has an associated ground truth file containing the correct answer for every possible agent action. When the agent completes an episode, the grader retrieves the ground truth for that scenario and compares the agent's actions against it.

### 12.2 Grader Implementation

The `Grader` class takes a scenario's ground truth and an episode's action history. It computes a score between 0.0 and 1.0 using the reward function. The grader is deterministic: given the same scenario and action history, it will always compute the same score.

```python
class TaskGrader:
    def __init__(self, scenario_ground_truth: Dict[str, Any]):
        self.ground_truth = scenario_ground_truth
    
    def grade(self, action_history: List[Tuple[int, SOCAction, float]]) -> float:
        """
        Grade an episode based on actions taken.
        Returns a score in [0.0, 1.0].
        """
        cumulative_reward = 0.0
        max_possible_reward = len(action_history) * 2.0  # Crude max
        
        for step, action, step_reward in action_history:
            # Verify this is the correct reward
            expected_reward = self._compute_expected_reward(action, step)
            assert expected_reward == step_reward, f"Reward mismatch at step {step}"
            cumulative_reward += step_reward
        
        # Normalize to [0, 1]
        score = cumulative_reward / max_possible_reward
        return max(0.0, min(1.0, score))
```

### 12.3 Reproducibility Guarantees

To ensure reproducibility, scenarios are seeded with a random seed, and the same seed always generates the same scenario. When the baseline inference script runs, it logs the seed used, allowing any researcher to reproduce the exact same scenario. The environment logs all rewards and actions to stdout using the standard [START], [STEP], [END] format.

---

## 13. REWARD FUNCTION DESIGN

### 13.1 Reward Function Philosophy

The reward function is designed to provide learning signal throughout an episode, not just at the end. It includes:

1. **Positive rewards** for correct actions (e.g., isolating the actual attacker IP).
2. **Negative rewards** for harmful actions (e.g., isolating innocent users).
3. **Partial credit** for investigating (e.g., fetching logs).
4. **Penalties** for inefficiency (e.g., taking too many steps).

### 13.2 Reward Computation Algorithm

```python
def compute_reward(action: SOCAction, ground_truth: Dict) -> float:
    base_reward = 0.0
    
    if action.action_type == "resolve_alert":
        alert = ground_truth["alerts"][action.alert_id]
        is_false_positive = alert["is_false_positive"]
        
        if is_false_positive:
            base_reward = 1.0  # Correct dismissal
        else:
            base_reward = -0.5  # Missed a real threat
    
    elif action.action_type == "isolate_ip":
        is_attacker = ground_truth["attacker_ips"].get(action.ip_address, False)
        
        if is_attacker:
            base_reward = 1.0
        else:
            base_reward = -0.3  # False positive isolation
    
    elif action.action_type == "isolate_user":
        is_compromised = ground_truth["compromised_users"].get(action.user_id, False)
        
        if is_compromised:
            base_reward = 1.0
        else:
            base_reward = -0.3
    
    elif action.action_type == "fetch_logs":
        # Always investigate, partial credit
        is_relevant = is_relevant_to_attack(action, ground_truth)
        base_reward = 0.3 if is_relevant else 0.1
    
    elif action.action_type == "escalate_to_human":
        is_ambiguous = ground_truth.get("is_ambiguous", False)
        base_reward = 0.8 if is_ambiguous else 0.3
    
    return base_reward
```

### 13.3 Episode Score Normalization

After all steps in an episode, the environment computes a final score:

```python
def compute_episode_score(step_rewards: List[float], step_count: int) -> float:
    cumulative_reward = sum(step_rewards)
    max_possible_reward = step_count * 2.0  # Rough estimate
    score = cumulative_reward / max_possible_reward
    
    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, score))
```

This ensures the final score is always in [0.0, 1.0], regardless of how many steps the agent took.

---

## 14. ENVIRONMENT STATE MANAGEMENT

### 14.1 Episode State

Each episode has its own isolated state. The environment maintains a dictionary mapping episode_id to episode state:

```python
episode_state = {
    "episode_id": "ep_abc123",
    "scenario": Scenario,
    "current_step": 1,
    "actions_taken": [],
    "rewards": [],
    "blocked_ips": [],
    "isolated_users": [],
    "resolved_alerts": [],
    "created_at": datetime.now(),
    "last_accessed_at": datetime.now()
}
```

### 14.2 Concurrency & Thread Safety

Since the environment is stateless and episodes are independent, multiple concurrent requests to the same endpoint are safe. However, requests for the same episode_id must be serialized (only one step() call per episode at a time). The FastAPI server uses asyncio for concurrent I/O handling, but episode state is protected by a lock.

### 14.3 Memory Management

Episodes are garbage-collected 1 hour after the last access. This prevents unbounded memory growth in long-running servers.

---

## 15. TESTING STRATEGY

### 15.1 Unit Tests

Unit tests cover individual components: scenario generation, reward computation, action validation, and observation generation. Each test uses known scenarios and verifies that outputs are correct.

**Scenario Generation Tests:** Verify that scenarios are correctly instantiated with expected ground truth. Test that the same seed produces the same scenario. Test that different seeds produce different scenarios.

**Reward Computation Tests:** Verify that known actions produce expected rewards. Test edge cases like invalid actions and impossible scenarios.

**Action Validation Tests:** Verify that valid actions are accepted and invalid actions are rejected.

**Observation Generation Tests:** Verify that observations are correctly formatted and include expected fields.

### 15.2 Integration Tests

Integration tests verify that the entire environment works end-to-end. They simulate an agent running through an episode and check that the final score is computed correctly.

**Full Episode Tests:** For each task (easy, medium, hard), simulate an agent that takes all correct actions and verify it receives a high score (~1.0). Simulate an agent that takes all incorrect actions and verify it receives a low score (~0.0). Simulate agents that take mixed correct and incorrect actions and verify intermediate scores.

**Consistency Tests:** Run the same scenario twice with different seeds and verify that the same agent actions receive the same rewards in both runs (accounting for seed differences).

### 15.3 API Tests

API tests verify that the REST endpoints work correctly. They use a test FastAPI client to call the endpoints and verify responses.

**Endpoint Tests:** Test POST /reset returns valid ResetResult. Test POST /step with valid and invalid actions. Test GET /state returns correct state. Test error handling (invalid episode_id, malformed action, etc.).

### 15.4 Baseline Inference Validation

The baseline inference script must run without error on all three tasks. The final output must include [START], [STEP], and [END] lines with correct formatting.

---

## 16. DEPLOYMENT STRATEGY

### 16.1 Docker Containerization

The environment is deployed as a Docker container. The Dockerfile specifies a Python 3.10 base image, installs dependencies from requirements.txt, and runs the FastAPI server on port 7860 (Hugging Face Spaces standard).

**Dockerfile Key Points:**
- Base image: python:3.10-slim-bookworm
- Working directory: /app
- Install dependencies: pip install -r requirements.txt
- Copy environment code: COPY artemis_env/ /app/artemis_env/
- Copy server code: COPY server/ /app/server/
- Expose port: EXPOSE 7860
- Run command: CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]

### 16.2 Hugging Face Spaces Deployment

The project is deployed to Hugging Face Spaces as a Docker application. The Space pulls the latest code from GitHub and rebuilds the Docker image automatically on each push. Once deployed, the Space is accessible at a public URL like `https://username-soc-analyst.hf.space`.

**Deployment Steps:**
1. Create a new Space on Hugging Face
2. Select "Docker" as the runtime
3. Connect the GitHub repository
4. Spaces will automatically build and deploy

### 16.3 Validation & Monitoring

Before submission, the `validate-submission.sh` script checks that:
1. The HF Space URL responds to POST /reset with HTTP 200
2. Docker builds successfully (runs on GitHub CI)
3. openenv validate passes
4. The baseline inference script runs without error

---

## 17. SUCCESS METRICS & KPIs

### 17.1 Functional Success Metrics

**Environment Deployment:** The environment deploys cleanly to Hugging Face Spaces and responds to HTTP requests within 500ms. Success: HTTP 200 response to POST /reset within 500ms.

**Task Solvability:** All three tasks are solvable by the baseline agent (GPT-4). Success: Each task achieves >0.5 score with the baseline agent.

**Grader Determinism:** Running the same scenario twice with the same agent actions produces identical rewards. Success: 100% consistency across three runs per task.

**Spec Compliance:** The environment fully implements the OpenEnv specification and passes openenv validate. Success: Zero validation errors.

### 17.2 Quality Success Metrics

**Reward Signal Quality:** The reward function provides learning signal throughout episodes, not just at the end. Success: No task has >50% of episodes with zero-reward steps (except early in episodes).

**Task Difficulty Progression:** Easy task is solved by the agent >80% of the time, medium task >60%, hard task >40%. Success: Baseline agent achieves these accuracy targets.

**Real-World Alignment:** Security experts evaluate the environment as realistic and representative of actual SOC alert triage. Success: Qualitative feedback indicates the environment models real-world operations reasonably well.

### 17.3 Performance Success Metrics

**Runtime Efficiency:** The entire baseline inference script (3 tasks × 8 steps max) runs in <20 minutes on target hardware. Success: Measurement shows <20 min runtime.

**Scalability:** The environment handles 100 concurrent episodes without degradation. Success: Load test shows no performance degradation.

---

## 18. TIMELINE & MILESTONES

### Phase 1: Core Environment Implementation (Days 1-2)

**Deliverables:**
- Data models (Pydantic) for Observation, Action, Reward, etc.
- SOCEnv class with reset(), step(), state() methods
- Scenario generator for easy task (false positive triage)
- Reward computation engine
- Basic logging

**Success Criteria:** Trivial agent (that always dismisses alerts) runs through easy task and achieves non-zero score.

### Phase 2: Task Implementation (Days 2-3)

**Deliverables:**
- Scenario generator for medium task (brute force)
- Scenario generator for hard task (lateral movement)
- Graders for all three tasks
- Ground truth validation

**Success Criteria:** All three tasks generate valid scenarios. Grader correctly scores known-good agent actions.

### Phase 3: API & Server (Days 3-4)

**Deliverables:**
- FastAPI application with /reset, /step, /state endpoints
- Request/response validation
- Error handling
- API documentation (OpenAPI)

**Success Criteria:** API endpoints respond correctly to valid and invalid requests. Postman collection works.

### Phase 4: Deployment (Days 4-5)

**Deliverables:**
- Dockerfile
- Docker image builds successfully
- Hugging Face Space is created and deployed
- Space URL is accessible

**Success Criteria:** docker build and docker run succeed. Space responds to HTTP requests.

### Phase 5: Baseline Agent & Testing (Days 5-6)

**Deliverables:**
- Baseline inference script
- Script runs against deployed environment
- Unit tests for environment components
- Integration tests for full episodes

**Success Criteria:** Baseline script produces [START], [STEP], [END] formatted output. All tests pass.

### Phase 6: Documentation & Validation (Days 6-7)

**Deliverables:**
- README with full documentation
- openenv.yaml metadata file
- This PRD document
- Validator script passes

**Success Criteria:** openenv validate returns zero errors. README includes all required sections. Submission passes pre-validation checks.

---

## 19. RISKS & MITIGATION PLAN

### Risk 1: Reward Function is Too Lenient or Too Strict

**Description:** If the reward function gives too much credit for any action, the agent learns nothing. If it's too strict, it becomes impossible to achieve non-zero rewards.

**Likelihood:** Medium  
**Impact:** High (fails task quality requirement)

**Mitigation:** Calibrate reward function empirically. Run baseline agent multiple times on each task and verify that scores range from 0.2 to 0.9 (not 0.0 or 1.0 for all runs). Adjust reward magnitudes if needed.

### Risk 2: Scenarios are Too Artificial or Unrealistic

**Description:** If the scenarios do not resemble real security alerts, the environment loses real-world utility value.

**Likelihood:** Low (domain expertise on security team)  
**Impact:** High (fails real-world utility requirement)

**Mitigation:** Base scenarios on actual security incidents (e.g., from public incident reports). Include distractors and false positives that match real SOC experience. Get feedback from security practitioners if possible.

### Risk 3: Environment is Too Slow for 20-Minute Runtime Budget

**Description:** If reset() or step() take >1 second, the entire baseline inference script exceeds 20 minutes.

**Likelihood:** Low  
**Impact:** Medium (disqualification if runtime exceeds budget)

**Mitigation:** Implement aggressive memoization and pre-generate all scenarios at startup. Benchmark reset() and step() before submission. Set hard timeouts and alert if latency increases.

### Risk 4: Grader Bugs Produce Incorrect Scores

**Description:** A subtle bug in the grader could cause it to produce consistent but incorrect scores.

**Likelihood:** Medium  
**Impact:** High (invalidates all results)

**Mitigation:** Write comprehensive unit tests for the grader. Test known-good actions and verify they produce expected scores. Use assertions to catch inconsistencies. Have a second person review grader code.

### Risk 5: Docker Image is Too Large or Build Takes Too Long

**Description:** If the Docker image exceeds available disk space or build time exceeds CI timeout, the submission fails validation.

**Likelihood:** Low  
**Impact:** High (disqualification)

**Mitigation:** Use minimal base image (python:3.10-slim, not full python:3.10). Limit dependencies to essential packages. Test docker build locally and verify it completes in <5 minutes.

### Risk 6: LLM Refuses to Solve the Task

**Description:** The LLM (in the baseline agent) may refuse to follow instructions if it perceives the task as harmful or ambiguous.

**Likelihood:** Low  
**Impact:** Medium (baseline agent fails, but environment is still valid)

**Mitigation:** Write a clear system prompt for the LLM explaining the task. Provide examples of good actions. Use a reliable, instruction-following model (GPT-4, Claude, Qwen).

---

## 20. APPENDICES

### Appendix A: OpenEnv Specification Compliance Checklist

- [x] Typed Observation, Action, Reward Pydantic models
- [x] reset() method returns observation and done flag
- [x] step(action) method returns (observation, reward, done, info)
- [x] state() method returns current state
- [x] openenv.yaml with metadata
- [x] Deterministic grading with 0.0-1.0 reward range
- [x] Minimum 3 tasks with difficulty progression
- [x] Meaningful reward function with partial progress signals
- [x] Baseline inference script with OpenAI client
- [x] Dockerfile for containerization
- [x] Hugging Face Spaces deployment
- [x] README with environment description
- [x] openenv validate passes without errors

### Appendix B: Example Alert Scenarios

**Scenario 1: False Positive (Easy)**

Alerts:
1. SQL Injection from 10.0.0.50 (internal testing IP)
2. Brute force from 192.0.2.1 (known Shodan bot)
3. Unusual login from 203.0.203.0 (user on travel)

Ground Truth:
- Alerts 1 & 2 are false positives
- Alert 3 is ambiguous (either action acceptable)

Expected Agent Action: Dismiss alerts 1 & 2, resolve or escalate alert 3.

**Scenario 2: Brute Force (Medium)**

Alerts:
1. Failed login attempts to admin (15 attempts, 5 minutes, multiple IPs)
2. Successful login from one of the attack IPs

Ground Truth:
- Attack IPs: 203.0.113.1, 203.0.113.2, 203.0.113.3, 203.0.113.4
- Successful login is suspicious

Expected Agent Action: Isolate all attack IPs, investigate successful login.

**Scenario 3: Lateral Movement (Hard)**

Alerts:
1. Unusual login from Shanghai (user normally in SF)
2. Sensitive file access (user never accesses this file)
3. API calls from unexpected IP (lateral movement)

Ground Truth:
- This is a coordinated attack (account compromise)
- All three events are connected and suspicious
- Isolate the user account or escalate

Expected Agent Action: Recognize the pattern, isolate the user, fetch comprehensive logs.

### Appendix C: Baseline Inference Script Template

```python
import asyncio
import os
import json
from openai import OpenAI

API_BASE_URL = os.getenv("API_BASE_URL", "https://your-space.hf.space")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

async def run_task(task_name):
    print(f"[START] task={task_name} env=soc-analyst model={MODEL_NAME}")
    
    # Reset environment
    response = requests.post(f"{API_BASE_URL}/reset", json={"task": task_name})
    observation = response.json()["observation"]
    episode_id = response.json()["episode_id"]
    
    rewards = []
    steps_taken = 0
    
    for step in range(1, 9):
        # Get action from LLM
        action_text = get_llm_action(observation)
        action = parse_action(action_text)
        
        # Step environment
        response = requests.post(
            f"{API_BASE_URL}/step",
            json={"episode_id": episode_id, "action": action}
        )
        
        result = response.json()
        reward = result["reward"]
        done = result["done"]
        observation = result["observation"]
        
        rewards.append(reward)
        steps_taken = step
        
        print(f"[STEP] step={step} action={action_text[:50]}... reward={reward:.2f} done={done} error=null")
        
        if done:
            break
    
    # Compute final score
    score = sum(rewards) / max(8 * 2.0, 1.0)
    score = max(0.0, min(1.0, score))
    
    print(f"[END] success={score > 0.5} steps={steps_taken} score={score:.2f} rewards={','.join(f'{r:.2f}' for r in rewards)}")

async def main():
    for task in ["false_positive_triage", "brute_force_defense", "lateral_movement_detection"]:
        await run_task(task)
        
if __name__ == "__main__":
    asyncio.run(main())
```

### Appendix D: Validation Checklist for Submission

Before submitting, verify:

- [ ] Docker builds successfully: `docker build -t soc-analyst .`
- [ ] Docker runs successfully: `docker run -p 7860:7860 soc-analyst`
- [ ] HF Space is deployed and accessible
- [ ] openenv validate passes: `openenv validate`
- [ ] Baseline inference script runs: `python inference.py`
- [ ] All three tasks complete without error
- [ ] README includes all required sections
- [ ] API documentation is complete (/docs endpoint works)
- [ ] Final score is between 0.0 and 1.0 for all tasks
- [ ] Runtime is under 20 minutes for full baseline run
- [ ] Code is well-commented and follows PEP 8
- [ ] No hardcoded API keys or secrets in code

### Appendix E: Post-Submission Considerations

If the submission is selected for further rounds, the following enhancements should be considered:

1. **Advanced Scenarios:** Add scenarios modeling zero-day exploits, supply chain attacks, insider threats, and encrypted malware communications.

2. **Multi-Agent Scenarios:** Support multiple agents working in parallel on the same incident (simulating team-based SOC response).

3. **Real Data Integration:** Connect to real security data sources (Shodan, Censys, MISP) for truly synthetic but realistic alerts.

4. **Feedback from Production SOCs:** Iterate on scenarios based on feedback from enterprise security teams.

5. **Agent Benchmark Database:** Create a leaderboard showing how different agents (GPT-4, Claude, Qwen, custom RL agents) perform on the benchmark.

---

## DOCUMENT APPROVAL & SIGN-OFF

**Prepared by:** Development Team  
**Version:** 1.0  
**Status:** Ready for Implementation  
**Last Review:** April 5, 2026  

This PRD is complete and contains all required sections for hackathon submission. Implementation should proceed according to the timeline specified in Section 18.
