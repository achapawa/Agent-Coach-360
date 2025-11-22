from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

import os

import pandas as pd


# ---------------------------------------------------------------------------
# Local data loading for KPI tool (no external APIs needed)
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "survey_responses.csv"

_df_cache: pd.DataFrame | None = None


def _load_survey_df_for_kpi() -> pd.DataFrame:
    """Local helper just for the KPI code tool (avoids circular imports)."""
    global _df_cache
    if _df_cache is None:
        df = pd.read_csv(DATA_PATH)
        df["date"] = pd.to_datetime(df["date"])
        _df_cache = df
    return _df_cache


# ---------------------------------------------------------------------------
# 1) Built-in style tool: Python KPI execution on the survey data
# ---------------------------------------------------------------------------

def run_kpi_python(code: str) -> Dict[str, Any]:
    """
    Execute a small Python snippet against the survey DataFrame `df`.

    - No external API keys required.
    - Exposes:
        * df: pandas DataFrame with survey_responses.csv
        * pd: pandas module
    - The LLM is instructed by the root agent to keep code short & safe
      (groupby, mean, counts, etc.) and put the output in a variable
      named `result`.

    The return is always JSON-like and safe for the LLM to consume.
    """
    try:
        df = _load_survey_df_for_kpi()
    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"survey CSV not found at {str(DATA_PATH)}",
        }

    # Very restricted exec environment: only df/pd and no builtins.
    local_ns: Dict[str, Any] = {"df": df, "pd": pd}
    safe_globals: Dict[str, Any] = {"__builtins__": {}}

    try:
        exec(code, safe_globals, local_ns)
    except Exception as e:
        return {
            "status": "error",
            "message": f"code_execution_failed: {e}",
        }

    result = local_ns.get("result")

    # If the model created a DataFrame, we send a compact preview.
    if isinstance(result, pd.DataFrame):
        preview = result.head(10).to_dict(orient="records")
        return {
            "status": "ok",
            "type": "dataframe",
            "preview_rows": preview,
        }

    # Anything else → just repr as a string.
    return {
        "status": "ok",
        "type": "raw",
        "result": repr(result),
    }


# ---------------------------------------------------------------------------
# 2) MCP / Google-style KB search tool
# ---------------------------------------------------------------------------

def kb_google_search(query: str) -> Dict[str, Any]:
    """
    Knowledge-base / Google-search style tool.

    Modes:
    - DEMO MODE (default, no config needed):
        * If neither GOOGLE_SEARCH_API_KEY/CX nor KB_SEARCH_BASE_URL is set,
          returns a 'demo' response that explains it's a stub.
    - REAL MODE (optional):
        * If KB_SEARCH_BASE_URL is set -> POSTs to that backend (e.g. MCP server).
        * Else if GOOGLE_SEARCH_API_KEY & GOOGLE_SEARCH_CX are set -> uses
          Google Custom Search JSON API.

    This means: in your current setup, with no search keys configured, it will
    NOT break. The root agent just treats it as “search not configured, answer
    from model knowledge”.
    """
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    cx = os.getenv("GOOGLE_SEARCH_CX")
    base_url = os.getenv("KB_SEARCH_BASE_URL")

    # --- DEMO / STUB MODE: no external config provided ----------------------
    if not (api_key and cx) and not base_url:
        return {
            "status": "demo",
            "message": (
                "Search backend is not configured. In a real enterprise setup, "
                "this tool would call Google Search, an MCP server, or an "
                "internal KB. For now, treat this as a stub and answer from "
                "your own knowledge plus the survey data."
            ),
            "query": query,
        }

    # Only import requests if we actually need it
    try:
        import requests  # type: ignore
    except Exception:
        return {
            "status": "error",
            "message": "requests library not available in this environment.",
        }

    # --- CUSTOM BACKEND / MCP STYLE ----------------------------------------
    if base_url:
        url = base_url.rstrip("/") + "/search"
        try:
            resp = requests.post(
                url,
                json={"query": query},
                timeout=10,
            )
            return {
                "status": "ok",
                "backend": "custom",
                "http_status": resp.status_code,
                "body": resp.text[:4000],
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"custom_search_failed: {e}",
            }

    # --- GOOGLE CUSTOM SEARCH JSON API -------------------------------------
    params = {"q": query, "key": api_key, "cx": cx, "num": 3}
    try:
        resp = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params=params,
            timeout=10,
        )
        data = resp.json()
        items = data.get("items", [])
        snippets = [
            {
                "title": it.get("title"),
                "snippet": it.get("snippet"),
                "link": it.get("link"),
            }
            for it in items[:3]
        ]
        return {
            "status": "ok",
            "backend": "google_cse",
            "results": snippets,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"google_search_failed: {e}",
        }


# ---------------------------------------------------------------------------
# 3) OpenAPI-style support / CRM connector
# ---------------------------------------------------------------------------

def call_openapi_support(endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generic OpenAPI-style connector.

    DEMO MODE (your current setup):
    - If SUPPORT_API_BASE_URL is not set, this returns a 'demo' response
      that just echoes the endpoint + payload preview.
    - The orchestrator agent treats this as “this is where a real support /
      CRM / reporting backend would be wired in”.

    REAL MODE (optional later):
    - Set SUPPORT_API_BASE_URL (and optionally SUPPORT_API_KEY).
    - Tool will POST JSON to: {SUPPORT_API_BASE_URL}/{endpoint}
    """
    base_url = os.getenv("SUPPORT_API_BASE_URL")
    api_key = os.getenv("SUPPORT_API_KEY")

    # --- DEMO / STUB MODE --------------------------------------------------
    if not base_url:
        return {
            "status": "demo",
            "message": (
                "Support OpenAPI backend is not configured. In production, this "
                "would POST to your support/CRM/reporting API. For now, use this "
                "payload as context and answer from your own reasoning."
            ),
            "endpoint": endpoint,
            "payload_preview": str(payload)[:1000],
        }

    # Only import requests if we actually need it
    try:
        import requests  # type: ignore
    except Exception:
        return {
            "status": "error",
            "message": "requests library not available in this environment.",
        }

    url = base_url.rstrip("/") + "/" + endpoint.lstrip("/")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        resp = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=15,
        )
        return {
            "status": "ok",
            "http_status": resp.status_code,
            "body": resp.text[:4000],
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"openapi_call_failed: {e}",
        }
