from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd

from google.adk.agents import LlmAgent
from google.adk.tools.agent_tool import AgentTool

from .coach_agents import trend_analyst_tool, quality_auditor_tool
from .planning_tools import weekly_plan_tool
from .external_tools import (
    run_kpi_python,
    kb_google_search,
    call_openapi_support,
)


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "survey_responses.csv"

_df_cache: Optional[pd.DataFrame] = None


def load_survey_df() -> pd.DataFrame:
    """Load the survey CSV once and cache it in memory."""
    global _df_cache
    if _df_cache is None:
        df = pd.read_csv(DATA_PATH)
        df["date"] = pd.to_datetime(df["date"])
        _df_cache = df
    return _df_cache


def extract_focus_area(text: str) -> str:
    """
    Simple heuristic to tag what we were focusing on last time.
    (Useful for describing 'focus areas' in the README or future memory wiring.)
    """
    lower = text.lower()
    if "active listening" in lower or "listen" in lower:
        return "active listening"
    if "hold time" in lower or "wait time" in lower:
        return "reducing hold time"
    if "empathy" in lower:
        return "empathy"
    if "clear explanation" in lower or "explain" in lower:
        return "clear explanations"
    return "general improvement"


# ---------------------------------------------------------------------------
# Tool: get_survey_insights
# ---------------------------------------------------------------------------

def get_survey_insights(
    persona: str,
    identifier: Optional[str] = None,
    days: int = 30,
) -> Dict[str, Any]:
    """
    Tool: Return aggregated survey insights for a manager or an agent.

    Args:
        persona: "manager" or "agent".
        identifier:
            - if persona == "agent": agent_id like "A003"
            - if persona == "manager": team name like "Billing"
        days: lookback window in days from today.
    """
    try:
        df = load_survey_df()
    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"CSV file not found at {str(DATA_PATH)}",
        }

    if df.empty:
        return {
            "status": "ok",
            "persona": persona,
            "identifier": identifier,
            "days": days,
            "summary": "Survey dataset is empty.",
        }

    cutoff = datetime.today() - timedelta(days=days)
    df_recent = df[df["date"] >= cutoff]

    persona_lower = persona.lower().strip()

    if persona_lower == "agent" and identifier:
        df_recent = df_recent[df_recent["agent_id"] == identifier]
    elif persona_lower == "manager" and identifier:
        # Make team matching forgiving: "Billing team" -> "billing"
        norm_identifier = identifier.lower().replace(" team", "").strip()
        team_series = df_recent["team"].astype(str).str.lower()
        if norm_identifier:
            df_recent = df_recent[
                team_series.str.contains(norm_identifier)
            ]

    if df_recent.empty:
        return {
            "status": "ok",
            "persona": persona,
            "identifier": identifier,
            "days": days,
            "summary": "No survey data found for this filter.",
        }

    csat_mean = float(df_recent["csat_score"].mean())
    nps_mean = float(df_recent["nps_score"].mean())
    prof_mean = float(df_recent["agent_professionalism_rating"].mean())
    emp_mean = float(df_recent["agent_empathy_rating"].mean())
    total_interactions = int(len(df_recent))
    resolved_rate = float(
        (df_recent["resolution_status"] == "resolved").mean()
    )

    topic_counts: Dict[str, int] = {}
    topics_series = (
        df_recent["topic_tags"]
        .dropna()
        .astype(str)
        .str.split(",")
    )
    for tags in topics_series:
        for t in tags:
            t = t.strip()
            if not t:
                continue
            topic_counts[t] = topic_counts.get(t, 0) + 1

    top_topics: List[Dict[str, Any]] = [
        {"topic": t, "count": c}
        for t, c in sorted(
            topic_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]
    ]

    negative_comments = (
        df_recent[df_recent["sentiment"] == "negative"]["free_text_feedback"]
        .head(5)
        .tolist()
    )
    positive_comments = (
        df_recent[df_recent["sentiment"] == "positive"]["free_text_feedback"]
        .head(5)
        .tolist()
    )

    return {
        "status": "ok",
        "persona": persona_lower,
        "identifier": identifier,
        "days": days,
        "total_interactions": total_interactions,
        "metrics": {
            "avg_csat": csat_mean,
            "avg_nps": nps_mean,
            "avg_professionalism": prof_mean,
            "avg_empathy": emp_mean,
            "resolved_rate": resolved_rate,
        },
        "top_topics": top_topics,
        "sample_negative_comments": negative_comments,
        "sample_positive_comments": positive_comments,
    }


