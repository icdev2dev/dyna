# LoopingAgentBase and Agents Framework – Consolidated Developer Guide (current repo state)

# Overview

Goal: Make it easy to build long‑running, persistent, interruptible agents. Subclass LoopingAgentBase to get a robust async loop, state/step persistence, and optional pause/interrupt behavior via mixins.

# Architecture:
agent_loop.Loop­ingAgentBase runs the loop and calls your hooks.
Mixins in agent_core provide Pause and Interrupt capabilities.
Persistence is handled by store.agent_state (state snapshots) and store.steps_async (per‑tick steps).
An action queue in LanceDB drives create/pause/resume/interrupt/destroy actions (agents.py + agent.py).
WebSocket updates are emitted on step append (ws_bus + store.agent_steps), consumed by the UI.

# What LoopingAgentBase Provides

Main async loop with start/stop lifecycle and per‑tick persistence.
Optional pause and interrupt support (duck‑typed: if you inherit the mixins, the base will use them).
Guidance handling: normalize raw guidance, call your apply_guidance, and persist guidance alongside steps.
Error capture and per‑tick status updates; default continues on errors.
Context snapshotting for observability.

# What Subclasses Typically Implement

initial_context() → dict (optional). Initial context included in state updates. If you don’t set agent_type, the base sets it to your class name.
on_start()/on_stop() (optional) for setup/cleanup.
do_tick(step) → StepOutcome (required). One unit of work per tick.
apply_guidance(g) → dict (optional). Update internal state based on structured or raw guidance, and return a context delta that the base merges into the persisted context.

# Current Loop Behavior (as implemented)

Pause and interrupts order: the loop checks the pause first, then interrupts, then runs do_tick, sleeps loop_interval seconds, and increments the step counter.
While paused: the loop blocks on wait_if_paused(). Interrupts are not processed until the agent is resumed. This is important: despite earlier design notes about “soft pause,” the current code does not process interrupts while paused.
Interrupts: One interrupt is fetched non‑blockingly per loop iteration if present; guidance is normalized and applied (with context delta merged), then do_tick runs.

# Guidance Handling

GuidanceInput can be str | dict | list | None.
Default interpret_guidance behavior:
If a custom guidance_interpreter callable is passed to the constructor, it is awaited.
If not, dict passes through, None returns None, strings are wrapped as {"_raw_text": "..."}.
apply_guidance(normalized) is where your agent updates its internal fields and returns a context delta dict for observability.

# Persistence:
You can configure persist_guidance_raw and persist_guidance_normalized in the constructor.
If outcome.guidance is empty but guidance was processed this tick, the base attaches a guidance object automatically (containing raw and/or normalized per flags).

# Error Handling

If do_tick raises, the base:
Records a step with status="error" and the error message.
Updates agent_state with status="running" by default so the loop continues.
You can override should_continue_on_error(exc) to stop on certain exceptions.

# Persistence Details

On every tick, LoopingAgentBase:
Appends a step via steps_appender (if provided) with fields: status, text, data, state, guidance, notes, latency_ms, error.
Updates agent_state via state_updater (if provided) with status="running", iteration, result (text or error), and the current context snapshot.
Context snapshot:
Is a dict maintained by the base and merged with deltas from initial_context(), on_start(), and apply_guidance().
Always includes "paused": True/False if PauseMixin is present.
Serialization:
state, data, guidance fields are stored as JSON strings when dict/list, or left as strings otherwise.
# Lifecycle Summary

## run():
starting → on_start() → running
Loop: wait_if_paused() → check_interrupt() → interpret/apply guidance → do_tick() → append step → upsert state → sleep(loop_interval)
When stop requested: on_stop() → final state "stopped"
## Helpers you can call:
request_stop() to end from inside do_tick.
_paused_flag() returns True/False if PauseMixin is present.
_context_snapshot() returns the current context with paused added.
### StepOutcome Dataclass

Fields you can return from do_tick (or any value, which is coerced to StepOutcome(text=str(value))):
status: "ok" | "error" | "info" (default "ok")
text: str | None
data: dict | list | str | None
state: dict | list | None
notes: str | None
latency_ms: int | None
error: str | None
guidance: dict | None (usually unnecessary to set; base fills if guidance occurred this tick)
Best practice: include a small, useful state snapshot every tick (e.g., subject, paused, mode, conversation_id).


### Constructor and Configuration (LoopingAgentBase)

