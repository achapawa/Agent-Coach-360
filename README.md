# AgentCoach360

AgentCoach360 is a lightweight yet capable multi-agent coaching platform designed to help contact-center leaders and frontline agents turn survey feedback into practical, outcome-driven improvements.

Built as part of the Google Agents Intensive Capstone, AgentCoach360 demonstrates how modern agent architectures can transform raw customer-survey data into weekly coaching plans, personalized insights, and clear performance narratives. It blends multiple AI agents, structured tools, memory, and context engineering into a compact, deployable system that can run locally or on Google Cloud Run.

---

## Why This Project Exists

Every contact center relies on surveys—CSAT, NPS, QA reviews, or post-call feedback—to understand how customers actually experience their service. Yet turning all that data into coaching takes time:

- supervisors rarely have enough hours to analyze trends,
- agents don’t get timely performance insights,
- coaching conversations are inconsistent,
- data sits unused until monthly review cycles.

AgentCoach360 reframes this entire workflow.

Instead of digging through CSVs, dashboards, and scores, leaders can simply ask:

> *“What should my Billing team focus on next week?”*

Or a frontline representative can ask:

> *“How have I been doing over the last 30 days?”*

Behind the scenes, the system orchestrates parallel agents for analysis, sequential agents for reasoning, and loop agents for coaching plans—returning answers shaped by data, memory, and past interactions.

---

## What AgentCoach360 Does

AgentCoach360 acts as a real-time “coaching partner” that can:

### ✔ Analyze survey CSVs using a Python KPI tool  
Find trends, strengths, and recurring issues in the last 30–60 days.

### ✔ Provide tailored insights for either managers or frontline agents  
The persona classifier adjusts depth, terminology, and tone.

### ✔ Track progression using long-term memory  
Each team or agent builds a coaching profile over time.

### ✔ Generate weekly coaching plans  
A loop-style agent looks at improvements, regressions, and patterns.

### ✔ Run parallel analysis (quality, sentiment, trend analysts)  
These agents inform the final coaching summary.

### ✔ Provide a built-in evaluation mode  
A scoring tool audits clarity, empathy, and actionability of the answer.

### ✔ Support tools like Google Search, OpenAPI connectors, CSV parsing, and code execution  
Demonstrating real-world extensibility.

### ✔ Provide audit logs, session continuity, and A2A protocol support  
You can trace how each answer was assembled—critical for enterprise trust.

### ✔ Run through a clean, modern web interface  
Managers and agents can simply chat with the system.

---

## Architecture Overview

AgentCoach360 is built on the ADK (Agent Development Kit) and the Vertex AI Agents runtime, with a focus on modularity:


Persistent memory is stored in **SQLite** using a custom long-term memory bank.  
Observability is tracked through CSV logs.  
Deployment uses a Docker container pushed to **Google Cloud Run**.

---

## Demonstrated Capstone Concepts

AgentCoach360 intentionally incorporates a broad range of the required technologies:

- Multi-agent system (parallel, sequential, loop)
- Custom tools (CSV KPI tool, evaluator)
- Built-in tools (Python execution)
- OpenAPI-ready connectors
- MCP-ready search tool demonstration
- Long-running operations
- Session/state management (InMemorySessionService)
- Long-term memory (SQLite)
- Context engineering (dynamic memory compaction)
- Observability (log records)
- Agent evaluation
- A2A Protocol
- Cloud Run deployment

This project doesn’t just check boxes—it blends these parts into a natural coaching workflow.

---

## Who It’s For

- **Supervisors** who need personalized weekly guidance for their team.
- **Frontline agents** who want feedback anytime.
- **Analysts** who want to automate routine performance reviews.
- **Organizations** looking for low-cost, practical AI coaching tools.

AgentCoach360 aims to capture the essence of the capstone objective: a real, useful system powered by agents—not a demo, not an experiment, but something that could genuinely help teams grow.

---

## Repository Structure
frontend (HTML/JS)
|
fastapi backend (web_app.py)
|
ADK Runner (session + state)
|
root_agent
├── manager_coach_agent
├── agent_coach_agent
├── trend_analyst_agent (parallel)
├── quality_auditor_agent (parallel)
├── weekly_plan_agent (loop)
└── coach_evaluator_agent

/agentcoach360_backend
agent.py # root agent + multi-agent orchestration
tools/ # CSV analysis, evaluator, search, openapi, etc.
memory_store.py # SQLite long-term memory
a2a_protocol.py # A2A exchange recording
/web_app.py # FastAPI backend + UI
/data/ # memory.sqlite and logs
Dockerfile
README.md
ProjectStartup.md
Features.md

---

## Status

AgentCoach360 is fully functional:

- runs locally,
- deploys to Cloud Run,
- includes a modern interface,
- demonstrates every major ADK concept.

It is intentionally compact and readable, making it ideal for learning, extension, or real-world use.

---

## License

This project is submitted as part of the Kaggle Agents Intensive Capstone.  
You may use it for educational or organizational purposes.

---

