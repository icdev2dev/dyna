import lancedb
import pyarrow as pa
import pandas as pd
from datetime import datetime
import uuid
import json

from store.schemas import AGENTS_URI, AGENTS_CONFIG_NAME, QUEUE_NAME
from store.sessions import get_agent_id_for_session_id

# --------------------
# Database Setup
# --------------------

AGENTS_DB = lancedb.connect(AGENTS_URI)


# --------------------
# Agent Config (Metadata) Management
# --------------------
def create_agent_config(agent_id, agent_type, agent_description="", agents_metadata=None):
    tbl = AGENTS_DB.open_table(AGENTS_CONFIG_NAME)
    record = {
        "agent_id": agent_id,
        "agent_type": agent_type,
        "agent_description": agent_description,
        "agents_metadata": json.dumps(agents_metadata) if agents_metadata else None,
    }
    tbl.add(data=[record], mode="append")
    print(f"AgentConfig for {agent_id} ({agent_type}) created.")

def update_agent_config(agent_id, agent_type=None, agent_description=None, agents_metadata=None):
    tbl = AGENTS_DB.open_table(AGENTS_CONFIG_NAME)
    updates = {}
    if agent_type is not None: updates["agent_type"] = agent_type
    if agent_description is not None: updates["agent_description"] = agent_description
    if agents_metadata is not None: updates["agents_metadata"] = json.dumps(agents_metadata)
    if not updates:
        print("No updates provided.")
        return
    count = tbl.update(where=f"agent_id == '{agent_id}'", updates=updates)
    print(f"Updated {count} AgentConfig record(s) for {agent_id}.")

def delete_agent_config(agent_id):
    tbl = AGENTS_DB.open_table(AGENTS_CONFIG_NAME)
    count = tbl.delete(where=f"agent_id == '{agent_id}'")
    print(f"Deleted {count} AgentConfig record(s) for {agent_id}.")

def list_agent_configs():
    tbl = AGENTS_DB.open_table(AGENTS_CONFIG_NAME)
    df = tbl.to_pandas()
    if df.empty:
        print("No agent configs found.")
        return []
    configs = []
    for _, row in df.iterrows():
        metadata = json.loads(row.agents_metadata or '{}')
        print(f"agent_id={row.agent_id}, type={row.agent_type}, desc={row.agent_description}, metadata={metadata}")
        configs.append({
            "agent_id": row.agent_id,
            "agent_type": row.agent_type,
            "agent_description": row.agent_description,
            "agents_metadata": metadata
        })
    return configs

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
    session_id: str | None = None
):
    queue_tbl = AGENTS_DB.open_table(QUEUE_NAME)
    record = {
        "action_id": action_id or str(uuid.uuid4()),
        "type": action_type,
        "created_at": created_at or datetime.now().isoformat(),
        "actor": actor,
        "processed": processed,
        "urgency": urgency,
        "description": description,
        "payload": payload,
        "metadata": metadata,
        "session_id": session_id,
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

# --------------------
# Helper: Agent action creators
# --------------------
def agent_create(agent_id, actor, initial_subject="foot", session_id: str | None = None):
    sid = session_id or str(uuid.uuid4())
    payload = json.dumps({ "agent_id": agent_id, "initial_subject": initial_subject, "session_id": sid})
    create_action( action_type="create_agent", actor=actor, payload=payload, session_id=sid)
    return sid

def agent_destroy_action(agent_id, actor, reason=None,  session_id: str | None = None):
    payload = json.dumps({"agent_id": agent_id, "reason": reason, "session_id": session_id})
    create_action(action_type="agent_destroy", actor=actor, payload=payload, session_id=session_id)
    return("ok")


def stop_agent(session_id, reason=None):
    agent_id = get_agent_id_for_session_id(session_id=session_id)
    if agent_id:
        agent_destroy_action(agent_id=agent_id, actor="user", reason=reason, session_id=session_id)



def agent_interrupt_action(agent_id, session_id, actor="user", guidance: dict = {} ):
    payload = json.dumps({ "agent_id": agent_id, "session_id": session_id, "guidance": guidance})
    create_action( action_type="agent_interrupt", actor=actor, payload=payload,session_id=session_id)
    
    return("ok")


def agent_pause_action(agent_id, session_id: str , reason="user initiated", actor="user"):
    payload = json.dumps({"agent_id": agent_id, "reason": reason, "session_id": session_id})
    create_action(action_type="agent_pause", actor=actor, payload=payload, session_id=session_id)
    return("ok")

def agent_resume_action(agent_id, session_id: str , actor="user", ):
    payload = json.dumps({"agent_id": agent_id, "session_id": session_id})
    create_action(action_type="agent_resume", actor=actor, payload=payload, session_id=session_id)
    return("ok")

# --------------------
# Async Helper
# --------------------

async def mark_action_processed_async(async_tbl, action_id: str):
    await async_tbl.update(where=f'action_id == "{action_id}"', updates={"processed": True})

# --------------------
# Main/test (remove or modify as needed)
# --------------------
if __name__ == "__main__":
    # Example: create and list agent configs
#    create_agents_config_schema()
    create_agent_config("agent1", "JokeAgent", "Tells programming jokes", {"initial_subject": "python"})
    list_agent_configs()
#    agent_create("agent1", "user", initial_subject="bananas")
#    agent_interrupt("agent1", "user", {"subject": "knock-knock"})
#    list_actions()
