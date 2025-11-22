from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "logs" / "interactions.csv"
SUMMARY_JSON = BASE_DIR / "logs" / "summary_stats.json"


def load_logs() -> pd.DataFrame:
    if not LOG_FILE.exists():
        raise FileNotFoundError(f"Log file not found at {LOG_FILE}")
    df = pd.read_csv(LOG_FILE)
    if "timestamp_utc" in df.columns:
        df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], errors="coerce")
    return df


def compute_stats(df: pd.DataFrame) -> Dict[str, Any]:
    stats: Dict[str, Any] = {}

    # Basic sizes
    stats["total_interactions"] = int(len(df))
    stats["total_sessions"] = int(df["session_id"].nunique())

    # Persona breakdown
    persona_counts = df["persona"].fillna("unknown").value_counts()
    stats["persona_counts"] = persona_counts.to_dict()

    # Eval vs normal
    if "is_eval" in df.columns:
        eval_counts = df["is_eval"].astype(str).value_counts()
        eval_true = int(eval_counts.get("1", 0))
        eval_false = int(eval_counts.get("0", 0))
        stats["eval_interactions"] = eval_true
        stats["non_eval_interactions"] = eval_false
        stats["eval_rate_pct"] = round(
            100.0 * eval_true / max(stats["total_interactions"], 1), 1
        )
    else:
        stats["eval_interactions"] = None
        stats["non_eval_interactions"] = None
        stats["eval_rate_pct"] = None

    # Messages per session
    per_session = df.groupby("session_id")["user_message"].count()
    stats["avg_messages_per_session"] = round(float(per_session.mean()), 2)
    stats["min_messages_per_session"] = int(per_session.min())
    stats["max_messages_per_session"] = int(per_session.max())

    # Sessions per persona
    sessions_per_persona = (
        df.groupby("persona")["session_id"].nunique().sort_values(ascending=False)
    )
    stats["sessions_per_persona"] = sessions_per_persona.to_dict()

    # Top identifiers (teams / agent IDs)
    if "identifier" in df.columns:
        id_counts = (
            df["identifier"]
            .fillna("")
            .replace("", "unspecified")
            .value_counts()
            .head(10)
        )
        stats["top_identifiers"] = id_counts.to_dict()
    else:
        stats["top_identifiers"] = {}

    # Activity over days
    if "timestamp_utc" in df.columns:
        df_valid = df.dropna(subset=["timestamp_utc"])
        per_day = (
            df_valid.groupby(df_valid["timestamp_utc"].dt.date)["session_id"]
            .count()
            .sort_index()
        )
        stats["interactions_per_day"] = {
            str(d): int(c) for d, c in per_day.items()
        }

    return stats


def print_stats(stats: Dict[str, Any]) -> None:
    line = "-" * 72
    print(line)
    print("AgentCoach 360 – Interaction Analytics")
    print(line)

    print(f"Total interactions: {stats['total_interactions']}")
    print(f"Total sessions    : {stats['total_sessions']}")
    print(
        f"Avg messages/session: {stats['avg_messages_per_session']} "
        f"(min={stats['min_messages_per_session']}, "
        f"max={stats['max_messages_per_session']})"
    )

    print("\nBy persona (interactions):")
    for persona, count in stats["persona_counts"].items():
        print(f"  - {persona}: {count}")

    print("\nSessions per persona:")
    for persona, count in stats["sessions_per_persona"].items():
        print(f"  - {persona}: {count}")

    print("\nTop identifiers (teams / agents):")
    for ident, count in stats["top_identifiers"].items():
        print(f"  - {ident}: {count}")

    if stats["eval_interactions"] is not None:
        print("\nEvaluation turns:")
        print(f"  - eval interactions    : {stats['eval_interactions']}")
        print(f"  - non-eval interactions: {stats['non_eval_interactions']}")
        print(f"  - eval rate            : {stats['eval_rate_pct']}%")

    if stats.get("interactions_per_day"):
        print("\nInteractions per day:")
        for day, count in stats["interactions_per_day"].items():
            print(f"  - {day}: {count}")

    print("\nSummary JSON written to:", SUMMARY_JSON)
    print(line)


def main() -> None:
    df = load_logs()
    stats = compute_stats(df)
    SUMMARY_JSON.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    print_stats(stats)


if __name__ == "__main__":
    main()
