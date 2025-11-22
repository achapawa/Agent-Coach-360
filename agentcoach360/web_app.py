from __future__ import annotations

from pathlib import Path
from typing import Optional
from datetime import datetime
import csv

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv 

from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types

# Import existing root agent
from agentcoach360_backend.agent import root_agent, extract_focus_area
from agentcoach360_backend.memory_store import memory_store
from agentcoach360_backend.a2a_protocol import record_a2a_exchange


# Load GOOGLE_API_KEY from backend/.env so ADK's Gemini client can see it
BASE_DIR = Path(__file__).resolve().parent
BACKEND_ENV = BASE_DIR / "agentcoach360_backend" / ".env"
load_dotenv(BACKEND_ENV)

# Logging: store every interaction for observability / eval
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "interactions.csv"

# -----------------------------------------------------------------------------
# FastAPI app setup
# -----------------------------------------------------------------------------
app = FastAPI(
    title="AgentCoach 360",
    description="Simple web UI for the AgentCoach 360 multi-agent system.",
    version="0.1.0",
)

# ADK session + runner
session_service = InMemorySessionService()
runner = Runner(
    agent=root_agent,
    app_name="agentcoach360_app",
    session_service=session_service,
)


# -----------------------------------------------------------------------------
# Request / response models for /chat
# -----------------------------------------------------------------------------
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    persona: Optional[str] = None  # "manager" or "agent"
    identifier: Optional[str] = None  # e.g. "Billing" or "A003"
    message: str
    is_eval: Optional[bool] = False



class ChatResponse(BaseModel):
    session_id: str
    reply: str
    tools: list[str] | None = None

def append_log_entry(
    *,
    session_id: str,
    persona: str,
    identifier: Optional[str],
    is_eval: bool,
    user_message: str,
    agent_reply: str,
) -> None:
    """Append a single interaction row to logs/interactions.csv."""
    is_new_file = not LOG_FILE.exists()

    with LOG_FILE.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new_file:
            writer.writerow(
                [
                    "timestamp_utc",
                    "session_id",
                    "persona",
                    "identifier",
                    "is_eval",
                    "user_message",
                    "agent_reply",
                ]
            )

        writer.writerow(
            [
                datetime.utcnow().isoformat(),
                session_id,
                persona or "",
                identifier or "",
                "1" if is_eval else "0",
                user_message.replace("\n", "\\n"),
                agent_reply.replace("\n", "\\n"),
            ]
        )

