def get_session_memory(session):
    """
    Returns the memory dict stored in session.state.
    Creates it if it doesn't exist.
    """
    if "memory" not in session.state:
        session.state["memory"] = {
            "persona": None,
            "identifier": None,
            "last_focus": None,
            "last_summary": None,
            "history": []
        }
    return session.state["memory"]


def update_memory_after_insights(session, persona, identifier, focus_area, summary):
    """
    Stores the last coaching result in session.memory.
    """
    memory = get_session_memory(session)

    memory["persona"] = persona
    memory["identifier"] = identifier
    memory["last_focus"] = focus_area
    memory["last_summary"] = summary

    memory["history"].append({
        "persona": persona,
        "identifier": identifier,
        "focus_area": focus_area,
        "summary": summary
    })

    session.state["memory"] = memory
