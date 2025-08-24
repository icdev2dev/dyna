import lancedb
import json

from .schemas import AGENTS_URI, AGENTS_CONFIG_NAME

AGENTS_DB = lancedb.connect(AGENTS_URI)

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

if __name__ == "__main__":
    create_agent_config("agent1", "JokeAgent", "Tells jokes", {"subject": "python"})
    list_agent_configs()