# -----------------------------------------------------------------------------
# HTML UI (single page, inline CSS + JS)
# -----------------------------------------------------------------------------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>AgentCoach 360</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">

  <style>
    :root {
      --bg: #0b1020;
      --card: #141a33;
      --accent: #3cb0c7;
      --accent-soft: rgba(60, 176, 199, 0.15);
      --text: #f9fafb;
      --muted: #9ca3af;
      --danger: #f97373;
      --shadow-soft: 0 18px 35px rgba(0,0,0,0.45);
      --radius-lg: 18px;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      padding: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: radial-gradient(circle at top, #1f2937 0, #020617 60%);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }
        .hero-line {
      text-align: center;
      font-size: 13px;
      color: var(--muted);
      margin-bottom: 10px;
      max-width: 900px;
      margin-left: auto;
      margin-right: auto;
      letter-spacing: 0.02em;
    }

    .hero-line .hero-prefix {
      font-weight: 600;
      color: #e5e7eb;
    }

    .hero-line .hero-prefix span {
      background: linear-gradient(120deg, #3cb0c7, #a855f7, #f97316);
      background-size: 200% 200%;
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
      animation: brandGlow 4.5s ease-in-out infinite;
    }


    .shell {
      width: 100%;
      max-width: 1080px;
      padding: 16px; /* less padding so UI feels larger */
    }

    .layout {
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr);
      gap: 18px;
    }

    @media (max-width: 900px) {
      .layout {
        grid-template-columns: 1fr;
      }
    }

    .panel {
      background: linear-gradient(145deg, rgba(15,23,42,0.98), rgba(15,23,42,0.9));
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-soft);
      border: 1px solid rgba(148,163,184,0.25);
      padding: 16px 18px; /* slightly tighter padding */
    }

    .panel-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 10px;
    }

    .title {
      font-size: 20px;
      font-weight: 600;
      letter-spacing: 0.03em;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .brand-title {
      background: linear-gradient(120deg, #3cb0c7, #a855f7, #f97316);
      background-size: 200% 200%;
      -webkit-background-clip: text;
      background-clip: text;
      color: transparent;
      animation: brandGlow 4.5s ease-in-out infinite;
      position: relative;
    }

    @media (max-width: 640px) {
      .brand-title::after {
        display: none;
      }
    }

    @keyframes brandGlow {
      0% {
        background-position: 0% 50%;
        text-shadow: 0 0 8px rgba(56,189,248,0.4);
      }
      50% {
        background-position: 100% 50%;
        text-shadow: 0 0 15px rgba(168,85,247,0.6);
      }
      100% {
        background-position: 0% 50%;
        text-shadow: 0 0 8px rgba(56,189,248,0.4);
      }
    }

    .badge {
      font-size: 11px;
      padding: 3px 8px;
      border-radius: 999px;
      background: rgba(15, 118, 110, 0.18);
      color: #a7f3d0;
      border: 1px solid rgba(45,212,191,0.4);
      animation: badgeFloat 4s ease-in-out infinite;
    }

    @keyframes badgeFloat {
      0%, 100% {
        transform: translateY(0);
      }
      50% {
        transform: translateY(-2px);
      }
    }

    .subtitle {
      font-size: 13px;
      color: var(--muted);
      margin-bottom: 10px;
    }

    .tagline {
      font-size: 12px;
      color: #e5e7eb;
      opacity: 0.9;
      display: inline-block;
      animation: taglineFade 5s ease-in-out infinite;
    }

    @keyframes taglineFade {
      0%, 100% { opacity: 0.6; }
      40% { opacity: 1; }
    }

    .field-group {
      margin-bottom: 14px;
    }

    .field-label {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin-bottom: 4px;
    }

    .persona-options {
      display: flex;
      gap: 8px;
    }

    .pill {
      flex: 1;
      border-radius: 999px;
      padding: 7px 10px;
      border: 1px solid rgba(148,163,184,0.4);
      font-size: 13px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      cursor: pointer;
      background: rgba(15,23,42,0.7);
      color: var(--muted);
      transition: all 0.15s ease;
    }

    .pill span.icon {
      font-size: 15px;
    }

    .pill.selected {
      border-color: var(--accent);
      background: var(--accent-soft);
      color: var(--text);
      box-shadow: 0 0 0 1px rgba(56,189,248,0.6);
    }

    .pill:hover {
      border-color: var(--accent);
    }

    .input {
      width: 100%;
      border-radius: 999px;
      border: 1px solid rgba(148,163,184,0.55);
      background: rgba(15,23,42,0.8);
      color: var(--text);
      padding: 7px 11px;
      font-size: 13px;
      outline: none;
      transition: border-color 0.1s ease, box-shadow 0.1s ease, background 0.1s ease;
    }

    .input::placeholder {
      color: #6b7280;
    }

    .input:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 1px rgba(56,189,248,0.85);
      background: rgba(15,23,42,0.95);
    }

    .hint {
      font-size: 11px;
      color: #6b7280;
      margin-top: 3px;
    }

    .chip-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 6px;
    }

    .chip {
      font-size: 11px;
      padding: 3px 7px;
      border-radius: 999px;
      background: rgba(51,65,85,0.8);
      color: #e5e7eb;
    }

    .chip strong {
      color: #a5b4fc;
      font-weight: 500;
    }

    .primary-btn, .ghost-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      border-radius: 999px;
      border: none;
      cursor: pointer;
      font-size: 13px;
      padding: 8px 12px;
      white-space: nowrap;
      transition: all 0.15s ease;
    }

    .primary-btn {
      background: linear-gradient(135deg, #3cb0c7, #14819e);
      color: white;
      box-shadow: 0 10px 25px rgba(8,47,73,0.55);
    }

    .primary-btn:hover {
      filter: brightness(1.08);
      transform: translateY(-0.5px);
    }

    .primary-btn:active {
      transform: translateY(0);
      box-shadow: 0 5px 15px rgba(8,47,73,0.5);
    }

    .ghost-btn {
      background: transparent;
      color: var(--muted);
      border: 1px dashed rgba(148,163,184,0.6);
    }

    .ghost-btn:hover {
      border-style: solid;
      color: var(--text);
    }

    .panel-footer {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      margin-top: 6px;
    }

    .status {
      font-size: 16px; /* slightly larger status text */
      color: var(--muted);
    }

    .status span.dot {
      display: inline-block;
      width: 9px;
      height: 9px;
      border-radius: 999px;
      background: #22c55e;
      margin-right: 4px;
      box-shadow: 0 0 0 3px rgba(34,197,94,0.25);
    }

    .status span.dot.off {
      background: #f97373;
      box-shadow: 0 0 0 3px rgba(239,68,68,0.25);
    }

    .status-text.thinking {
      font-weight: 700;
    }

    /* Chat panel */

    .chat-panel {
      display: flex;
      flex-direction: column;
      height: 520px;
    }

    .messages {
      flex: 1;
      border-radius: 15px;
      border: 1px solid rgba(148,163,184,0.4);
      background: radial-gradient(circle at top left, rgba(34,197,235,0.08), rgba(15,23,42,0.9));
      padding: 10px 12px;
      overflow-y: auto;
      font-size: 13px;
    }

    .bubble-row {
      margin-bottom: 8px;
      display: flex;
    }

    .bubble-row.user {
      justify-content: flex-end;
    }

    .bubble-row.agent {
      justify-content: flex-start;
    }

    .bubble {
      max-width: 75%;
      padding: 8px 10px;
      border-radius: 14px;
      line-height: 1.4;
      white-space: pre-wrap;
      word-wrap: break-word;
    }

    .bubble.user {
      background: linear-gradient(135deg, #4f46e5, #0ea5e9);
      color: white;
      border-bottom-right-radius: 4px;
    }

    .bubble.agent {
      background: rgba(15,23,42,0.9);
      color: var(--text);
      border: 1px solid rgba(148,163,184,0.5);
      border-bottom-left-radius: 4px;
    }

    .bubble-header {
      font-size: 11px;
      font-weight: 600;
      margin-bottom: 2px;
      opacity: 0.8;
    }

    .bubble.agent .bubble-header {
      color: #a5b4fc;
    }

    .bubble.user .bubble-header {
      color: #e0f2fe;
    }

    .composer {
      margin-top: 10px;
      display: flex;
      gap: 8px;
      align-items: center;
    }

    .composer textarea {
      flex: 1;
      border-radius: 14px;
      border: 1px solid rgba(148,163,184,0.55);
      background: rgba(15,23,42,0.9);
      padding: 8px 10px;
      font-size: 13px;
      color: var(--text);
      resize: none;
      height: 46px;
      outline: none;
    }

    .composer textarea::placeholder {
      color: #6b7280;
    }

    .composer textarea:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 1px rgba(56,189,248,0.85);
    }

    .thinking-inline {
      font-size: 16px;
      color: var(--muted);
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .thinking-inline::before {
      content: "●";
      font-size: 14px;
      color: var(--accent);
      animation: pulse 1.2s ease-in-out infinite;
    }

    @keyframes pulse {
      0% { opacity: 0.4; transform: scale(0.9); }
      50% { opacity: 1; transform: scale(1.0); }
      100% { opacity: 0.4; transform: scale(0.9); }
    }


    .toolbar {
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      margin-top: 4px;
      font-size: 11px;
      color: var(--muted);
      justify-content: space-between;
      align-items: center;
    }

    .toolbar span.hint {
      font-size: 11px;
      color: var(--muted);
    }

    .eval-btn {
      border-radius: 999px;
      border: none;
      background: rgba(30,64,175,0.5);
      color: #c7d2fe;
      padding: 5px 9px;
      font-size: 11px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      transition: all 0.12s ease;
    }

    .eval-btn:hover {
      background: rgba(30,64,175,0.85);
      color: white;
    }

        .tool-row {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
      width: 100%;
    }

    .tool-indicator {
      display: none; /* shown dynamically when tools are present */
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
      font-size: 11px;
      color: var(--muted);
    }

    .tool-label {
      font-weight: 500;
      color: #e5e7eb;
    }

    .tool-pill {
      padding: 2px 7px;
      border-radius: 999px;
      border: 1px solid rgba(148,163,184,0.6);
      background: rgba(15,23,42,0.9);
      color: #e5e7eb;
      font-size: 11px;
    }


    .error {
      color: var(--danger);
      font-size: 11px;
      margin-top: 4px;
    }

    /* Toast notification */

    .toast {
      position: fixed;
      bottom: 16px;
      left: 50%;
      transform: translateX(-50%) translateY(20px);
      background: rgba(15,23,42,0.95);
      color: var(--text);
      padding: 8px 14px;
      border-radius: 999px;
      font-size: 12px;
      border: 1px solid rgba(56,189,248,0.7);
      box-shadow: 0 12px 30px rgba(0,0,0,0.45);
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.2s ease-out, transform 0.2s ease-out;
      z-index: 50;
    }

    .toast.show {
      opacity: 1;
      pointer-events: auto;
      transform: translateX(-50%) translateY(0);
    }
  </style>
</head>
<body>
  <div class="shell">
    <div id="toast" class="toast"></div>

    <!-- Hero line above both panels -->
    <div class="hero-line">
      <span class="hero-prefix"><span>AgentCoach 360</span></span>
      &nbsp;is a small but powerful tool for companies that rely on survey data to improve customer satisfaction.
    </div>

    <div class="layout">
      <!-- Left: persona + context -->
      <div class="panel">
        <div class="panel-header">
          <div>
            <div class="title">
              <span class="brand-title">AgentCoach 360</span>
              <span class="badge">Survey → Coaching</span>
            </div>
            <div class="subtitle">
              <span class="tagline">Small yet powerful coaching for modern enterprises.</span>
            </div>
          </div>
        </div>

        <div class="field-group">
          <div class="field-label">Persona</div>
          <div class="persona-options">
            <button type="button" class="pill selected" data-persona="manager">
              <span class="icon">👩‍💼</span>
              Manager / Supervisor
            </button>
            <button type="button" class="pill" data-persona="agent">
              <span class="icon">🎧</span>
              Frontline Agent
            </button>
          </div>
          <div class="hint">
            This helps the agent decide whether to coach at team level or individual level.
          </div>
        </div>

        <div class="field-group">
          <div class="field-label">Team / Agent ID (optional)</div>
          <input id="identifier-input" class="input" placeholder="e.g. Billing   or   A003" />
          <div class="hint">
            You can leave this blank and mention your team or agent ID directly in chat instead.
          </div>
        </div>

        <div class="field-group">
          <div class="field-label">Quick Prompts</div>
          <div class="chip-row">
            <div class="chip">Manager • <strong>Last 30 days focus</strong></div>
            <div class="chip">Agent • <strong>How am I doing?</strong></div>
            <div class="chip"><strong>Coaching plan</strong> for next week</div>
            <div class="chip">Ask for <strong>evaluation scores</strong></div>
          </div>
        </div>

        <div class="field-group">
          <div class="field-label">Under the hood</div>
          <div class="hint">
            AgentCoach 360 quietly uses multiple agents and tools each time it answers.
          </div>
          <div class="chip-row" style="margin-top: 6px;">
            <div class="chip"><strong>Multi-agent</strong> coaching & analysis</div>
            <div class="chip"><strong>KPI code</strong> on survey CSV</div>
            <div class="chip"><strong>Loop plans</strong> for weekly focus</div>
            <div class="chip"><strong>Search / OpenAPI</strong> connector ready</div>
          </div>
        </div>


        <div class="panel-footer">
          <div class="status">
            <span class="dot" id="status-dot"></span>
            <span id="status-text" class="status-text">Ready – no session yet</span>
          </div>

          <div>
            <button type="button" class="ghost-btn" id="reset-btn">
              Reset session
            </button>
          </div>
        </div>

        <div id="error-panel" class="error" style="display:none;"></div>
      </div>

      <!-- Right: chat panel -->
      <div class="panel chat-panel">
        <div class="panel-header">
          <div>
            <div class="title" style="font-size: 17px;">
              Conversation
            </div>
            <div class="subtitle">
              Ask things like “What should my team focus on next?” or “How did I do last month?”
            </div>
          </div>
        </div>

        <!-- Thinking indicator now lives in the chat area -->
        <div id="thinking-indicator" class="thinking-inline" style="display:none;">
          Thinking…
        </div>

        <div id="messages" class="messages"></div>

        <div class="composer">
          <textarea id="message-input" placeholder="Type your question or coaching request here..."></textarea>
          <button type="button" class="primary-btn" id="send-btn">
            Send
          </button>
        </div>

        <div class="toolbar">
          <span class="hint">
            Tip: After any answer, click “Evaluate last coaching” to get quality scores.
          </span>
          <div class="tool-row">
            <div class="tool-indicator" id="tool-indicator">
              <span class="tool-label">Tools used this turn:</span>
              <span id="tool-list"></span>
            </div>
            <button type="button" class="eval-btn" id="eval-btn">
              ★ Evaluate last coaching
            </button>
          </div>
        </div>

      </div>
    </div>
  </div>

  <script>
    let currentPersona = "manager";
    let sessionId = null;

    const personaButtons = document.querySelectorAll(".pill[data-persona]");
    const identifierInput = document.getElementById("identifier-input");
    const messagesEl = document.getElementById("messages");
    const messageInput = document.getElementById("message-input");
    const sendBtn = document.getElementById("send-btn");
    const evalBtn = document.getElementById("eval-btn");
    const statusDot = document.getElementById("status-dot");
    const statusText = document.getElementById("status-text");
    const resetBtn = document.getElementById("reset-btn");
    const errorPanel = document.getElementById("error-panel");
    const toastEl = document.getElementById("toast");
    const toolIndicator = document.getElementById("tool-indicator");
    const toolListEl = document.getElementById("tool-list");
    const thinkingIndicator = document.getElementById("thinking-indicator");



    function showToast(message) {
      toastEl.textContent = message;
      toastEl.classList.add("show");
      setTimeout(() => {
        toastEl.classList.remove("show");
      }, 2600);
    }

    function setStatus(text, online = true) {
      statusText.textContent = text;
      if (text.toLowerCase().includes("thinking")) {
        statusText.classList.add("thinking");
      } else {
        statusText.classList.remove("thinking");
      }

      if (online) {
        statusDot.classList.remove("off");
      } else {
        statusDot.classList.add("off");
      }
    }

    function setError(message) {
      if (message) {
        errorPanel.style.display = "block";
        errorPanel.textContent = message;
      } else {
        errorPanel.style.display = "none";
        errorPanel.textContent = "";
      }
    }

    function setThinking(isThinking) {
      if (isThinking) {
        thinkingIndicator.style.display = "flex";
        thinkingIndicator.textContent = "Thinking…";
      } else {
        thinkingIndicator.style.display = "none";
      }
    }



    personaButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        const newPersona = btn.dataset.persona || "manager";
        if (newPersona === currentPersona) return;

        currentPersona = newPersona;
        personaButtons.forEach(b => b.classList.remove("selected"));
        btn.classList.add("selected");

        // If there is an active session, reset it when persona changes
        if (sessionId) {
          sessionId = null;
          messagesEl.innerHTML = "";
          updateToolIndicator([]);
          setStatus("Session reset – persona changed", true);
          setError("");
          showToast("Session reset because persona changed.");
        }
      });
    });

    function appendMessage(from, text) {
      const row = document.createElement("div");
      row.classList.add("bubble-row", from === "user" ? "user" : "agent");

      const bubble = document.createElement("div");
      bubble.classList.add("bubble", from === "user" ? "user" : "agent");

      const header = document.createElement("div");
      header.classList.add("bubble-header");
      header.textContent = from === "user" ? "You" : "AgentCoach 360";

      const body = document.createElement("div");
      body.textContent = text;

      bubble.appendChild(header);
      bubble.appendChild(body);
      row.appendChild(bubble);
      messagesEl.appendChild(row);
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }

        function updateToolIndicator(toolsArray) {
      if (!toolsArray || toolsArray.length === 0) {
        toolIndicator.style.display = "none";
        toolListEl.innerHTML = "";
        return;
      }

      toolListEl.innerHTML = "";

      const friendlyNames = {
        "get_survey_insights": "Survey insights (CSV)",
        "manager_coach_tool": "Manager coach agent",
        "agent_coach_tool": "Agent coach agent",
        "coach_evaluator_tool": "Coach evaluator",
        "trend_analyst_tool": "Trend analyst",
        "quality_auditor_tool": "Quality auditor",
        "weekly_plan_tool": "Weekly plan (loop)",
        "run_kpi_python": "KPI Python code",
        "kb_google_search": "Knowledge search (demo)",
        "call_openapi_support": "OpenAPI / CRM connector",
      };

      toolsArray.forEach((name) => {
        const pill = document.createElement("span");
        pill.classList.add("tool-pill");
        pill.textContent = friendlyNames[name] || name;
        toolListEl.appendChild(pill);
      });

      toolIndicator.style.display = "flex";
    }

    async function sendMessage(isEval = false) {
      setError("");

      const raw = messageInput.value.trim();
      if (!raw && !isEval) return;

      let messageText = raw;
      if (isEval) {
        if (!sessionId) {
          setError("You need at least one conversation turn before requesting an evaluation.");
          return;
        }
        messageText = "Please evaluate the coaching advice you just gave me. Rate clarity, actionability, empathy, and relevance.";
      }

      // Build a persona-aware prefix for the first message in a session
      let fullMessage = messageText;
      const identifier = (identifierInput.value || "").trim();

      if (!sessionId) {
        if (currentPersona === "manager") {
          if (identifier) {
            fullMessage =
              `I'm a supervisor for the ${identifier} team. ` + messageText;
          } else {
            fullMessage =
              "I am a supervisor in the contact center, but I haven't specified which team I manage yet. If detailed survey insights depend on a team, please first ask me which team I supervise before going deep into the data. " +
              messageText;
          }
        } else {
          if (identifier) {
            fullMessage =
              `I am frontline agent ${identifier}. ` + messageText;
          } else {
            fullMessage =
              "I am a frontline agent, but I haven't specified my agent ID yet. If detailed survey insights depend on a specific agent ID, please first ask me which agent I am before going deep into the data. " +
              messageText;
          }
        }
      }

      appendMessage("user", messageText);
      messageInput.value = "";

      try {
        // Show thinking in the chat area, keep left status more generic
        setThinking(true);
        setStatus(
          sessionId
            ? "Connected – generating answer…"
            : "Connected – preparing session…",
          true
        );

        const resp = await fetch("/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            session_id: sessionId,
            persona: currentPersona,
            identifier: identifier || null,
            message: fullMessage,
            is_eval: isEval,
          }),
        });

        if (!resp.ok) {
          throw new Error("HTTP " + resp.status);
        }

        const data = await resp.json();
        sessionId = data.session_id;
        appendMessage("agent", data.reply);
        updateToolIndicator(data.tools || []);
        setStatus("Connected – session " + sessionId.slice(0, 8) + "…", true);
      } catch (err) {
        console.error(err);
        setStatus("Error – check server logs", false);
        setError("Request failed. Make sure the FastAPI server is running, then try again.");
      } finally {
        setThinking(false);
      }
    }

    sendBtn.addEventListener("click", () => sendMessage(false));
    evalBtn.addEventListener("click", () => sendMessage(true));

    messageInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage(false);
      }
    });

    resetBtn.addEventListener("click", () => {
      sessionId = null;
      messagesEl.innerHTML = "";
      updateToolIndicator([]);
      setStatus("Ready – no session yet", true);
      setError("");
      showToast("Session reset.");
    });

    setStatus("Ready – no session yet", true);
  </script>
