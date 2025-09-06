import uuid
import json
from typing import Optional, Literal, Dict, Any, List
from datetime import datetime, timezone

import lancedb
import pandas as pd

from .schemas import AGENTS_URI, CONVERSATIONS_NAME, PARTICIPANTS_NAME, MESSAGES_NAME
import math

DB = lancedb.connect(AGENTS_URI)

VALID_CONVERSATION_STATUSES = {"active", "ended", "archived"}
ORDER_VALUES = {"asc", "desc"}

def _is_nan(v):
    try:
        return v is None or (isinstance(v, float) and math.isnan(v)) or pd.isna(v)
    except Exception:
        return False

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _escape(val: str) -> str:
    return str(val).replace("'", "\'")





def _loads_or(obj, default):
    if obj is None: 
        return default
    if isinstance(obj, (dict, list)): 
        return obj
    if isinstance(obj, str) and obj.strip():
        try: 
            return json.loads(obj)
        except Exception: 
            return default
    return default





def create_conversation(title: Optional[str] = None) -> str:
    cid = str(uuid.uuid4())
    DB.open_table(CONVERSATIONS_NAME).add([{
    "conversation_id": cid,
    "title": (title or f"Conversation {cid[:8]}").strip(),
    "status": "active",
    "created_at": _now_iso(),
    }])
    return cid

def set_conversation_status(conversation_id: str, status: str) -> int:
    if status not in VALID_CONVERSATION_STATUSES:
        raise ValueError(f"Invalid status: {status}. Allowed: {sorted(VALID_CONVERSATION_STATUSES)}")
    res = DB.open_table(CONVERSATIONS_NAME).update(
    where=f"conversation_id == '{_escape(conversation_id)}'",
    values={"status": status},
    )
    return getattr(res, "rows_updated", 0)

def add_participant(conversation_id: str, agent_id: str, session_id: str, persona_config: dict | None = None) -> int:
    DB.open_table(PARTICIPANTS_NAME).add([{
    "conversation_id": conversation_id,
    "agent_id": agent_id,
    "session_id": session_id,
    "persona_config": json.dumps(persona_config or {}),
    "joined_at": _now_iso(),
    }])
    return 1

def conversations(
    status: Optional[str] = "all",
    limit: int = 100,
    offset: int = 0,
    order: Literal["asc", "desc"] = "desc",
    include_participants: bool = False,
) -> Dict[str, Any]:
    """
    Return a JSON-serializable structure for API responses:
    {
    "data": [ {conversation...} ],
    "meta": { total, returned, limit, offset, order, status, has_more, next_offset }
    }
    """
    if order not in ORDER_VALUES:
        raise ValueError(f"order must be one of {sorted(ORDER_VALUES)}")

    q = DB.open_table(CONVERSATIONS_NAME).search()
    if status and status != "all":
        if status not in VALID_CONVERSATION_STATUSES:
            raise ValueError(f"Invalid status: {status}. Allowed: {sorted(VALID_CONVERSATION_STATUSES)}")
        q = q.where(f"status == '{_escape(status)}'")

    df = q.to_pandas()
    total = int(len(df))

    if df.empty:
        return {
            "data": [],
            "meta": {
                "total": 0,
                "returned": 0,
                "limit": limit,
                "offset": offset,
                "order": order,
                "status": status,
                "has_more": False,
                "next_offset": None,
            },
        }

    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df = df.sort_values("created_at", ascending=(order == "asc"))

    if offset:
        df = df.iloc[offset:]
    if limit is not None:
        df = df.iloc[:limit]

    items: List[Dict[str, Any]] = []
    for _, r in df.iterrows():
        created = r.get("created_at")
        items.append({
            "conversation_id": r.get("conversation_id"),
            "title": r.get("title"),
            "status": r.get("status"),
            "created_at": created.isoformat() if pd.notna(created) else None,
        })

    if include_participants and items:
        cids = [i["conversation_id"] for i in items]
        # Build an OR where clause for small pages
        or_clause = " OR ".join([f"conversation_id == '{_escape(cid)}'" for cid in cids])
        part_df = DB.open_table(PARTICIPANTS_NAME).search().where(or_clause).to_pandas()
        if not part_df.empty:
            # Parse persona_config JSON safely
            def _to_json(val):
                if isinstance(val, (dict, list)): return val
                if isinstance(val, str) and val.strip():
                    try: return json.loads(val)
                    except Exception: return {}
                return {}
            part_df["persona_config"] = part_df.get("persona_config", "").apply(_to_json)

            grouped = part_df.groupby("conversation_id")
            participants_map = {
                cid: [
                    {
                        "agent_id": row.agent_id,
                        "session_id": row.session_id,
                        "persona_config": row.persona_config,
                        "joined_at": row.joined_at,
                    }
                    for _, row in grp.iterrows()
                ]
                for cid, grp in grouped
            }
            for item in items:
                item["participants"] = participants_map.get(item["conversation_id"], [])

    returned = len(items)
    has_more = total > (offset + returned)
    return {
        "data": items,
        "meta": {
            "total": total,
            "returned": returned,
            "limit": limit,
            "offset": offset,
            "order": order,
            "status": status,
            "has_more": has_more,
            "next_offset": (offset + returned) if has_more else None,
        },
    }

