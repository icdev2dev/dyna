# FIRST REPL Bootstrap a clean DB and start background loops
import os, shutil, threading, asyncio, time
DB_PATH = "/tmp/agents_demo"
os.environ["AGENTS_URI"] = DB_PATH

if os.path.exists(DB_PATH):
    shutil.rmtree(DB_PATH)

from store.schemas import create_all_schemas, create_conversation_schemas
create_all_schemas()
create_conversation_schemas()

from queue_imp import delete_all_actions
delete_all_actions()

import agents
bg = threading.Thread(target=lambda: asyncio.run(agents.main()), daemon=True)
bg.start()
print("Background agent loops started.")



# SECOND REPL
## 0
import os, shutil, threading, asyncio, time
DB_PATH = "/tmp/agents_demo"
os.environ["AGENTS_URI"] = DB_PATH


## Simple Test

### Create Conversation

from queue_imp import create_conversation, persona_agent_create
cid = create_conversation("Three agents test")

### Create Agent in conversation
sid_a = persona_agent_create("agent_alice", "repl", cid, {"name": "Alice", "tone": "friendly"})


### See Participants
from store.conversations import get_conversation_messages_and_participants
snapshot = get_conversation_messages_and_participants(cid) 
for participant in snapshot['participants']:
    print (f"{participant['name']} Persona: {participant['persona_config']}")

### First Message 

from store.messages import append_message 
append_message(cid, "user", "user", "Hello everyone, what do you think about autonomous agents?")

### See First response from Alice

snapshot = get_conversation_messages_and_participants(cid) 
for message in snapshot['messages']:
    if message['author_id'] == 'agent_alice':
        print (f"{message}")

### Speak Now Interrupt

from queue_imp import agent_interrupt_action
agent_interrupt_action("agent_alice", sid_a, "repl", {"type": "speak_now"})

### Pause Alice

from store.agent_state import get_agent_state
from queue_imp import agent_pause_action

get_agent_state("agent_alice", sid_a)['status']  # status should be "running"
agent_pause_action("agent_alice", sid_a) 
get_agent_state("agent_alice", sid_a)['status'] # status should be "paused"

- send message 
append_message(cid, "user", "user", "Hello everyone, can you please reply asap?")

- notice that alice is paused

snapshot = get_conversation_messages_and_participants(cid) 
for message in snapshot['messages']:
    if message['author_id'] == 'agent_alice':
        print (f"{message}")

### Resume Alice

from queue_imp import agent_resume_action
agent_resume_action("agent_alice", sid_a)

## Add two more agents

sid_b = persona_agent_create("agent_bob",   "repl", cid, {"name": "Bob",   "tone": "dry"})
sid_c = persona_agent_create("agent_cara",  "repl", cid, {"name": "Cara",  "tone": "excited"})


### See Participants
snapshot = get_conversation_messages_and_participants(cid) 
for participant in snapshot['participants']:
    print (f"{participant['name']} Persona: {participant['persona_config']}")






## 0.1  Functions

def wait_until(fn, timeout=20, interval=0.5):
    start = time.time()
    while time.time() - start < timeout:
        try:
            val = fn()
            if val:
                return val
        except Exception:
            pass
        time.sleep(interval)
    return None

def last_text():
    rows = list_agent_steps_latest(session_id=session_id, limit=1)
    print(rows)
    if rows:
        return rows[0].get("text")
    return None


## COnversations 
>>> from store.conversations import conversations
>>> resp = conversations(status="all", limit=100, offset=0, order="desc", include_participants=True)
>>> print(resp["data"])

##  messages too (for a given conversation_id):
from store.conversations import get_conversation_messages_and_participants

detail = get_conversation_messages_and_participants("80b01006-7dca-488f-b2c2-758bfb6c34f1", limit=200, order="asc")
print(detail["messages"])
print(detail["participants"])

## 1) Create a conversation and a PersonaAgent
from queue_imp import create_conversation, persona_agent_create
from store.agent_state import get_agent_state

conv_id = create_conversation("Demo Conversation")
print("Conversation:", conv_id)

