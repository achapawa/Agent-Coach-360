# AgentCoach360 — Intelligent Coaching for Contact Centers  
### Enterprise Agents Track · Google Agents Intensive Capstone Project

## 1. Problem Statement

Modern contact centers live and breathe survey data. CSAT, NPS, QA scoring, and call-after feedback are central to improving agent performance — but the practical reality inside most operations is messy:

- Supervisors are overwhelmed with raw data.
- Agents rarely receive timely, personalized coaching.
- Insights are buried in dashboards instead of influencing day-to-day behavior.
- Coaching often happens monthly, not continuously.
- Managers lack a unified, narrative-style summary of how their team is doing.

These gaps create an environment where teams work hard but without the guidance needed to move needle on customer experience.

AgentCoach360 exists to bridge that gap.

It acts as a data-aware coaching partner that supervisors and frontline agents can talk to directly. Instead of navigating spreadsheets, BI tools, or dashboards, leaders simply ask questions in natural language:

- “What should my Billing team focus on next week?”  
- “Can you break down the last 30 days for me?”  
- “How am I personally doing on empathy and first-call resolution?”  

AgentCoach360 reads the available survey data, runs parallel analysis agents, incorporates long-term coaching memory, and produces clear, actionable coaching advice.

The goal is to make coaching continuous, consistent, and personalized without adding more overhead to managers’ schedules.

---

## 2. Solution Overview

AgentCoach360 is a multi-agent coaching platform that transforms survey data and conversation context into personalized guidance for both supervisors and agents. It combines:

- **multi-agent orchestration**
- **CSV data analysis tools**
- **Google Search + OpenAPI connectors**
- **long-term memory (SQLite)**
- **sessions/state via ADK**
- **context compaction**
- **coach evaluation tooling**
- **A2A protocol logging**
- **Cloud Run deployment**
- **a clean, modern web UI**

Supervisors and agents interact through a chat experience that feels natural and useful. Behind the scenes, the system coordinates sequential agents, parallel analysts, and loop-style coaching planners.

This design reflects how real-world coaching works: multiple sources of insight, combined into a unified, personalized narrative.

---

## 3. Why Agents?

Traditional dashboards require cognitive effort. Agents shine when:

1. **The user expresses needs in natural language.**  
2. **The system must combine multiple types of intelligence** (analysis, coaching, context, memory).  
3. **The outcome must feel personalized**, not templated.  
4. **A conversation evolves over time**, requiring continuity and state.

AgentCoach360 is exactly the sort of problem that agents are meant to solve.

---

## 4. System Architecture

### 4.1 High-Level Structure

The system is built around a single root agent which delegates to specialized sub-agents:


### 4.2 Tooling

- **CSV KPI tool** — reads and interprets survey data  
- **Python Exec** — for dynamic KPI code  
- **Google Search demo tool (MCP)**  
- **OpenAPI connector** — simulates CRM integration  
- **Memory store (SQLite)** — long-term coaching continuity  
- **A2A Protocol** — logs internal agent-to-agent exchanges  
- **Session service** — multi-turn memory for UI  

---

## 5. Key Features Demonstrated (Capstone Requirements)

This project implements **nine** of the key concepts (minimum required: 3):

- ✔ Multi-agent system (sequential, parallel, loop)
- ✔ Custom tools (CSV analyzer, evaluator)
- ✔ Built-in tools (Python execution)
- ✔ Google Search tool (MCP-style)
- ✔ OpenAPI integration
- ✔ Sessions & state via InMemorySessionService
- ✔ Long-term memory via SQLite (MemoryBank)
- ✔ Context compaction for memory snippets
- ✔ A2A logging of evaluation interactions
- ✔ Observability via CSV logs
- ✔ Cloud Run deployment
- ✔ Modern UI for conversation-based use

This breadth reflects a realistic coaching system, not just a demo.

---

## 6. Value & Impact

The value of AgentCoach360 is simple:

### ✔ **Better coaching with less effort**  
Supervisors get immediate, data-backed recommendations.

### ✔ **Faster understanding of performance trends**  
Parallel analysis agents summarize key problems quickly.

### ✔ **Personalized guidance for each agent or team**  
Memory helps maintain continuity across interactions.

### ✔ **Weekly accountability**  
The loop agent provides ongoing coaching plans.

### ✔ **Explainability**  
Tools used each turn are displayed in the UI.

### ✔ **Scales easily**  
Cloud Run deployment means it can support many users.

---

## 7. Results

The system performs consistently:

- identifies actionable coaching focus areas,
- generates weekly plans,
- produces manager-level or agent-level insights depending on persona,
- adapts over time using memory,
- and self-evaluates coaching quality.

This transforms survey data from static metrics into continuous coaching intelligence.

---

## 8. Attachments (Code & Demo)

- Git Repository: *https://github.com/achapawa/Agent-Coach-360*  
- Deployment: For demo purposes, I have deployed my whole project to *https://agentcoach360-74997962082.us-central1.run.app/*  
- Video Demo: *[YouTube link to be attached]*  

---

## 9. Conclusion

AgentCoach360 demonstrates how a multi-agent AI system can make coaching more human, more data-driven, and more continuous. It blends analytics, memory, context, and conversation into a unified tool aligned with the needs of real contact centers.

What began as a coaching problem becomes a system that elevates every interaction — for supervisors, frontline agents, and the customers they serve.


