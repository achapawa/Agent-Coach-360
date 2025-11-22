from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import json

BASE_DIR = Path(__file__).resolve().parents[1]
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
A2A_LOG = LOG_DIR / "a2a_traces.jsonl"


@dataclass
class AgentIdentity:
    """Minimal identity for an agent in the A2A protocol."""
    name: str
    role: str  # e.g. "orchestrator", "coach", "evaluator"


@dataclass
class AgentMessage:
    """
    One A2A message between agents.
    We use this for tracing when the orchestrator routes to specialist agents.
    """
    ts_utc: str
    conversation_id: str
    from_agent: AgentIdentity
    to_agent: AgentIdentity
    message_type: str  # e.g. "evaluation_request"
    payload: Dict[str, Any]


def record_a2a_exchange(
    *,
    conversation_id: str,
    from_name: str,
    from_role: str,
    to_name: str,
    to_role: str,
    message_type: str,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Append a single A2A message to logs/a2a_traces.jsonl.

    We use this in the web layer when we know the root agent is
    delegating to the coach_evaluator_agent (evaluation flow).
    """
    msg = AgentMessage(
        ts_utc=datetime.utcnow().isoformat(),
        conversation_id=conversation_id,
        from_agent=AgentIdentity(from_name, from_role),
        to_agent=AgentIdentity(to_name, to_role),
        message_type=message_type,
        payload=payload or {},
    )

    record = {
        "ts_utc": msg.ts_utc,
        "conversation_id": msg.conversation_id,
        "from_agent": asdict(msg.from_agent),
        "to_agent": asdict(msg.to_agent),
        "message_type": msg.message_type,
        "payload": msg.payload,
    }

    with A2A_LOG.open("a", encoding="utf-8") as f:
        json.dump(record, f)
        f.write("\n")