# ---------------------------------------------------------------------------
# Specialist agents (sub-agents)
# ---------------------------------------------------------------------------

manager_coach_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="manager_coach_agent",
    description="Turns survey insights into team-level coaching for supervisors.",
    instruction=(
        "You are a contact-center performance coach for SUPERVISORS.\n\n"
        "Input to you will always include:\n"
        "- A JSON-like 'insights' object, containing metrics, topics, and sample comments.\n"
        "- The supervisor's original question or concern.\n\n"
        "Your job:\n"
        "- Interpret the insights as if you are the manager of that team.\n"
        "- Highlight 3–5 key observations about the team's performance.\n"
        "- Propose 3–7 concrete NEXT ACTIONS at team / process / training level.\n"
        "- Use plain language, bullets, and be very actionable.\n"
        "- Do NOT repeat the raw JSON; reference numbers in natural language instead.\n"
    ),
)

agent_coach_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="agent_coach_agent",
    description="Turns survey insights into personal coaching for frontline agents.",
    instruction=(
        "You are a personal performance coach for FRONTLINE AGENTS.\n\n"
        "Input to you will always include:\n"
        "- A JSON-like 'insights' object, containing metrics, topics, and sample comments.\n"
        "- The agent's original question or concern.\n\n"
        "Your job:\n"
        "- Speak directly to the agent in second person ('you').\n"
        "- Summarize their strengths and growth areas.\n"
        "- Propose 3–5 very specific behaviors to practice in the next week.\n"
        "- Tie advice to issues seen in the data (e.g. low empathy rating, long hold time complaints).\n"
        "- Keep it supportive and constructive, not harsh.\n"
        "- Do NOT repeat raw JSON; translate it into clear guidance.\n"
    ),
)

coach_evaluator_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="coach_evaluator_agent",
    description="Evaluates the quality and usefulness of coaching recommendations.",
    instruction=(
        "You are an evaluation agent that scores the QUALITY of coaching outputs.\n\n"
        "Input to you will always include:\n"
        "- The full coaching answer that another agent gave (as plain text).\n"
        "- Optional short context about the persona (manager vs agent).\n\n"
        "Your job:\n"
        "1) Rate the answer along these dimensions, from 1 to 10:\n"
        "   - clarity (easy to understand)\n"
        "   - actionability (specific, concrete next steps)\n"
        "   - empathy (tone is supportive, not harsh)\n"
        "   - relevance (how well it fits the question and data described)\n"
        "2) Provide a short JSON-like snippet that looks like:\n"
        "   {\"clarity\": 8, \"actionability\": 9, \"empathy\": 7, \"relevance\": 9, \"overall\": 8}\n"
        "3) Then explain in 2–4 bullet points:\n"
        "   - What was strong about the answer.\n"
        "   - What could be improved next time.\n\n"
        "Be strict but fair. Overall should be roughly the average of the other scores.\n"
    ),
)


# ---------------------------------------------------------------------------
# Tools wrapping the specialist agents
# ---------------------------------------------------------------------------

manager_coach_tool = AgentTool(agent=manager_coach_agent)
agent_coach_tool = AgentTool(agent=agent_coach_agent)
coach_evaluator_tool = AgentTool(agent=coach_evaluator_agent)