init(agent_id, session_id, state_updater=None, steps_appender=None, loop_interval=3.0, guidance_interpreter=None, persist_guidance_raw=True, persist_guidance_normalized=True)
state_updater: async callable(agent_id, status, iteration, result, context, history). In this repo, agent.py provides upsert_state_async partial for JokeAgent. PersonaAgent wiring currently uses the Ellipsis placeholder (see note below).
steps_appender: async callable(agent_id, iteration, **fields). In this repo, store.steps_async.append_step_async is used for JokeAgent via functools.partial inside agent_create.
loop_interval: seconds between ticks. You can adjust at runtime if needed.
guidance_interpreter: async callable(raw_guidance) → dict for custom normalization.

### Mixins (agent_core)

PauseMixin:
pause(), resume(), is_paused(), wait_if_paused()
In current loop, pause fully blocks the loop before interrupt handling. You must resume to process queued guidance.
InterruptMixin:
interrupt(guidance): enqueue guidance
check_interrupt(): get one queued guidance if any, else None
StopMixin (built into LoopingAgentBase): request_stop(), should_stop()

# Agents Included in Repo

## JokeAgent (joke_agent.py)
Inherits PauseMixin, InterruptMixin, and LoopingAgentBase.
Constructor parameters:
initial_subject="foot"
loop_interval=30.0 (default here is relatively large)
state_updater and steps_appender must be provided; agent.py wires them correctly for JokeAgent.
initial_context: {"agent_type": "JokeAgent", "subject": self.current_subject}
apply_guidance:
structured: {"subject": "..."} sets the subject
free‑form: naive regex on "_raw_text" for "subject: X" or "about X"
do_tick:
Calls baml_client async TellAJokeV2 with current_subject
Returns StepOutcome with text and state={"subject": ..., "paused": ...}
## 2. PersonaAgent (persona_agent.py) – Conversations as first‑class

- Inherits PauseMixin, InterruptMixin, and LoopingAgentBase.

- Purpose: autonomous chat participants bound to a conversation_id, reading/writing messages in LanceDB.

- Constructor parameters:
conversation_id: required
persona_config: dict, e.g., {"name": "Arthur", "tone": "bemused"}
loop_interval default 1.5s; cooldown_seconds default 2.0s
Note: In agent_create (agent.py), PersonaAgent is currently constructed with state_updater=... and steps_appender=... placeholders (Python Ellipsis). These are not valid callables and will break persistence if left as is. You must pass real callables (see “Wiring notes” below).

- initial_context: {"agent_type": "PersonaAgent", "conversation_id": ..., "persona": name or agent_id}

- Guidance (apply_guidance):
{"type":"set_tone","tone": "..."} updates persona_config["tone"], returns context delta {"tone": "..."}
{"type":"speak_now"} sets self._force_tick=True (note: not currently used by the base loop)
{"type":"set_cooldown","seconds": N} updates cooldown_seconds, returns context delta

- Tick behavior (do_tick):
Reads messages newer than last_seen_iso (list_messages_since)
Skips if no messages, or if last message was authored by self, or if cooldown not elapsed
Otherwise generates a reply (trivial echo template using persona and tone) and appends it to messages
Updates self._last_spoke_at and returns StepOutcome with state including conversation_id and tone

- Activation rule (current):
Speak if there are new messages, the last message isn’t from me, and cooldown has elapsed.
Simple; consider refining in your subclass.

- Important current limitation:
_force_tick is set by guidance but not consumed by the base loop. There is no immediate “speak now” tick unless the next heartbeat arrives.

## Data Model (LanceDB)
New tables added for conversations:

conversations: conversation_id (PK), title, status ("active" | "ended"), created_at
messages: message_id (PK), conversation_id (FK), author_id (agent_id or "user"), role ("agent" | "user" | "system"), text, created_at, reply_to, meta (JSON string)
participants: conversation_id (FK), agent_id, session_id, persona_config (JSON), joined_at Helpers:
store/conversations.py:
create_conversation(title) → conversation_id
set_conversation_status(conversation_id, status)
add_participant(conversation_id, agent_id, session_id, persona_config)
store/messages.py:
append_message(conversation_id, author_id, role, text, reply_to=None, meta=None) → message_id
list_messages_since(conversation_id, since_iso, limit=K) → list[dict]
latest_message(conversation_id) → dict | None
Schemas and Initialization

store/schemas.py defines schemas and creation helpers.
create_all_schemas() currently creates only agent_state, agent_steps, and queue tables.
Conversations/messages/participants require calling create_conversation_schemas() separately (not included in create_all_schemas). Ensure you run this before using PersonaAgent.

# Agent Runner and Actions

