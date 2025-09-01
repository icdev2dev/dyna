
# What we have built

## Architecture: Async agents driven by a LanceDB-backed action queue.
- Actions are written to table "queue" (JSON payload/metadata stored as strings).
- agents.py runs a queue watcher that polls unprocessed actions and dispatches to async handlers in agent.py.
- Agents are cooperative: they support pause, resume, interrupts (new guidance), and graceful stop.
- Each action is marked processed after handling to avoid reprocessing.
## Two entry points:
- app.py: Flask + Socket.IO server (note: for real WebSocket support, run with socketio.run(app, ...) instead of app.run()).
- agents.py: long-running async process that polls the queue and dispatches actions to create/control agents.

# Core components and flow

## queue_imp.py

- Defines LanceDB connection, schemas for agents_config and queue.
- Helpers to enqueue actions:
- agent_create(agent_id, actor, initial_subject)
- agent_pause_action(agent_id, actor, reason)
- agent_resume_action(agent_id, actor)
- agent_interrupt(agent_id, actor, guidance)
- agent_destroy_action(agent_id, actor, reason)
- mark_action_processed_async(async_tbl, action_id): sets processed=True.

## agents.py

Connects to LanceDB asynchronously, opens the queue table.
queue_watcher loops and calls poll_lancedb_for_actions, then handle_actions.
handle_actions dispatches via ACTION_HANDLERS and tracks IN_FLIGHT_ACTION_IDS to prevent double-dispatch while a handler is still running.

## agent.py

- Action handlers (all with signature (db, async_tbl, action)):
- create_agent: creates a JokeAgent if not present, launches its run loop, stores task handle on agent, marks action processed.
- agent_pause: pauses the agent and marks processed.
- agent_resume: resumes the agent and marks processed.
- agent_interrupt: pushes guidance onto the agent’s interrupt queue and marks processed.
- agent_destroy: cooperative stop; resumes if paused, requests stop, awaits task with timeout, cancels if needed, removes from registry, marks processed.
- environment_reload: calls environment.reload and marks processed.
- JOKE_AGENTS is the in-memory registry (agent_id -> agent).

## agent_core.py (mixins)

- AgentBase: stores agent_id; must call super().init.
- InterruptMixin: asyncio.Queue for cooperative interrupts (interrupt/check_interrupt).
- PauseMixin: asyncio.Event for pause/resume (pause/resume/wait_if_paused/is_paused).
- StopMixin: asyncio.Event for cooperative stop (request_stop/should_stop).
- Important: every class in this MRO calls super().init(*args, **kwargs) so all mixin initializers run. We fixed AttributeError by ensuring super().init everywhere.

## joke_agent.py

- JokeAgent inherits StopMixin, PauseMixin, InterruptMixin, AgentBase.
- Loop:
If should_stop: break.
await wait_if_paused.
If should_stop: break.
check_interrupt; if dict with "subject", update current_subject.
await tell_a_joke(current_subject) via baml; print.
await asyncio.sleep(3).
Stores _task (the asyncio Task running run()) for clean shutdown.

## Step 1 achieved (and steady)

queue_imp.agent_create writes a create_agent action.
agents.py watcher picks it up, agent_create launches JokeAgent.
agent_interrupt writes an interrupt action; JokeAgent consumes guidance and changes subject on next cycle.
Actions are marked processed so they don’t re-run.

## Fixes and improvements we implemented

- Cooperative pausing/resuming with PauseMixin and checks in run loop.
- Cooperative stopping with StopMixin; agent_destroy handler uses it and cleans up the task.
- Correct super().init across the MRO to initialize mixins (fixes _pause_event error).
- In-flight action tracking to avoid duplicate dispatches while a handler is running.
- Standardized handler signatures to (db, async_tbl, action), and each marks action in a finally block.
- Persisting agent state (for UI/observability)

