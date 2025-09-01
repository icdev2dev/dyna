
# Current system snapshot
## Architecture

### Queue-driven async agents using LanceDB:

Actions are appended to a LanceDB “queue” table (payload/metadata as JSON strings).
agents.py runs an async poller/dispatcher that pulls unprocessed actions and invokes async handlers in agent.py.
Agents are cooperative via mixins: PauseMixin, InterruptMixin, StopMixin.
Each action is marked processed; IN_FLIGHT_ACTION_IDS prevents double-dispatch while a handler is running.
Agent runtime and registry

JokeAgent runs in an asyncio.Task; loop checks stop/pause, consumes interrupts, and calls tell_a_joke(subject).
JOKE_AGENTS maps agent_id -> instance for lifecycle control (create, pause, resume, interrupt, destroy).
Graceful destroy: if paused, resume, then request_stop, await with timeout, cancel if needed, remove from registry.
State persistence plumbing

store/agent_state.py provides upsert/get/list; we agreed to use update-then-append (not overwrite).
An async wrapper runs sync storage in threads (asyncio.to_thread).
We introduced agent_steps (append-only) to record per-iteration history and added list endpoints (details below).


### Two entry points

agents.py: long-running async service that polls the queue and dispatches actions.
app.py: Flask + Socket.IO app. For real WebSockets, run with socketio.run(app, …), not app.run().
Core components and flow

queue_imp.py (or equivalent store/action_queue):
LanceDB connection + schemas; enqueue helpers: agent_create, agent_pause_action, agent_resume_action, agent_interrupt, agent_destroy_action; mark_action_processed_async.
agent_core.py:
AgentBase, InterruptMixin (asyncio.Queue), PauseMixin (asyncio.Event), StopMixin (asyncio.Event).
All mixins call super().init to ensure proper initialization.
agent.py:
Handlers have signature (db, async_tbl, action).
Handlers mark actions processed in finally to avoid stuck actions.
Dispatcher spawns a task per action; closure variables must be bound (run_one(aid=aid, action=action, handler=handler)) to avoid late-binding bugs.
joke_agent.py:
Loop respects pause/stop, consumes interrupt guidance (updates current_subject), prints joke, sleeps ~3s.
Calls async state_updater and steps_appender (closures injected at create) to persist.

## Assessments and fixes

### Lifecycle and robustness

Cooperative pause/resume/stop are in place.
agent_destroy was fixed and now persists status (stopping -> stopped) without crashing.

### State handling

upsert_agent_state must be update-then-append; do not use add(mode="overwrite").
get_agent_state should safely parse JSON fields; if result is plain text (not JSON), return as-is (avoid JSONDecodeError).
Async wrappers use asyncio.to_thread to keep event loop responsive.

### Dispatcher and handlers

Agent interrupt must always mark the action processed even on bad payloads (use try/finally).
Bind loop variables in run_one to avoid late-binding hazards and catch/print exceptions (prevents “Task exception was never retrieved” noise).


### Poller and ordering

Current cadence is slow (effectively ~15s). Improve by reducing sleep and ordering by created_at (and optionally urgency).
WebSockets

Use socketio.run(app, …) for proper WS. Consider emitting per-step events to clients.

### LanceDB semantics

append adds rows; overwrite replaces the entire table. For agent_state, use update-then-append; for agent_steps and queue, use append; use update to mark queue processed.

## Moniker model and runner pattern

### Why “moniker”

Encapsulates the task-specific step function (tell_a_joke, summarize, research) with a stable I/O contract; the runner (agent) handles orchestration.

#### StepFrame-v0 contract (MVP)

Input to moniker: { step, state, guidance? }
Output from moniker: { step, next_step, state, text?, data?, done, notes? }
We decided:
Keep both step and iteration. They serve different purposes.
step/next_step are strings (tokens) to support hierarchical/named cursors (e.g., “4.2”, “review/1”).
iteration is the runner’s monotonically increasing int for ordering/pagination/ops and is not part of the moniker contract.
#### Runner loop

Maintain step_token: str and iteration: int.
Each loop: build frame_in with step_token/state/guidance_once -> call moniker -> parse frame_out.
Persist:
agent_state snapshot: status, iteration, step_token, next_step_token, result, context.
agent_steps history: append iteration, step_token, next_step_token, text, data, state, guidance, notes, status.
If out.done and stop_on_done=true: exit; else continue with step_token = out.next_step; iteration += 1.
Add safeguards: max_steps and/or max_runtime_s.

#### BAML function

We generalized the “joke” moniker to a generic RunMonikerStep(frame, task) returning the StepFrame JSON.

# 4. Sessions (run/correlation id)

## Decisions

Introduce session_id across queue → runtime → agent_state → agent_steps. Prefer client-supplied session_id for idempotency and immediate correlation; server-generated is fine if returned right away.
Registries:
SESSIONS[session_id] -> agent instance.
AGENT_LATEST[agent_id] -> latest session_id for backward-compatible controls by agent_id.
Control actions accept session_id; if only agent_id is provided, resolve via AGENT_LATEST.

## Data model implications

queue: add session_id; carry through all actions.
agent_state: add session_id (nullable initially); upsert keyed by (agent_id, session_id) when session_id present; otherwise legacy by agent_id.
agent_steps: include session_id on every row (append-only).
HTTP/UI: filter by session_id and/or agent_id; stream by session_id room/topic.
## Rehydration

