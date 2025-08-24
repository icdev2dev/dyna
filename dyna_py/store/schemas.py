
import pyarrow as pa
import lancedb
AGENTS_URI = "data/agents"

AGENTS_CONFIG_NAME = "agents_config"
AGENTS_CONFIG_SCHEMA = pa.schema([
    pa.field("agent_id", pa.string(), nullable=False),
    pa.field("agent_type", pa.string(), nullable=False),
    pa.field("agent_description", pa.string(), nullable=True),
    pa.field("agents_metadata", pa.string(), nullable=True),
])


QUEUE_NAME = "queue"
QUEUE_SCHEMA = pa.schema([
    pa.field("action_id", pa.string(), nullable=False),
    pa.field("type", pa.string(), nullable=False),
    pa.field("created_at", pa.string(), nullable=False),
    pa.field("actor", pa.string(), nullable=False),
    pa.field("processed", pa.bool_(), nullable=False),
    pa.field("urgency", pa.string()),
    pa.field("description", pa.string()),
    pa.field("payload", pa.string()),
    pa.field("metadata", pa.string()),
])


AGENT_STATE_NAME = "agent_state"

AGENT_STATE_SCHEMA = pa.schema([
    pa.field("agent_id", pa.string(), nullable=False),
    pa.field("status", pa.string(), nullable=False),
    pa.field("iteration", pa.int32(), nullable=True),
    pa.field("result", pa.string(), nullable=True),        # could be JSON string
    pa.field("last_updated", pa.string(), nullable=True),
    pa.field("history", pa.string(), nullable=True),        # JSON list or log
    pa.field("context", pa.string(), nullable=True),        # agentic data
])





AGENTS_DB = lancedb.connect(AGENTS_URI)


# --------------------
# Schema management
# --------------------



def create_agent_state_schema():
    print("creating agent state schema")
    AGENTS_DB.create_table(AGENT_STATE_NAME, schema=AGENT_STATE_SCHEMA)

def delete_agent_state_schema():
    print("deleting agent state schema")
    AGENTS_DB.drop_table(AGENT_STATE_NAME)


def create_agents_config_schema():
    print("creating agent config schema")
    AGENTS_DB.create_table(AGENTS_CONFIG_NAME, schema=AGENTS_CONFIG_SCHEMA)

def delete_agents_schema():
    print("deleting agent config schema")
    AGENTS_DB.drop_table(AGENTS_CONFIG_NAME)

def create_queue_schema():
    print("creating_queue_schema")
    AGENTS_DB.create_table(QUEUE_NAME, schema=QUEUE_SCHEMA)

def delete_queue_schema():
    print("deleting_queue_schema")
    AGENTS_DB.drop_table(QUEUE_NAME)

if __name__ == '__main__':
    create_agents_config_schema()


