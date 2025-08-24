import lancedb
import pyarrow as pa
from datetime import datetime
import json

from schemas import AGENT_STATE_NAME, AGENTS_URI
AGENTS_DB = lancedb.connect(AGENTS_URI)


def upsert_agent_state(agent_id, status, iteration=None, result=None, context=None, history=None):
    tbl = AGENTS_DB.open_table(AGENT_STATE_NAME)
    now = datetime.now().isoformat()
    rec = {
        "agent_id": agent_id,
        "status": status,
        "iteration": iteration,
        "result": json.dumps(result) if isinstance(result, (dict, list)) else result,
        "last_updated": now,
        "history": json.dumps(history) if history else None,
        "context": json.dumps(context) if context else None,
    }
    tbl.add(data=[rec], mode="overwrite")
    print(f"Agent {agent_id} state = {status}, iter {iteration}, saved at {now}")

def get_agent_state(agent_id):
    tbl = AGENTS_DB.open_table(AGENT_STATE_NAME)
    df = tbl.to_pandas().query(f"agent_id == '{agent_id}'")
    if df.empty:
        return None
    row = df.iloc[0]
    return {
        "agent_id": row.agent_id,
        "status": row.status,
        "iteration": row.iteration,
        "result": json.loads(row.result) if row.result else None,
        "last_updated": row.last_updated,
        "history": json.loads(row.history) if row.history else [],
        "context": json.loads(row.context) if row.context else {}
    }

def list_agent_states():
    tbl = AGENTS_DB.open_table(AGENT_STATE_NAME)
    df = tbl.to_pandas()
    if df.empty:
        return []
    return [get_agent_state(row.agent_id) for _, row in df.iterrows()]