On restart, read agent_state rows with status in {running, paused}, recreate agents with saved state/session_id, resume with step_token=next_step_token and iteration+1.

# 5. Agent steps (append-only history)

## Schema (in LanceDB)

id, created_at, agent_id, session_id (nullable at first), iteration (int), step_token (str), next_step_token (str), status, text, data (JSON string), state (JSON string), guidance (JSON string), notes, latency_ms, error.
Store helpers and endpoints

append_agent_step(...) (sync) + append_step_async wrapper.
list_agent_steps filters: session_id/agent_id/min/max iteration/since_created_at/status, ordering by iteration asc, limit/offset; JSON decoding of fields.
list_agent_steps_since_iteration(session_id, after_iteration).
list_agent_steps_latest(session_id|agent_id).
HTTP example: GET /api/agent-steps?session_id=... or ?agent_id=....
Sessions listing per agent

list_sessions_for_agent(agent_id): returns distinct sessions with latest snapshot if agent_state has session_id; else falls back to agent_steps grouping.
HTTP example: GET /api/agents/<agent_id>/sessions.
# 6. Conversations as a first-class component

## Rationale

Multiple agents (each with multiple sessions) and users participate in a shared thread. Agents deposit interim/final outputs to a conversation; users post messages that can guide agents.
## Data model

conversations: conversation_id, title, created_by, status, tags, created_at.
conversation_participants: link conversation_id to user_id or (agent_id, session_id), with roles and join/leave times.
conversation_messages (append-only): message_id, conversation_id, created_at, sender_type, user_id/agent_id/session_id, text, data, status, event_type, iteration, step_token, next_step_token, notes.
Optional session_cursors for agents that pull messages.
Agent participation

On create_agent, accept conversation_id; register the session as a participant and bind conversation_id to state_updater/steps_appender closures.
On each loop, in addition to agent_state/agent_steps, append a conversation_message with sender_type="agent".
On user POST to conversation, append message and enqueue agent_interrupt/agent_input actions targeting participant sessions (push model); or support pull via cursors.
HTTP endpoints (minimal)

POST /api/conversations (create), GET /api/conversations (list).
POST /api/conversations/{id}/participants, GET /api/conversations/{id}/participants.
POST /api/conversations/{id}/messages (user posts), GET /api/conversations/{id}/messages (list transcript).
# 7. Notable implementation decisions and patterns

Persist JSON fields as strings in LanceDB columns; parse defensively (safe_json_loads).
Use update-then-append for upserts; never overwrite an entire table unintentionally.
Always mark queue actions processed in finally to avoid stuck rows.
Use asyncio.to_thread for sync LanceDB operations from async handlers.
Prefer ULID or created_at ordering for human timelines; iteration for precise session-local ordering.
Emit Socket.IO events keyed by session_id and/or conversation_id for real-time UI.
On error in handlers, persist last_error/status="error" in agent_state and append an error event to agent_steps.

# 8. Roadmap and verification plan

## Step 1: Introduce agent_steps (done/in progress)

Create table and append per iteration.
Add list_agent_steps HTTP endpoint; test pagination and ordering.
No change to agent_state yet.

## Step 2: Introduce session_id end-to-end

Extend queue payloads and schema to carry session_id (accept client-supplied UUID).
Extend agent_state with session_id; switch upsert to (agent_id, session_id) when present.
Modify agent_create to accept/generate session_id; store in instance; bind into state_updater/steps_appender closures.
Add SESSIONS and AGENT_LATEST registries; modify control handlers to accept session_id (resolve if only agent_id is provided).
Verify: GET /api/agents/<agent_id>/sessions shows distinct sessions; GET /api/agent-steps?session_id=... returns timeline.

## Step 3: Switch moniker to StepFrame-v0

Update BAML to RunMonikerStep(frame, task) returning JSON with step/next_step text tokens and state.
Update runner loop to use step_token/next_step_token; persist into agent_state and agent_steps.
Add stop_on_done option per agent/moniker and max_steps guard.
Verify: outputs still flow; step tokens appear; iteration monotonic; done semantics work.

## Step 4: Conversations

Add conversations, participants, messages tables + HTTP endpoints.
Update agent_create to accept conversation_id and register participant.
On each agent loop, also append conversation_message with agent output.
Implement user POST to conversation -> enqueue agent_input/interrupt to participant sessions.
Verify: messages appear in transcript; agents react to user posts through queue.

## Step 5: Rehydration and ops

On startup, rehydrate running/paused sessions from agent_state; resume with step_token=next_step_token and iteration+1.
Improve poller responsiveness and ordering (created_at asc, urgency).
Replace app.run with socketio.run; emit session/conversation events for UI.
Error handling: capture exceptions in handlers and persist status="error", last_error; retry policies where appropriate.
Table bootstrap: ensure schemas are created lazily or on startup.

# 9. Open items and options

Choose UUID vs ULID for ids (ULID helps natural ordering).
Decide default stop_on_done per moniker (continuous vs finite workflows).
Decide when to make session_id required in agent_state and agent_steps (initially nullable for migration).
Optionally add agent_config table for per-agent/moniker parameters.
Consider agent_steps event_seq if you plan partial/streamed events within the same iteration.