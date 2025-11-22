import csv
import os
import random
from datetime import datetime, timedelta

OUTPUT_DIR = "data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "survey_responses.csv")
NUM_ROWS = 100  # change to 50 if you want fewer rows

# Define some sample agents and teams
AGENTS = [
    {"agent_id": "A001", "agent_name": "Alice Johnson", "team": "Billing"},
    {"agent_id": "A002", "agent_name": "Brian Lee", "team": "Billing"},
    {"agent_id": "A003", "agent_name": "Carla Gomez", "team": "Tech Support"},
    {"agent_id": "A004", "agent_name": "David Patel", "team": "Tech Support"},
    {"agent_id": "A005", "agent_name": "Emma Williams", "team": "Retention"},
    {"agent_id": "A006", "agent_name": "Farhan Khan", "team": "Retention"},
]

CHANNELS = ["phone", "chat", "email"]

RESOLUTION_STATUSES = ["resolved", "unresolved", "escalated"]

# Template feedback snippets
NEGATIVE_ISSUES = [
    ("long_hold_time", "I had to wait on hold for a very long time before speaking to someone."),
    ("rude_tone", "The agent sounded impatient and a bit rude."),
    ("did_not_listen", "I felt like the agent wasn’t really listening to my problem."),
    ("no_resolution", "My issue is still not resolved after this call."),
    ("complex_process", "The process was confusing and I had to repeat my information multiple times."),
]

NEUTRAL_FEEDBACK = [
    ("neutral_experience", "The experience was okay, nothing special."),
    ("slow_but_resolved", "It took a while, but my issue was eventually resolved."),
    ("average_service", "Service was average, not terrible but not great either."),
]

POSITIVE_FEEDBACK = [
    ("friendly_agent", "The agent was very friendly and professional."),
    ("quick_resolution", "My issue was resolved quickly and efficiently."),
    ("clear_explanations", "The agent explained everything very clearly."),
    ("above_and_beyond", "The agent went above and beyond to help me."),
    ("empathy", "I really appreciated how empathetic the agent was."),
]

AGENT_NOTES_TEMPLATES = [
    "Customer had a billing discrepancy, provided breakdown and adjusted invoice.",
    "Escalated to tier 2 due to system limitation.",
    "Offered one-time credit as goodwill gesture.",
    "Customer was frustrated at first, calmed down after clarification.",
    "Follow-up email sent with detailed steps.",
    "Customer requested supervisor call back within 24 hours.",
]


def random_date_within_last_n_days(n_days: int) -> str:
    """Return a random date within the last n_days as YYYY-MM-DD."""
    today = datetime.today().date()
    delta_days = random.randint(0, n_days)
    date = today - timedelta(days=delta_days)
    return date.isoformat()


def generate_row(row_index: int) -> dict:
    interaction_id = f"INT-{row_index:04d}"
    date = random_date_within_last_n_days(60)
    channel = random.choice(CHANNELS)
    agent = random.choice(AGENTS)

    # Skew the scores to be mostly positive with some realistic negatives
    csat_score = random.choices(
        population=[1, 2, 3, 4, 5],
        weights=[5, 10, 25, 35, 25],  # more 3–4–5, fewer 1–2
        k=1,
    )[0]

    # NPS buckets corresponding loosely to CSAT
    if csat_score <= 2:
        nps_score = random.choice([-100, -50])
    elif csat_score == 3:
        nps_score = random.choice([-50, 0, 50])
    else:
        nps_score = random.choice([0, 50, 100])

    # Professionalism & empathy ratings (close to CSAT but with some noise)
    agent_professionalism_rating = min(
        5, max(1, csat_score + random.choice([-1, 0, 0, 1]))
    )
    agent_empathy_rating = min(
        5, max(1, csat_score + random.choice([-1, 0, 0, 1]))
    )

    # Resolution status skewed towards resolved
    resolution_status = random.choices(
        population=RESOLUTION_STATUSES,
        weights=[70, 15, 15],
        k=1,
    )[0]

    # Choose feedback & sentiment based on CSAT
    topic_tags_list = []
    if csat_score <= 2:
        topic, text = random.choice(NEGATIVE_ISSUES)
        sentiment = "negative"
        topic_tags_list.append(topic)
    elif csat_score == 3:
        topic, text = random.choice(NEUTRAL_FEEDBACK)
        sentiment = "neutral"
        topic_tags_list.append(topic)
    else:
        topic, text = random.choice(POSITIVE_FEEDBACK)
        sentiment = "positive"
        topic_tags_list.append(topic)

    # Add some extra topic tags sometimes
    if random.random() < 0.3:
        extra_topic = random.choice(
            ["billing_issue", "technical_issue", "account_cancellation", "password_reset"]
        )
        if extra_topic not in topic_tags_list:
            topic_tags_list.append(extra_topic)

    topic_tags = ",".join(topic_tags_list)

    free_text_feedback = text
    agent_notes = random.choice(AGENT_NOTES_TEMPLATES)

    return {
        "interaction_id": interaction_id,
        "date": date,
        "channel": channel,
        "agent_id": agent["agent_id"],
        "agent_name": agent["agent_name"],
        "team": agent["team"],
        "csat_score": csat_score,
        "nps_score": nps_score,
        "agent_professionalism_rating": agent_professionalism_rating,
        "agent_empathy_rating": agent_empathy_rating,
        "resolution_status": resolution_status,
        "sentiment": sentiment,
        "topic_tags": topic_tags,
        "free_text_feedback": free_text_feedback,
        "agent_notes": agent_notes,
    }


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    fieldnames = [
        "interaction_id",
        "date",
        "channel",
        "agent_id",
        "agent_name",
        "team",
        "csat_score",
        "nps_score",
        "agent_professionalism_rating",
        "agent_empathy_rating",
        "resolution_status",
        "sentiment",
        "topic_tags",
        "free_text_feedback",
        "agent_notes",
    ]

    with open(OUTPUT_FILE, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(1, NUM_ROWS + 1):
            row = generate_row(i)
            writer.writerow(row)

    print(f"Generated {NUM_ROWS} rows in: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