## We already have store/agent_state.py with:
upsert_agent_state(agent_id, status, iteration, result, context, history)
get_agent_state(agent_id)
list_agent_states()
## Change recommended: upsert_agent_state should not use tbl.add(..., mode="overwrite").
Replace with update-then-append semantics:
Try tbl.update(where=f"agent_id == '{agent_id}'", updates=updates).
If count == 0, tbl.add([{"agent_id": agent_id, ...}], mode="append").
How we wire runtime to persist state:
In agent_create, pass a state_updater (async closure) into the agent, and write an initial state row (status="running", iteration=0, subject, paused=False).
In JokeAgent.run:
After each step, call state_updater with status="running", iteration=step, result=last joke, current_subject.
On interrupt, update pending guidance/subject.
On stop, update status="stopped" and ended time.
In pause/resume/interrupt/destroy handlers, upsert current status flags for the agent (paused running/stopped etc.).
Because store functions are sync, call them via asyncio.to_thread in an upsert_state_async wrapper to keep the event loop responsive.


# How to test the lifecycle end-to-end

Start the queue watcher:

python -m agents (or however you run agents.py)
Create an agent:

from queue_imp import agent_create
agent_create("agent1", "user", initial_subject="cats")
Watch: JokeAgent starts printing jokes about cats.
Send an interrupt:

from queue_imp import agent_interrupt
agent_interrupt("agent1", "user", {"subject": "dogs"})
Watch: logs say it switched subject; subsequent jokes are about dogs.
Pause/resume:

from queue_imp import agent_pause_action, agent_resume_action
agent_pause_action("agent1", "user", "demo pause")
agent_resume_action("agent1", "user")
Watch: output stalls during pause, resumes after.
Destroy:

from queue_imp import agent_destroy_action
agent_destroy_action("agent1", "user", reason="demo")
Watch: cooperative stop and cleanup; no further logs.
Inspect state (for UI):

from store.agent_state import list_agent_states
print(list_agent_states())
You should see one row per agent_id with updated status/iteration/result/context.

# Notes and gotchas

WebSockets in app.py: use socketio.run(app, ...) instead of app.run(...) if you rely on Socket.IO handlers.
Poll cadence: poll_lancedb_for_actions has a 5s sleep and only fetches every 3rd call (effectively ~15s). Tweak for responsiveness.
Always mark actions processed in a finally block to prevent stuck actions.
Make sure the LanceDB tables exist (schemas.create_* helpers or lazy-create on startup).
payload and metadata fields are JSON strings in pa.string() columns (serialize with json.dumps, parse with json.loads).


# What’s ready now

Queue-driven agent creation, interrupt, pause/resume, destroy.
Cooperative lifecycle (no abrupt cancels unless destroy timeout triggers).
State persistence hooks (once upsert_agent_state is switched to update-then-append and wired as described).

# Recommended next steps

Finalize upsert_agent_state patch (remove mode="overwrite").
Add an HTTP endpoint to list agent states for the web UI (wrap store.agent_state.list_agent_states()).
Add optional agent_steps history table for step-level observability and timelines.
On process restart, rehydrate: read agent_state rows for status="running"/"paused" and recreate agents with saved operational state.
Prioritization: respect action.urgency and created_at ordering in poller/dispatcher.
Retries and error handling: capture exceptions in handlers and write status="error" with last_error.

# Quick reference of handler contract and payloads

create_agent: payload {"agent_id": str, "initial_subject": str?}
agent_pause: payload {"agent_id": str, "reason": str?}
agent_resume: payload {"agent_id": str}
agent_interrupt: payload {"agent_id": str, "guidance": dict}
agent_destroy: payload {"agent_id": str, "reason": str?}
environment_reload: payload depends on action; current handler just forwards action.
If you want, I can provide a small patch set next session:

The upsert_agent_state update-then-insert change.
An async wrapper and agent injection of state_updater.
A /api/agents endpoint to return list_agent_states() for your UI.
