import lancedb, uuid, json
from datetime import datetime, timezone
import pandas as pd
from .schemas import AGENTS_URI, MESSAGES_NAME
DB = lancedb.connect(AGENTS_URI)

def append_message(conversation_id: str, author_id: str, role: str, text: str, reply_to: str | None = None, meta: dict | None = None) -> str:
    mid = str(uuid.uuid4())
    DB.open_table(MESSAGES_NAME).add([{
    "message_id": mid,
    "conversation_id": conversation_id,
    "author_id": author_id,
    "role": role,
    "text": text,
    "created_at": datetime.now(timezone.utc).isoformat(),
    "reply_to": reply_to,
    "meta": json.dumps(meta) if meta else None,
    }])
    return mid


def list_messages_since(conversation_id: str, since_iso: str | None, limit: int = 50) -> list[dict]:
    tbl = DB.open_table(MESSAGES_NAME)
    q = tbl.search().where(f"conversation_id == '{conversation_id}'")
    df = q.to_pandas()
    if df is None or df.empty:
        return []
    df["created_at_dt"] = pd.to_datetime(df["created_at"], errors="coerce")
    if since_iso:
        cutoff = pd.to_datetime(since_iso, errors="coerce")
        df = df[df["created_at_dt"] > cutoff]
    df = df.sort_values("created_at_dt").iloc[:limit]
    return df.drop(columns=["created_at_dt"]).to_dict(orient="records")

def latest_message(conversation_id: str) -> dict | None:
    tbl = DB.open_table(MESSAGES_NAME)
    df = tbl.search().where(f"conversation_id == '{conversation_id}'").to_pandas()
    if df is None or df.empty: return None
    df["created_at_dt"] = pd.to_datetime(df["created_at"], errors="coerce")
    row = df.sort_values("created_at_dt").iloc[-1]
    return row.to_dict()
