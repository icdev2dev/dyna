import lancedb
import json
import pandas as pd
from datetime import datetime

from .schemas import AGENTS_URI, AGENT_STATE_NAME
from .schemas import AGENT_STEPS_NAME  # fallback if agent_state lacks session_id

AGENTS_DB = lancedb.connect(AGENTS_URI)

ACTIVE_STATUSES = {"starting", "running", "paused", "stopping"}

def _safe_json_loads(s, default=None):
    if s is None:
        return default
    if isinstance(s, (dict, list)):
        return s
    try:
        return json.loads(s)
    except Exception:
        return default if default is not None else s

def _has_column(df: pd.DataFrame, col: str) -> bool:
    return df is not None and not df.empty and (col in df.columns)

def list_sessions_for_agent(
    agent_id: str,
    *,
    active_only: bool = False,
    limit: int = 100,
    offset: int = 0,
    order: str = "desc",  # by last_updated
):
    """
    Return distinct sessions for an agent with a latest snapshot.
    Prefers agent_state (one row per session); falls back to agent_steps if needed.
    """
    # Try from agent_state (preferred)
    try:
        #print(agent_id)
        state_tbl = AGENTS_DB.open_table(AGENT_STATE_NAME)
        df = state_tbl.search().where(f"agent_id == '{agent_id}'").to_pandas()
        #print(df)
    except Exception as e:
        print(e)
        df = pd.DataFrame()

    if not df.empty and _has_column(df, "session_id"):
        # Keep latest row per session_id by last_updated (string ISO)
        df["last_updated"] = pd.to_datetime(df["last_updated"], errors="coerce")
        df = df.sort_values(by=["last_updated"], ascending=True)
        latest = df.drop_duplicates(subset=["session_id"], keep="last")
        if active_only and "status" in latest.columns:
            latest = latest[latest["status"].isin(ACTIVE_STATUSES)]

        # Order and paginate
        ascending = (order.lower() != "desc")
        latest = latest.sort_values(by=["last_updated"], ascending=ascending)

        if offset:
            latest = latest.iloc[offset:]
        if limit:
            latest = latest.iloc[:limit]

        rows = []
        for _, r in latest.iterrows():
            rows.append({
                "agent_id": r.get("agent_id"),
                "session_id": r.get("session_id"),
                "status": r.get("status"),
                "iteration": int(r.get("iteration")) if pd.notna(r.get("iteration")) else None,
                "last_updated": r.get("last_updated").isoformat() if pd.notna(r.get("last_updated")) else None,
                "result": _safe_json_loads(r.get("result")),
                "context": _safe_json_loads(r.get("context"), default={}),
            })
        return rows

    # Fallback: derive sessions from agent_steps (distinct session_id)
    try:
        steps_tbl = AGENTS_DB.open_table(AGENT_STEPS_NAME)
        sdf = steps_tbl.query().where(f"agent_id == '{agent_id}'").to_pandas()
    except Exception:
        sdf = pd.DataFrame()

    if sdf.empty or "session_id" not in sdf.columns:
        # No data to infer sessions
        return []

    # Group by session and compute aggregates for a summary row
    sdf["created_at"] = pd.to_datetime(sdf["created_at"], errors="coerce")
    agg = sdf.groupby("session_id").agg(
        last_updated=("created_at", "max"),
        max_iteration=("iteration", "max"),
    ).reset_index()

    # We don’t have status in steps; mark unknown unless you also write status events into steps
    agg["status"] = "unknown"

    ascending = (order.lower() != "desc")
    agg = agg.sort_values(by=["last_updated"], ascending=ascending)

    if offset:
        agg = agg.iloc[offset:]
    if limit:
        agg = agg.iloc[:limit]

    rows = []
    for _, r in agg.iterrows():
        rows.append({
            "agent_id": agent_id,
            "session_id": r.get("session_id"),
            "status": r.get("status"),
            "iteration": int(r.get("max_iteration")) if pd.notna(r.get("max_iteration")) else None,
            "last_updated": r.get("last_updated").isoformat() if pd.notna(r.get("last_updated")) else None,
        })
    return rows