agents.py:
queue_watcher() polls the queue and dispatches actions via agent.handle_actions.
poll interval: 15 seconds (poll_lancedb_for_actions sleeps 15s). Reduce for snappier interrupts.
agent.py ACTION_HANDLERS:
create_agent: creates and starts an agent task
JokeAgent: wires state_updater and steps_appender correctly using functools.partial
PersonaAgent: currently passes state_updater=... and steps_appender=... placeholders (Ellipsis). Replace these with real callables (see “Wiring notes”).
Registers SESSIONS[session_id] and AGENT_LATEST[agent_id]
Adds participants row if PersonaAgent and conversation_id present
agent_destroy: requests stop; waits up to 5s for the task; updates state to "stopped"; removes from maps
agent_pause/agent_resume: call pause()/resume() if present; update state
agent_interrupt: puts guidance on the agent’s interrupt_queue; updates state with last_guidance
environment_reload: simple async handler in environment.py
Addressing agents:
Always prefer session_id to avoid ambiguity. AGENT_LATEST maps agent_id → latest session_id for convenience.
Queue helpers (queue_imp.py):
agent_create(agent_id, actor, initial_subject="foot", session_id=None) → sid
agent_destroy_action(agent_id, actor, reason, session_id)
stop_agent(session_id, reason) resolves agent_id and enqueues destroy
agent_interrupt_action(agent_id, session_id, actor="user", guidance={})
agent_pause_action / agent_resume_action
persona_agent_create(agent_id, actor, conversation_id, persona_config, session_id=None) → sid
Also includes AgentConfig management (unrelated to loop runtime, used to list available agents).

# WebSocket updates

store/agent_steps.append_agent_step emits run_update via ws_bus.emit_run_update for room run::agent_id::session_id with payload {run_id, last_text, timestamp}.
app.py initializes Socket.IO and sets up rooms and a subscribe_run handler. It sends an initial snapshot using store.sessions.get_last_step_for_session_id(session_id).


# Stores Summary

store.agent_state: upsert_agent_state and get_agent_state; records per-session rows keyed by agent_id + session_id; state updates on every tick.
store.agent_steps and store.steps_async: append per‑tick steps; list/query helpers; emits WS updates.
store.sessions:
list_sessions_for_agent(agent_id, active_only=False, ...) returns a distinct list of sessions based on agent_state or falls back to steps if needed.
get_agent_id_for_session_id(session_id) and get_last_step_for_session_id(session_id) utility functions.

# Best Practices

- Keep do_tick responsive. Use async IO; split long work into smaller ticks.
- Always include a small, useful state snapshot in StepOutcome.state on each tick.
- If you accept free‑form guidance, either provide a guidance_interpreter or parse "_raw_text" in apply_guidance. Consider turning off raw persistence if guidance may contain PII.
- If initial_context needs subclass fields, set those fields before calling super().init in your subclass constructor.
- If your agent should stop when finished, call self.request_stop() inside do_tick.
- For chatty agents, consider a shorter loop_interval and enforce cooldowns in your agent logic.

# Debugging Tips

## Ensure LanceDB schemas exist:
create_all_schemas() for agent_state, agent_steps, queue
create_conversation_schemas() for conversations/messages/participants
## Inspect steps and state:
store/agent_steps.list_agent_steps_latest(...)
store/agent_state.get_agent_state(...)
For UI updates, confirm ws_bus is initialized and append_step emits correctly.
## Action queue tuning:
poll_lancedb_for_actions currently sleeps 15s. Reduce to ~1–2s to improve interrupt latency.

# Minimal Test Checklist

## Initialize schemas: run create_all_schemas() and create_conversation_schemas().
## Start background agents: run app.py; it starts the Flask app and background agents (agents.main in a thread).
## REPL flow (using queue_imp):
cid = create_conversation("Demo")
sidA = persona_agent_create("arthur", "user", cid, {"name":"Arthur","tone":"bemused"})
sidF = persona_agent_create("ford", "user", cid, {"name":"Ford","tone":"cheeky"})
append_message(cid, "user", "user", "We’ve landed on an improbability trajectory. Thoughts?")
Expect replies from Arthur and Ford on subsequent heartbeats (once you wire state_updater/steps_appender correctly for PersonaAgent, see below).
Optionally send interrupts: agent_interrupt_action("arthur", sidA, {"type":"speak_now"}) (note current base loop won’t fast‑tick on speak_now; reply occurs on next heartbeat).
## Observability:
list_sessions_for_agent("arthur") shows session rows and context
Runs UI receives run_update events with last_text
# Wiring Notes and Important Caveats (current repo)

## PersonaAgent persistence wiring is incomplete in agent_create:
It passes state_updater=... and steps_appender=..., which are Python Ellipsis placeholders and will fail if used.
## To enable persistence, pass:
state_updater = functools.partial(upsert_state_async, agent_id=agent_id, session_id=session_id)
steps_appender = functools.partial(store.steps_async.append_step_async, agent_id, session_id=session_id)
## Pause behavior:
Current loop blocks on pause before checking interrupts. You must resume the agent to process queued guidance.
## Hybrid event/heartbeat scheduling:
Not implemented in the current LoopingAgentBase. There is no wait_for_interrupt or “race” between interrupt and heartbeat. The loop sleeps loop_interval between ticks. self._force_tick is set by PersonaAgent for speak_now but isn’t used by the loop.
## Action queue poll interval:
15s by default; decrease to 1–2s for faster control actions.