</body>
</html>
"""



@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=HTML_PAGE)


# -----------------------------------------------------------------------------
# Main chat endpoint
# -----------------------------------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    """
    POST /chat
    - Manages a session with the ADK Runner.
    - Persona + identifier are used both from the left panel AND inferred
      from the chat text when possible.
    """
    import re  # lightweight, safe to import here

    is_eval = bool(req.is_eval)
    persona = (req.persona or "").lower().strip()
    identifier = (req.identifier or "").strip()

    # --- NEW: infer persona + identifier from the chat text when missing ---
    # This lets memory work even if the user only mentions team/agent in chat.
    text_lower = req.message.lower()

    # If persona not set from UI, try to guess from phrasing
    if not persona:
        if any(kw in text_lower for kw in ["my team", "as a manager", "supervisor"]):
            persona = "manager"
        elif any(kw in text_lower for kw in ["i am agent", "as an agent", "my calls", "my score"]):
            persona = "agent"

    # If identifier is still empty, try to infer from the text
    if not identifier:
        if persona == "manager":
            # Patterns like: "for the Billing team", "the Billing team", "Billing team"
            m = re.search(r"\bfor the ([A-Za-z][A-Za-z0-9_-]{1,}) team\b", req.message, re.IGNORECASE)
            if not m:
                m = re.search(r"\bthe ([A-Za-z][A-Za-z0-9_-]{1,}) team\b", req.message, re.IGNORECASE)
            if not m:
                m = re.search(r"\b([A-Za-z][A-Za-z0-9_-]{1,}) team\b", req.message, re.IGNORECASE)
            if m:
                identifier = m.group(1)
        elif persona == "agent":
            # Patterns like: "I am agent A003", "agent A003"
            m = re.search(r"\bi am agent\s+([A-Za-z0-9_-]{2,15})\b", req.message, re.IGNORECASE)
            if not m:
                m = re.search(r"\bagent\s+([A-Za-z0-9_-]{2,15})\b", req.message, re.IGNORECASE)
            if m:
                identifier = m.group(1)

    # ------------------------------------------------------------------
    # Create or reuse session
    # ------------------------------------------------------------------
    if req.session_id:
        session = await session_service.get_session(
            app_name="agentcoach360_app",
            user_id="web_user",
            session_id=req.session_id,
        )
    else:
        session = await session_service.create_session(
            app_name="agentcoach360_app",
            user_id="web_user",
        )

    # ------------------------------------------------------------------
    # Apply persistent memory (READ) into the prompt if persona+identifier known
    # ------------------------------------------------------------------
    base_text = req.message
    final_text = base_text

    if persona in ("manager", "agent") and identifier:
        try:
            mem_row = memory_store.get(persona, identifier)
        except Exception as e:
            # Never break chat because of memory issues
            print(f"[memory_store] get failed: {e}")
            mem_row = None

        if mem_row:
            snippet = memory_store.to_prompt_snippet(mem_row)
            final_text = (
                "You are continuing an ongoing coaching relationship.\n"
                "Use the long-term memory below to maintain continuity and avoid "
                "repeating the same advice verbatim.\n\n"
                f"{snippet}\n\n"
                "Now respond to the user's latest message:\n"
                f"{base_text}"
            )

    # Build the user message as Content (uses final_text now)
    content = types.Content(
        role="user",
        parts=[types.Part(text=final_text)],
    )

    # ------------------------------------------------------------------
    # Run the agent through Runner; this returns an event stream.
    # ------------------------------------------------------------------
    try:
        events = runner.run(
            user_id="web_user",
            session_id=session.id,
            new_message=content,
        )
    except Exception as e:
        reply_text = f"AgentCoach 360 backend error: {e}"
        # Log even error cases
        append_log_entry(
            session_id=session.id,
            persona=persona or "unknown",
            identifier=identifier or "",
            is_eval=is_eval,
            user_message=req.message,
            agent_reply=reply_text,
        )
        return ChatResponse(
            session_id=session.id,
            reply=reply_text,
            tools=None,
        )

    # ------------------------------------------------------------------
    # Extract the last text response from events
    # ------------------------------------------------------------------
    reply_text = "No response from agent."
    for event in events:
        if getattr(event, "content", None) and event.content.parts:
            part = event.content.parts[0]
            if getattr(part, "text", None):
                reply_text = part.text

    # Keep a copy of the raw text (with the TOOLS_USED footer)
    raw_reply_text = reply_text

    # Try to parse a trailing TOOLS_USED: line for the UI
    tools_used: list[str] | None = None
    lines = reply_text.splitlines()
    if lines and lines[-1].strip().startswith("TOOLS_USED:"):
        footer = lines.pop().strip()
        raw = footer[len("TOOLS_USED:"):].strip()
        if raw and raw.lower() != "none":
            tools_used = [t.strip() for t in raw.split(",") if t.strip()]
        reply_text = "\n".join(lines).strip()

    # ------------------------------------------------------------------
    # NEW: Persist long-term memory (WRITE) if persona+identifier known
    # ------------------------------------------------------------------
    try:
        if persona in ("manager", "agent") and identifier:
            last_focus = extract_focus_area(req.message)
            last_summary = reply_text  # cleaned answer (without TOOLS_USED)

            memory_store.upsert(
                persona=persona,
                identifier=identifier,
                last_focus=last_focus,
                last_summary=last_summary,
            )
    except Exception as e:
        # Never break the chat because of memory write issues
        print(f"[memory_store] upsert failed: {e}")

    # 🔹 Log this interaction for observability / evaluation
    append_log_entry(
        session_id=session.id,
        persona=persona or "unknown",
        identifier=identifier or "",
        is_eval=is_eval,
        user_message=req.message,
        agent_reply=raw_reply_text,  # log the full text, including footer
    )

    return ChatResponse(
        session_id=session.id,
        reply=reply_text,
        tools=tools_used,
    )