def list_conversations_for_window(
    status: str | None = "all",
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
    order: str = "desc",  # by updated_at
):
    conv_tbl = DB.open_table(CONVERSATIONS_NAME)
    msg_tbl = DB.open_table(MESSAGES_NAME)
    q_conv = conv_tbl.search()
    if status and status != "all":
        q_conv = q_conv.where(f"status == '{status}'")       # FIXME FOR PROD
    conv_df = q_conv.to_pandas()

    if conv_df.empty:
        return []

    conv_df["created_at"] = pd.to_datetime(conv_df["created_at"], errors="coerce")

    try:
        msg_df = msg_tbl.search().to_pandas()
    except Exception:
        msg_df = pd.DataFrame()

    if not msg_df.empty:
        msg_df["created_at"] = pd.to_datetime(msg_df["created_at"], errors="coerce")
        msg_df = msg_df.sort_values("created_at")
        last_msg = msg_df.drop_duplicates(subset=["conversation_id"], keep="last")
        last_msg = last_msg[["conversation_id", "created_at", "text"]].rename(
            columns={"created_at": "last_msg_at", "text": "preview"}
        )
        merged = conv_df.merge(last_msg, on="conversation_id", how="left")
    else:
        merged = conv_df.copy()
        merged["last_msg_at"] = pd.NaT
        merged["preview"] = ""

    merged["updated_at"] = merged["last_msg_at"].fillna(merged["created_at"])

    # Optional search
    if q:
        ql = q.strip().lower()
        merged["__t"] = (merged["title"].fillna("").astype(str).str.lower()) + " " + (
            merged["preview"].fillna("").astype(str).str.lower()
        )
        merged = merged[merged["__t"].str.contains(ql, na=False)]
        merged = merged.drop(columns=["__t"])

    # Ensure JSON-safe columns (no NaN/NaT)
    merged["preview"] = merged["preview"].astype(object)
    merged.loc[pd.isna(merged["preview"]), "preview"] = ""
    merged["title"] = merged["title"].astype(object)
    merged.loc[pd.isna(merged["title"]), "title"] = None
    merged["status"] = merged["status"].astype(object)
    merged.loc[pd.isna(merged["status"]), "status"] = None

    merged = merged.sort_values("updated_at", ascending=(order == "asc"))
    if offset:
        merged = merged.iloc[offset:]
    if limit is not None:
        merged = merged.iloc[:limit]

    items = []
    for _, r in merged.iterrows():
        upd = r.get("updated_at")
        updated_at = upd.isoformat() if pd.notna(upd) else None
        title = None if _is_nan(r.get("title")) else r.get("title")
        preview = "" if _is_nan(r.get("preview")) else r.get("preview")
        status_val = None if _is_nan(r.get("status")) else r.get("status")

        items.append({
            "id": r.get("conversation_id"),
            "title": title,
            "status": status_val,
            "updated_at": updated_at,
            "last_updated": updated_at,   # UI fallback
            "preview": preview,
        })
    return items

