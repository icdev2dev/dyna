import lancedb
import pyarrow as pa
from datetime import datetime, timezone
import json
import pandas as pd

from .schemas import AGENT_STATE_NAME, AGENTS_URI
AGENTS_DB = lancedb.connect(AGENTS_URI)


def _safe_json_loads(s, *, default_if_fail=None):
    if s is None:
        return default_if_fail
    if isinstance(s, (dict, list)):
        return s
    try:
        return json.loads(s)
    except Exception:
        return default_if_fail if default_if_fail is not None else s

def upsert_agent_state(agent_id, status,*, iteration=None, result=None, context=None, history=None,session_id: str | None = None,):
    tbl = AGENTS_DB.open_table(AGENT_STATE_NAME)
    now = datetime.now(timezone.utc).isoformat()

    updates = {
        "agent_id": agent_id,
        "status": status,
        "iteration": iteration,
        "result": json.dumps(result) if isinstance(result, (dict, list)) else result,
        "last_updated": now,
        "history": json.dumps(history) if history else None,
        "context": json.dumps(context) if context else None,
    }
    
    where = f"agent_id == '{agent_id}'"
    if session_id is not None:
        where += f" and session_id == '{session_id}'"
    else:
        where += " and session_id IS NULL"

    try:
        count = tbl.update(where=where, updates=updates)
    except Exception:
        count = 0

    if not count:
        rec = {
            "agent_id": agent_id,
            "session_id": session_id,
            "status": status,
            "iteration": int(iteration) if iteration is not None else None,
            "result": json.dumps(result) if isinstance(result, (dict, list)) else result,
            "last_updated": now,
            "history": json.dumps(history) if history is not None else None,
            "context": json.dumps(context) if context is not None else None,
        }
        tbl.add(data=[rec], mode="append")
    print(f"Agent {agent_id} session={session_id} state={status} iter={iteration} @ {now}")

def get_agent_state(agent_id, session_id: str | None = None):
    tbl = AGENTS_DB.open_table(AGENT_STATE_NAME)
    df = tbl.to_pandas().query(f"agent_id == '{agent_id}'")
    if df.empty:
        return None
    if session_id is not None and "session_id" in df.columns:
        sdf = df.query(f"agent_id == '{agent_id}' and session_id == '{session_id}'")
        if sdf.empty:
            return None
        row = sdf.sort_values("last_updated").iloc[-1]
    else:
        # legacy fallback: most recent row by agent_id (session_id may be null or absent)
        sdf = df.query(f"agent_id == '{agent_id}'")
        if sdf.empty:
            return None
        # sort by last_updated if present
        if "last_updated" in sdf.columns:
            try:
                sdf["last_updated_dt"] = pd.to_datetime(sdf["last_updated"], errors="coerce")
                sdf = sdf.sort_values("last_updated_dt")
            except Exception:
                pass
        row = sdf.iloc[-1]

    return {
        "agent_id": row.agent_id,
        "session_id": getattr(row, "session_id", None) if hasattr(row, "session_id") else None,
        "status": row.status,
        "iteration": row.iteration,
        "result": _safe_json_loads(getattr(row, "result", None), default_if_fail=getattr(row, "result", None)),
        "last_updated": row.last_updated,
        "history": _safe_json_loads(getattr(row, "history", None), default_if_fail=[]),
        "context": _safe_json_loads(getattr(row, "context", None), default_if_fail={}),
    }


def list_agent_states():
    tbl = AGENTS_DB.open_table(AGENT_STATE_NAME)
    df = tbl.to_pandas()
    if df.empty:
        return []
    return df

