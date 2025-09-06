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

def list_agent_configs(agent_type="JokeAgent"):
    tbl = AGENTS_DB.open_table(AGENTS_CONFIG_NAME)
    if agent_type != "all":
        df = tbl.search().where(f"agent_type = '{agent_type}'").to_pandas()
    else:
        df = tbl.search().to_pandas()

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



def upsert_agent_config(agent_id, agent_type, agent_description: str = "", agents_metadata=None):
    """
    Upsert an agent config by agent_id. If a record exists, update it; otherwise create a new one.
    - agents_metadata may be dict/list (will be json-dumped) or a JSON string. If it's a string,
    it must be valid JSON (object/array); otherwise '{}' is stored.
    Returns: "updated" if an existing row was changed, "created" if a new row was added.
    """
    import json
    from .schemas import AGENTS_CONFIG_NAME
    tbl = AGENTS_DB.open_table(AGENTS_CONFIG_NAME)


    # Normalize metadata to a JSON string for storage
    def _norm_meta(m):
        if m is None or m == "":
            return None
        if isinstance(m, (dict, list)):
            return json.dumps(m)
        if isinstance(m, str):
            s = m.strip()
            if not s:
                return None
            # Ensure it's valid JSON; if not, store {}
            try:
                json.loads(s)
                return s
            except Exception:
                return "{}"
        # Fallback
        return None

    meta_str = _norm_meta(agents_metadata)

    updates = {
        "agent_type": agent_type,
        "agent_description": agent_description,
        "agents_metadata": meta_str,
    }

    try:
        where = f"agent_id == '{agent_id}'"
        print(where)

        updated = tbl.update(where=where, values=updates)
        # Some LanceDB versions return an object; others return an int. Coerce to int if possible.
        try:
            rows_updated = int(getattr(updated, "rows_updated", updated))
            print(f"ROWS updated : {rows_updated}")

        except Exception as e1:
            print(e1)
            rows_updated = 0
    except Exception as e2:
        print(e2)
        rows_updated = 0

    if rows_updated and rows_updated > 0:
        print(f"Upsert updated {rows_updated} record(s) for {agent_id}.")
        return "updated"

    # No existing row -> insert
    rec = {
        "agent_id": agent_id,
        "agent_type": agent_type,
        "agent_description": agent_description,
        "agents_metadata": meta_str,
    }
    tbl.add([rec], mode="append")
    print(f"Upsert created agent config for {agent_id}.")
    return "created"




if __name__ == "__main__":
    create_agent_config("agent1", "JokeAgent", "Tells jokes", {"subject": "python"})
    list_agent_configs()
