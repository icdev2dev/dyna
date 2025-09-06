
import lancedb
import uuid
from datetime import datetime, timezone

from schemas import AGENTS_URI, QUEUE_NAME

AGENTS_DB = lancedb.connect(AGENTS_URI)


# --------------------
# Action Queue Management
# --------------------


def create_action(
    action_type: str,
    actor: str,
    payload: str = None,
    metadata: str = None,
    urgency: str = "normal",
    description: str = "",
    processed: bool = False,
    action_id: str = None,
    created_at: str = None,
):
    queue_tbl = AGENTS_DB.open_table(QUEUE_NAME)
    record = {
        "action_id": action_id or str(uuid.uuid4()),
        "type": action_type,
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "processed": processed,
        "urgency": urgency,
        "description": description,
        "payload": payload,
        "metadata": metadata,
    }
    queue_tbl.add(data=[record], mode="append")
    print(f"Action '{action_type}' for actor '{actor}' queued.")

def list_actions():
    queue_tbl = AGENTS_DB.open_table(QUEUE_NAME)
    df = queue_tbl.to_pandas()
    print(df)
    return df.to_dict(orient="records")

def delete_all_actions():
    queue_tbl = AGENTS_DB.open_table(QUEUE_NAME)
    queue_tbl.delete("1 == 1")

if __name__ == "__main__":
    create_action("create_agent", "user")

    list_actions()
    pass