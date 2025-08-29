
import pyarrow as pa
import lancedb
import os
from dotenv import load_dotenv
load_dotenv()

AGENTS_URI = os.getenv('AGENTS_URI')
AGENTS_DB = lancedb.connect(AGENTS_URI)


AGENT_STEPS_NAME = "agent_steps"

AGENT_STEPS_SCHEMA = pa.schema([
    pa.field("id", pa.string(), nullable=False),             # uuid per row
    pa.field("created_at", pa.string(), nullable=False),     # ISO timestamp
    pa.field("agent_id", pa.string(), nullable=False),
    pa.field("session_id", pa.string(), nullable=True),      # nullable for now
    pa.field("iteration", pa.int32(), nullable=False),       # runner’s counter
    pa.field("step_token", pa.string(), nullable=True),      # future: moniker step (string)
    pa.field("next_step_token", pa.string(), nullable=True), # future: moniker next step (string)
    pa.field("status", pa.string(), nullable=True),          # "ok" | "error" | "info"
    pa.field("text", pa.string(), nullable=True),            # human output
    pa.field("data", pa.string(), nullable=True),            # JSON string (optional)
    pa.field("state", pa.string(), nullable=True),           # JSON string (post-step state)
    pa.field("guidance", pa.string(), nullable=True),        # JSON string (applied guidance)
    pa.field("notes", pa.string(), nullable=True),
    pa.field("latency_ms", pa.int32(), nullable=True),
    pa.field("error", pa.string(), nullable=True),
])

def create_agent_steps_schema():
    print("creating agent_steps_schema")
    AGENTS_DB.create_table(AGENT_STEPS_NAME, schema=AGENT_STEPS_SCHEMA)

def delete_agent_steps_schema():
    print("deleting agent_steps_schema")
    AGENTS_DB.drop_table(AGENT_STEPS_NAME)



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
    pa.field("session_id", pa.string(), nullable=True),  # NEW
])


AGENT_STATE_NAME = "agent_state"

AGENT_STATE_SCHEMA = pa.schema([
    pa.field("agent_id", pa.string(), nullable=False),
    pa.field("session_id", pa.string(), nullable=True),   # NEW
    pa.field("status", pa.string(), nullable=False),
    pa.field("iteration", pa.int32(), nullable=True),
    pa.field("result", pa.string(), nullable=True),        # could be JSON string
    pa.field("last_updated", pa.string(), nullable=True),
    pa.field("history", pa.string(), nullable=True),        # JSON list or log
    pa.field("context", pa.string(), nullable=True),        # agentic data
])



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



def create_all_schemas():
    create_agent_state_schema()
    create_agent_steps_schema()
    create_queue_schema()
#    create_agents_config_schema()

def delete_all_schemas():
    delete_agent_state_schema()
    delete_agent_steps_schema()
    delete_queue_schema()

if __name__ == "__main__":
    create_all_schemas()