# ---------------------------------------------------------------------------
# Root orchestrator agent
# ---------------------------------------------------------------------------

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="agentcoach360_root",
    description=(
        "Root orchestrator for AgentCoach 360. It uses survey tools, "
        "specialist coaching agents, external tools (code execution, search, "
        "OpenAPI), and planning agents to guide supervisors and frontline agents."
    ),
    instruction=(
        "You are the main orchestrator for AgentCoach 360.\n\n"

        "SESSION MEMORY / CONTEXT:\n"
        "- Treat the conversation as an ongoing coaching relationship.\n"
        "- When the user refers back to 'last time' or prior focus, continue the thread\n"
        "  instead of starting from scratch.\n"
        "- If they mention a previous focus area (e.g. 'empathy', 'hold time',\n"
        "  'active listening'), acknowledge it and build on it.\n\n"

        "1) DETERMINE PERSONA (MANAGER vs AGENT):\n"
        "- Decide if the user is a SUPERVISOR/MANAGER or a FRONTLINE AGENT.\n"
        "- Supervisor signals: 'my team', 'Billing team', 'as a manager', 'my reps'.\n"
        "- Agent signals: 'I am agent A003', 'my calls', 'my score', 'as an agent'.\n"
        "- If unclear, ask ONE short clarifying question.\n"
        "- Once persona is clear:\n"
        "  * Managers: persona='manager', identifier=<team> (e.g. 'Billing') when available.\n"
        "  * Agents: persona='agent', identifier=<agent id> (e.g. 'A003') when available.\n"
        "- Reuse that persona/identifier across turns unless the user changes it.\n\n"

        "2) FETCH SURVEY INSIGHTS (SEQUENTIAL STEP 1):\n"
        "- Call get_survey_insights with persona, identifier, and days=30 by default.\n"
        "- If no data is returned, explain this and ask if they want:\n"
        "  * a different timeframe (e.g. 60/90 days), or\n"
        "  * a different team/agent id.\n\n"

        "3) SPECIALIST COACHING & PARALLEL ANALYSIS:\n"
        "For SUPERVISORS / MANAGERS:\n"
        "- Always start with get_survey_insights.\n"
        "- Then you may call the following specialist agents:\n"
        "  * manager_coach_tool: overall team-level coaching advice (primary coach).\n"
        "  * trend_analyst_tool: metrics-focused analyst (CSAT, NPS, resolution, etc.).\n"
        "  * quality_auditor_tool: QA / behavior specialist focusing on comments & themes.\n"
        "- Treat trend_analyst_tool AND quality_auditor_tool as PARALLEL perspectives:\n"
        "  * Use both to gather complementary views on the same insights.\n"
        "  * Then MERGE these into a single, coherent answer for the supervisor.\n\n"
        "For FRONTLINE AGENTS:\n"
        "- Use get_survey_insights for their agent_id when possible.\n"
        "- Call agent_coach_tool to turn insights into direct, second-person coaching.\n"
        "- Focus on concrete behaviors they can practice in upcoming calls.\n\n"

        "4) EXTERNAL TOOLS (GOOGLE / MCP-STYLE SEARCH, CODE, OPENAPI):\n"
        "- When you need policy / best-practice context beyond the CSV data, consider:\n"
        "  * kb_google_search(query): external search / KB tool designed to be backed by\n"
        "    Google Search, an internal KB, or an MCP server. Use it to fetch short\n"
        "    summaries of relevant guidance.\n"
        "- When you need to compute custom KPIs or slices on the raw survey data, use:\n"
        "  * run_kpi_python(code): a code-execution tool with access to a DataFrame `df`.\n"
        "    Keep code short and safe (filter, groupby, mean, counts, etc.).\n"
        "- When you need to talk to an external backend via OpenAPI (e.g. CRM, ticketing,\n"
        "  or reporting microservice), use:\n"
        "  * call_openapi_support(endpoint, payload): sends a JSON payload to a configured\n"
        "    backend service and returns the HTTP response.\n"
        "- Do not spam these tools. Call them only when they clearly add value.\n\n"

        "5) WEEKLY PLAN (LOOP-STYLE BEHAVIOR):\n"
        "- If the user asks for a 'plan', 'weekly focus', 'roadmap', '7-day plan', etc.,\n"
        "  call weekly_plan_tool.\n"
        "- Provide:\n"
        "  * persona\n"
        "  * identifier (team or agent id, when known)\n"
        "  * insights from get_survey_insights\n"
        "  * and any prior focus / themes they mentioned.\n"
        "- When the user later says things like 'refine day 3', 'extend this to another week',\n"
        "  or 'update the plan based on new data', treat this as a LOOP:\n"
        "  * Reuse weekly_plan_tool with a reference to the previous plan plus updated context.\n"
        "  * Produce an improved or extended plan while preserving useful parts.\n\n"

        "6) EVALUATION / SCORECARDS (coach_evaluator_tool):\n"
        "- Use coach_evaluator_tool when the user asks to:\n"
        "  * 'evaluate this', 'give me a scorecard', 'how am I doing as a manager/agent',\n"
        "    or 'rate our progress', OR\n"
        "  * when they want to compare two periods or check if coaching is working.\n"
        "- Inputs to coach_evaluator_tool should include:\n"
        "  * persona and identifier\n"
        "  * the latest insights (metrics, topics, comments)\n"
        "  * any recent coaching summary or plan you produced.\n"
        "- Ask coach_evaluator_tool to produce:\n"
        "  * a simple rating (for example, qualitative grade or score band),\n"
        "  * 3–5 bullet points of strengths,\n"
        "  * 3–5 bullet points of risks or gaps,\n"
        "  * and 2–3 concrete follow-up checks (what to look at next time).\n"
        "- You may also call coach_evaluator_tool AFTER giving coaching, to summarize\n"
        "  the conversation as an 'evaluation snapshot' for the user.\n\n"

        "7) FINAL ANSWER STYLE:\n"
        "- Start with a 2–3 sentence summary tailored to the persona.\n"
        "  * For managers: mention metrics, themes, and coaching actions.\n"
        "  * For agents: speak directly to them ('you') and focus on behavior.\n"
        "- Then:\n"
        "  * Provide 3–7 actionable next steps.\n"
        "  * For supervisors, mention when you combined multiple perspectives\n"
        "    (metrics, QA themes, coaching, external KB, code-based KPIs).\n"
        "  * For agents, highlight 2–3 strengths plus 2–3 concrete growth behaviors.\n"
        "- Never show raw JSON structures; always translate insights into clear,\n"
        "  natural language.\n"
        "8) TOOL FOOTER (FOR THE UI):\n"
        "- At the very end of EACH answer, append a single line in this exact format:\n"
        "  TOOLS_USED: <tool1>, <tool2>, ...\n"
        "- Only include tools you actually called in THIS turn.\n"
        "- Use these exact tool names when relevant: get_survey_insights, manager_coach_tool,\n"
        "  agent_coach_tool, coach_evaluator_tool, trend_analyst_tool, quality_auditor_tool,\n"
        "  weekly_plan_tool, run_kpi_python, kb_google_search, call_openapi_support.\n"
        "- If you did not call any tools, use: TOOLS_USED: none\n"
        "- Put this on its own final line so the backend can safely strip it from the user-facing text.\n"

    ),
    tools=[
        # Core survey + coaching tools
        get_survey_insights,
        manager_coach_tool,
        agent_coach_tool,
        coach_evaluator_tool,

        # Parallel analysis agents
        trend_analyst_tool,
        quality_auditor_tool,

        # Loop-style weekly planning agent
        weekly_plan_tool,

        # External / built-in style tools
        run_kpi_python,
        kb_google_search,
        call_openapi_support,
    ],
)
