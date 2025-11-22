```markdown
# AgentCoach360 – Technical Features & Architecture

This document deeply describes the engineering behind AgentCoach360, covering all major concepts required by the Kaggle Agents Intensive Capstone.

It focuses on **why** each feature exists, **how** it's implemented, and **what value** it brings to a real coaching workflow.

---

# 1. Multi-Agent Architecture

AgentCoach360 uses several agents that collaborate to produce a final coaching response.

### 1.1 Sequential Reasoning Agents  
The root agent delegates to:

- `manager_coach_agent`
- `agent_coach_agent`

depending on persona.

These agents read the user request, inspect context, and determine what deeper analysis is needed—from CSV trends to coaching explanations.

### 1.2 Parallel Analysis Agents  
Two parallel agents run simultaneously:

- **Trend Analyst Agent**  
  Highlights shifts in sentiment, CSAT dips, positive spikes.

- **Quality Auditor Agent**  
  Checks consistency between recommended actions and KPI data.

Both return results that are merged into the final answer.

Parallel agents reduce latency and produce more balanced recommendations.

### 1.3 Loop Agent  
`weekly_plan_agent` generates a recurring coaching plan.  
When invoked, it:

1. Reads memory history  
2. Determines the last focus area  
3. Suggests continuity or adjustments  
4. Produces a 7-day structured plan  

This simulates realistic management cycles.

---

# 2. Tooling

### 2.1 KPI CSV Tool (Custom Python Tool)
Runs Python code to analyze uploaded survey CSVs:

- counts categories
- detects sentiment shifts
- summarizes themes
- derives focus areas

This mirrors real enterprise BI processes.

### 2.2 Coach Evaluator Tool  
Scores answers on:

- clarity
- empathy
- actionability
- relevance

This enables self-assessment after each coaching session.

### 2.3 Built-In Tools  
The system uses:

- **Python Exec Tool** for KPI code  
- **Google Search (MCP-ready demo)** to show extensibility  
- **Function-call tools** via ADK architecture

### 2.4 OpenAPI Tool  
A minimal connector simulates calling a CRM or support system via OpenAPI.  
Shows how the system could integrate real enterprise workflows.

---

# 3. Sessions & Memory

### 3.1 Session Management  
Using:
The system tracks:

- conversation continuity
- persona
- identifier
- message history

This allows multi-turn reasoning.

### 3.2 Long-Term Memory (SQLite)

AgentCoach360 stores coaching memory per:


Fields:

- last_focus
- last_summary
- last_seen_utc
- total_interactions

This improves personalization over time and enables context compaction.

### 3.3 Context Engineering

The system prepends a compacted memory snippet to new requests:

- keeping history minimal  
- avoiding token bloat  
- preserving key coaching narrative  

This is especially useful for supervisor–team relationships.

---

# 4. Observability

### 4.1 Logging  
Every turn is logged into:

Captured:

- timestamp
- session id
- persona
- identifier
- user message
- raw agent reply (including tools)

### 4.2 Tracing  
Tool usage is displayed in the UI.  
This helps explain “how” the agent reached its answer.

### 4.3 Metrics  
Interaction count is stored per persona/identifier.  
Useful for progression tracking.

---

# 5. Agent Evaluation

Using the coach evaluator tool, the system:

- grades its own coaching answer  
- highlights areas to improve  
- demonstrates model reflection capabilities

This supports better coaching accuracy during live use.

---

# 6. A2A Protocol

AgentCoach360 includes a minimal implementation:

- every evaluation request is stored as an A2A exchange  
- session ID + user message + evaluation response  
- expandable to multi-agent negotiation

This earns the A2A requirement credit while serving a practical auditing purpose.

---

# 7. Deployment

### 7.1 Containerized architecture  
A Dockerfile builds the entire FastAPI + ADK environment.

### 7.2 Google Cloud Run  
The deployed service:

- supports stateless sessions  
- loads memory.sqlite during container runtime  
- injects env vars  
- serves the HTML UI directly  
- scales automatically

This satisfies the bonus deployment award.

---

# 8. Why These Features Matter

Each feature is not only included to satisfy the rubric—it supports a real coaching workflow:

- **multi-agent orchestration** mirrors how supervisors think: multiple viewpoints  
- **tools** replicate analytics, research, and reporting  
- **memory** makes coaching believable and consistent  
- **loop agents** promote weekly accountability  
- **evaluation** ensures transparency  
- **observability** builds trust  
- **deployment** proves the system is usable outside notebooks  

The end result is a system that feels practical, grounded, and extensible—something a real team could adopt.

---


