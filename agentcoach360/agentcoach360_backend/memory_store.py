from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Optional

import sqlite3

# Base path: project root (same pattern as your other modules)
BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "memory.sqlite"


@dataclass
class MemoryRow:
    """Single long-term memory record for a persona + identifier."""
    persona: str
    identifier: str
    last_focus: str
    last_summary: str
    last_seen_utc: str
    total_interactions: int


class SQLiteMemoryStore:
    """
    Simple, file-based long-term memory store.
    Keyed by (persona, identifier) – e.g., ("manager", "Billing") or ("agent", "A003").
    """

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self._db_path = str(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _init_db(self) -> None:
        with self._connect() as conn, conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    persona TEXT NOT NULL,
                    identifier TEXT NOT NULL,
                    last_focus TEXT,
                    last_summary TEXT,
                    last_seen_utc TEXT,
                    total_interactions INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (persona, identifier)
                )
                """
            )

    def get(self, persona: str, identifier: str) -> Optional[MemoryRow]:
        persona = (persona or "").lower().strip()
        identifier = (identifier or "").strip()
        if not persona or not identifier:
            return None

        with self._lock, self._connect() as conn:
            cur = conn.execute(
                """
                SELECT persona, identifier, last_focus, last_summary,
                       last_seen_utc, total_interactions
                FROM memories
                WHERE persona = ? AND identifier = ?
                """,
                (persona, identifier),
            )
            row = cur.fetchone()

        if not row:
            return None

        return MemoryRow(
            persona=row[0],
            identifier=row[1],
            last_focus=row[2] or "",
            last_summary=row[3] or "",
            last_seen_utc=row[4] or "",
            total_interactions=row[5] or 0,
        )

    def upsert(
        self,
        *,
        persona: str,
        identifier: str,
        last_focus: str | None,
        last_summary: str | None,
    ) -> MemoryRow:
        """
        Insert or update the memory row for (persona, identifier),
        incrementing total_interactions.
        """
        persona = (persona or "").lower().strip()
        identifier = (identifier or "").strip()
        if not persona or not identifier:
            raise ValueError("persona and identifier are required for memory upsert")

        now = datetime.utcnow().isoformat()
        focus = (last_focus or "").strip()
        summary = (last_summary or "").strip()

        with self._lock, self._connect() as conn:
            cur = conn.execute(
                "SELECT total_interactions FROM memories WHERE persona = ? AND identifier = ?",
                (persona, identifier),
            )
            row = cur.fetchone()

            if row:
                total = (row[0] or 0) + 1
                conn.execute(
                    """
                    UPDATE memories
                    SET last_focus = ?, last_summary = ?, last_seen_utc = ?, total_interactions = ?
                    WHERE persona = ? AND identifier = ?
                    """,
                    (focus, summary, now, total, persona, identifier),
                )
            else:
                total = 1
                conn.execute(
                    """
                    INSERT INTO memories (
                        persona, identifier, last_focus, last_summary,
                        last_seen_utc, total_interactions
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (persona, identifier, focus, summary, now, total),
                )

        return MemoryRow(
            persona=persona,
            identifier=identifier,
            last_focus=focus,
            last_summary=summary,
            last_seen_utc=now,
            total_interactions=total,
        )

    @staticmethod
    def to_prompt_snippet(row: MemoryRow) -> str:
        """
        Turn a MemoryRow into a compact string we can prepend
        to the model input (context engineering).
        """
        parts: list[str] = []

        if row.last_focus:
            parts.append(f"Last coaching focus area: {row.last_focus}")

        if row.last_summary:
            truncated = row.last_summary
            if len(truncated) > 600:
                truncated = truncated[:600].rstrip() + "…"
            parts.append(f"Last coaching summary: {truncated}")

        parts.append(f"Total recorded interactions: {row.total_interactions}")
        if row.last_seen_utc:
            parts.append(f"Last updated (UTC): {row.last_seen_utc}")

        return "\n".join(parts)


# Shared instance used by the web app
memory_store = SQLiteMemoryStore()