def get_conversation_messages_and_participants(
    conversation_id: str,
    *,
    limit: int = 500,
    offset: int = 0,
    order: str = "asc",   # messages in time order
    ):
    msg_tbl = DB.open_table(MESSAGES_NAME)
    part_tbl = DB.open_table(PARTICIPANTS_NAME)

    # Messages
    mdf = (
        msg_tbl.search()
        .where(f"conversation_id == '{_escape(conversation_id)}'")
        .to_pandas()
    )
    if not mdf.empty:
        mdf["created_at"] = pd.to_datetime(mdf["created_at"], errors="coerce")
        mdf = mdf.sort_values("created_at", ascending=(order == "asc"))
        if offset:
            mdf = mdf.iloc[offset:]
        if limit is not None:
            mdf = mdf.iloc[:limit]
    msgs = []
    for _, r in mdf.iterrows():
        ts = r.get("created_at")
        msgs.append({
            "id": r.get("message_id"),
            "message_id": r.get("message_id"),
            "conversation_id": r.get("conversation_id"),
            "author_id": r.get("author_id"),
            "role": r.get("role"),
            "text": "" if _is_nan(r.get("text")) else r.get("text"),
            "created_at": ts.isoformat() if pd.notna(ts) else None,
            "reply_to": None if _is_nan(r.get("reply_to")) else r.get("reply_to"),
            "meta": _loads_or(r.get("meta"), default={}),
        })

    # Participants
    pdf = (
        part_tbl.search()
        .where(f"conversation_id == '{_escape(conversation_id)}'")
        .to_pandas()
    )
    participants = []
    for _, r in pdf.iterrows():
        joined = r.get("joined_at")
        participants.append({
            "conversation_id": r.get("conversation_id"),
            "name": r.get("agent_id"),
            "session_id": r.get("session_id"),
            "persona_config": _loads_or(r.get("persona_config"), default={}),
            "joined_at": joined if isinstance(joined, str) else (joined.isoformat() if pd.notna(joined) else None),
        })

    return {"messages": msgs, "participants": participants}



def participant_exists(conversation_id: str, agent_id: str, session_id: str) -> bool:
    tbl = DB.open_table(PARTICIPANTS_NAME)
    df = tbl.search().where(
    f"conversation_id == '{_escape(conversation_id)}' AND agent_id == '{_escape(agent_id)}' AND session_id == '{_escape(session_id)}'"
    ).to_pandas()
    return (df is not None) and (not df.empty)

def add_participant_if_absent(conversation_id: str, agent_id: str, session_id: str, persona_config: dict | None = None) -> int:
    if participant_exists(conversation_id, agent_id, session_id):
        return 0
    return add_participant(conversation_id, agent_id, session_id, persona_config)


def list_participants(conversation_id: str) -> list[dict]:
    tbl = DB.open_table(PARTICIPANTS_NAME)
    df = tbl.search().where(f"conversation_id == '{conversation_id}'").to_pandas()
    if df is None or df.empty:
        return []
    import json
    def _to_json(val):
        if isinstance(val, (dict, list)): return val
        if isinstance(val, str) and val.strip():
            try: 
                return json.loads(val)
            except Exception: return {}
        return {}
    
    df["persona_config"] = df.get("persona_config", "").apply(_to_json)
    out = []
    for _, r in df.iterrows():
        out.append({
        "agent_id": r.get("agent_id"),
        "session_id": r.get("session_id"),
        "persona_config": r.get("persona_config") or {},
        "joined_at": r.get("joined_at"),
        })
    return out