agent_id = "agent-alpha"
persona_cfg = {"name": "Alpha", "tone": "friendly"}
session_id = persona_agent_create(agent_id, "user", conv_id, persona_cfg)
print("Session:", session_id)


assert wait_until(lambda: (get_agent_state(agent_id, session_id) or {}).get("status") == "running"), "Agent did not reach running state."

## 2) Phase 4: Send a message; agent should reply (interrupt via fan-out)
from store.messages import append_message
from store.agent_steps import list_agent_steps_latest

append_message(conv_id, "user", "user", "Hello Alpha, first message!")


reply1 = wait_until(last_text, timeout=12, interval=0.5)
print("First reply:", reply1)

## 3) Phase 6: Cooldown bypass on new_message (send a second message immediately)
append_message(conv_id, "user", "user", "Second message right away!")

reply2 = wait_until(last_text, timeout=10, interval=0.5)
print("Second reply (should be immediate due to new_message):", reply2)

### Inspect agent context (last_seen_iso, last_msg_id)
st_ctx = (get_agent_state(agent_id, session_id) or {}).get("context", {})
print("Context after two messages:", st_ctx)

## 4) Participants dedupe check (should be a single row for this conversation/agent/session)
import lancedb
from store.schemas import AGENTS_URI, PARTICIPANTS_NAME
DB = lancedb.connect(AGENTS_URI)
pdf = DB.open_table(PARTICIPANTS_NAME).search().where(f"conversation_id == '{conv_id}'").to_pandas()
subset = pdf[(pdf["conversation_id"] == conv_id) & (pdf["agent_id"] == agent_id) & (pdf["session_id"] == session_id)]
print("Participants rows for (conv,agent,session):", len(subset))
assert len(subset) == 1, "Duplicate participant rows detected (should be deduped)."

## 5) Phase 5: Rehydration test
### Option A: automatic (wait ~65s); Option B: manual (immediate). Manual shown below.
from queue_imp import stop_agent, agent_interrupt_action, persona_agent_create

### Stop the agent
stop_agent(session_id, reason="rehydration test")
assert wait_until(lambda: (get_agent_state(agent_id, session_id) or {}).get("status") == "stopped", timeout=12), "Agent did not stop."

### Manual rehydration (immediate)
persona_agent_create(agent_id, "rehydrator", conv_id, persona_cfg, session_id=session_id)

### Pull last_seen_iso from stored state and send rehydrate guidance
lsi = (get_agent_state(agent_id, session_id) or {}).get("context", {}).get("last_seen_iso")
agent_interrupt_action(agent_id, session_id, "rehydrator", {"type": "rehydrate", "last_seen_iso": lsi})

assert wait_until(lambda: (get_agent_state(agent_id, session_id) or {}).get("status") == "running", timeout=12), "Agent did not rehydrate to running."

### Re-check participants count remains 1 (add_participant_if_absent prevents duplicates)
pdf2 = DB.open_table(PARTICIPANTS_NAME).search().where(f"conversation_id == '{conv_id}'").to_pandas()
subset2 = pdf2[(pdf2["conversation_id"] == conv_id) & (pdf2["agent_id"] == agent_id) & (pdf2["session_id"] == session_id)]
print("Participants rows post-rehydrate:", len(subset2))
assert len(subset2) == 1, "Duplicate participant row created during rehydration."

## 6) After rehydration: send another message; ensure single fresh reply and updated context
append_message(conv_id, "user", "user", "Hello again after rehydration!")

reply3 = wait_until(last_text, timeout=12, interval=0.5)
print("Reply after rehydration:", reply3)

st_ctx2 = (get_agent_state(agent_id, session_id) or {}).get("context", {})
print("Context after rehydration reply:", st_ctx2)

## What to expect

First and second replies appear promptly; the second one should bypass cooldown due to new_message guidance.
Context contains last_seen_iso and last_msg_id.
Participants table shows a single row for (conversation_id, agent_id, session_id), even after rehydration.
After manual rehydration, the agent resumes running and responds to new messages without replaying older ones.
Notes

If you prefer automatic rehydration, skip the “manual rehydration” block and instead sleep ~65s after stop_agent; the background rehydrator runs every 60s.

