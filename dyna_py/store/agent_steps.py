import lancedb, uuid, json
from datetime import datetime
from .schemas import AGENTS_URI, AGENT_STEPS_NAME
import json as _json


AGENTS_DB = lancedb.connect(AGENTS_URI)
JSON_FIELDS = ("data", "state", "guidance")


def _safe_json_loads(s, default=None):
    if s is None:
        return default
    if isinstance(s, (dict, list)):
        return s
    try:
        return json.loads(s)
    except Exception:
        return default if default is not None else s





def _to_json_str(obj):
    if obj is None:
        return None
    if isinstance(obj, (dict, list)):
        return _json.dumps(obj)
    return str(obj)

def append_agent_step(
    agent_id: str,
    iteration: int,
    *,
    session_id: str | None = None,
    step_token: str | None = None,
    next_step_token: str | None = None,
    status: str = "ok",
    text: str | None = None,
    data: dict | list | None = None,
    state: dict | list | None = None,
    guidance: dict | list | None = None,
    notes: str | None = None,
    latency_ms: int | None = None,
    error: str | None = None,
    ):
        
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print(AGENTS_DB.table_names())
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        
        tbl = AGENTS_DB.open_table(AGENT_STEPS_NAME)
        rec = {
            "id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "agent_id": agent_id,
            "session_id": session_id,
            "iteration": iteration,
            "step_token": step_token,
            "next_step_token": next_step_token,
            "status": status,
            "text": text,
            "data": _to_json_str(data),
            "state": _to_json_str(state),
            "guidance": _to_json_str(guidance),
            "notes": notes,
            "latency_ms": latency_ms,
            "error": error,
        }
        tbl.add([rec], mode="append")





def _build_where(
*,
    session_id: str | None,
    agent_id: str | None,
    min_iteration: int | None,
    max_iteration: int | None,
    since_created_at: str | None,
    status: str | None,
    ):
        parts = []
        if session_id:
            parts.append(f"session_id == '{session_id}'")
        if agent_id:
            parts.append(f"agent_id == '{agent_id}'")
        if min_iteration is not None:
            parts.append(f"iteration >= {int(min_iteration)}")
        if max_iteration is not None:
            parts.append(f"iteration <= {int(max_iteration)}")
        if since_created_at:
            parts.append(f"created_at > '{since_created_at}'")
        if status:
            parts.append(f"status == '{status}'")
        return " and ".join(parts) if parts else None

def _normalize_rows(df):
    if df is None or df.empty:
        return []
    df = df.copy()
    # Ensure integer types where expected
    if "iteration" in df.columns:
        df["iteration"] = df["iteration"].astype("Int64")
    if "latency_ms" in df.columns:
        df["latency_ms"] = df["latency_ms"].astype("Int64")
    rows = df.to_dict(orient="records")
    # JSON-decode selected fields
    out = []
    for r in rows:
        for f in JSON_FIELDS:
            if f in r:
                r[f] = _safe_json_loads(r.get(f))
        out.append(r)
    return out

def list_agent_steps(
*,
session_id: str | None = None,
agent_id: str | None = None,
min_iteration: int | None = None,
max_iteration: int | None = None,
since_created_at: str | None = None,
status: str | None = None,
limit: int = 100,
offset: int = 0,
order: str = "asc",  # "asc" or "desc" by iteration
):
    """
    Returns a list of agent step rows filtered by the provided criteria.
    Ordering is by iteration, ascending by default.
    """
    tbl = AGENTS_DB.open_table(AGENT_STEPS_NAME)
    where = _build_where(
    session_id=session_id,
    agent_id=agent_id,
    min_iteration=min_iteration,
    max_iteration=max_iteration,
    since_created_at=since_created_at,
    status=status,
    )
    # LanceDB doesn't support offset directly; fetch a window and slice in pandas.
    fetch_n = max(limit + offset, limit)
    q = tbl.search()
    if where:
        q = q.where(where)
        # Fetch to pandas then sort and slice
        df = q.limit(fetch_n).to_pandas()
        if df is None or df.empty:
            return []
    # Order by iteration; created_at is a tiebreaker
        ascending = (order.lower() != "desc")
        df = df.sort_values(by=["iteration", "created_at"], ascending=[ascending, ascending])
        if offset:
            df = df.iloc[offset:]
        if limit:
            df = df.iloc[:limit]
        return _normalize_rows(df)

def list_agent_steps_since_iteration(
    *,
    session_id: str,
    after_iteration: int,
    limit: int = 500,
    order: str = "asc",
    ):
    """
    Convenience: get steps strictly after the given iteration for a session.
    """
    return list_agent_steps(
    session_id=session_id,
    min_iteration=after_iteration + 1,
    limit=limit,
    order=order,
    )

def list_agent_steps_latest(
    *,
    session_id: str | None = None,
    agent_id: str | None = None,
    limit: int = 20,
):
    """
    Convenience: latest N steps for a session or agent.
    """
    return list_agent_steps(
    session_id=session_id,
    agent_id=agent_id,
    limit=limit,
    order="desc",
    )