# API Reference (most relevant types and functions)

## agent_loop.LoopingAgentBase

init(agent_id, session_id, state_updater=None, steps_appender=None, loop_interval=3.0, guidance_interpreter=None, persist_guidance_raw=True, persist_guidance_normalized=True)
initial_context(self) -> dict | None
on_start(self) -> dict | None
on_stop(self) -> None
do_tick(self, step: int) -> StepOutcome [abstract]
apply_guidance(self, normalized_guidance) -> dict | None
interpret_guidance(self, raw) -> dict | None
should_continue_on_error(self, exc) -> bool
request_stop(), should_stop()
_paused_flag(), _context_snapshot()
run(self) [main loop]

## agent_loop.StepOutcome dataclass

status="ok", text=None, data=None, state=None, notes=None, latency_ms=None, error=None, guidance=None
## agent_core mixins

PauseMixin: pause(), resume(), is_paused(), wait_if_paused()
InterruptMixin: interrupt(guidance), check_interrupt()
StopMixin: request_stop(), should_stop() (LoopingAgentBase already inherits this)

## agent.py action handlers (async)

agent_create(db, async_tbl, action): creates JokeAgent or PersonaAgent; starts run() task
agent_destroy(db, async_tbl, action): requests stop; cancels on timeout; updates state to stopped
agent_pause/agent_resume(db, async_tbl, action)
agent_interrupt(db, async_tbl, action)
environment_reload_handler(db, async_tbl, action)
agents.py background runner

main(): connects to LanceDB and runs queue_watcher to poll and handle actions
queue_watcher(db, async_tbl): polls via poll_lancedb_for_actions and dispatches actions

# Persistence stores

## store.agent_state:
upsert_agent_state(agent_id, status, iteration=None, result=None, context=None, history=None, session_id=None)
get_agent_state(agent_id, session_id=None)
## store.agent_steps:
append_agent_step(agent_id, iteration, session_id=None, ..., text, data, state, guidance, notes, latency_ms, error)
list_agent_steps(...) and helpers list_agent_steps_since_iteration, list_agent_steps_latest
## store.steps_async:
append_step_async(agent_id, iteration, **fields) [thread‑offload wrapper]
## store.sessions:
list_sessions_for_agent(agent_id, active_only=False, ...)
get_agent_id_for_session_id(session_id) -> agent_id | None
get_last_step_for_session_id(session_id) -> last text | ""
## store.conversations:
create_conversation(title) -> conversation_id
set_conversation_status(conversation_id, status)
add_participant(conversation_id, agent_id, session_id, persona_config)
## store.messages:
append_message(conversation_id, author_id, role, text, reply_to=None, meta=None) -> message_id
list_messages_since(conversation_id, since_iso, limit=50) -> list[dict]
latest_message(conversation_id) -> dict | None
## store.schemas:
create_agent_state_schema, create_agent_steps_schema, create_queue_schema, create_conversation_schemas, create_all_schemas (no conversations), delete_* variants

# Known Gaps and TODOs (relative to earlier plans)

Hybrid event/heartbeat scheduling and “speak_now” fast ticks are not implemented in the base loop.
While paused, interrupts are not processed; consider reordering pause/interrupt checks or adding a “soft pause” mode.
PersonaAgent create handler must pass real state_updater and steps_appender callables for persistence.
Consider adding a persist_noop_steps toggle to reduce step volume for info/idle ticks.
Consider reducing the action queue poll interval to 1–2s for better responsiveness.
Optional: Append user message “pokes” (agent_interrupt speak_now) upon user message insertion to improve immediacy if you later add hybrid scheduling.

# Examples

## Minimal agent subclass

Define do_tick to produce one output per tick. Return StepOutcome with a small state snapshot.
Optionally, implement apply_guidance to respond to {"_raw_text": "..."} or structured fields.

### JokeAgent (as in this repo)

Maintains self.current_subject.
apply_guidance updates subject from structured or free‑form.
do_tick calls BAML tool and returns a joke; state includes subject and paused.

### PersonaAgent (as in this repo)

Binds to a conversation_id and persona_config (name, tone).
On each tick, reads new messages since last_seen; if last isn’t mine and cooldown passed, replies and appends to messages; persists a StepOutcome (when wired).
Guidance supports set_tone, set_cooldown; speak_now sets an unused self._force_tick flag in current base.

