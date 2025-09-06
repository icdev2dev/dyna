
import asyncio
import json
from datetime import datetime, timezone

from queue_imp import mark_action_processed_async, QUEUE_NAME

from agent_core import AgentBase, InterruptMixin
from joke_agent import JokeAgent

from store.agent_state import upsert_agent_state, get_agent_state
from environment import environment_reload as _environment_reload
from persona_agent import PersonaAgent
from store.conversations import add_participant_if_absent

JOKE_AGENTS = {}  # agent_id -> JokeAgent
SESSIONS = {}              # session_id -> instance
AGENT_LATEST = {}          # agent_id -> latest session_id


async def upsert_state_async(agent_id, status=None, iteration=None, result=None, context=None, history=None,  session_id=None):
    def do_upsert():
        try:
            prev = get_agent_state(agent_id, session_id=session_id)
                        
        except Exception as e:
            print(f"get_agent_state failed for {agent_id}/{session_id}: {e}")
            prev = {}

        eff_status = status or (prev.get("status") if prev else "running")
        upsert_agent_state(
            agent_id=agent_id,
            session_id=session_id,
            status=eff_status,
            iteration=iteration,
            result=result,
            context=context,
            history=history,
        )
    await asyncio.to_thread(do_upsert)



def _resolve_agent(agent_id=None, session_id=None):
# Prefer session_id if supplied
    if session_id and session_id in SESSIONS:
        return session_id, SESSIONS.get(session_id)
    # Fallback: latest session for agent_id (only if not stale)
    if agent_id and agent_id in AGENT_LATEST:
        sid = AGENT_LATEST[agent_id]
        agent = SESSIONS.get(sid)
        if agent:
            return sid, agent
    # stale mapping; fall through to legacy
    # Legacy: single-agent map
    if agent_id and agent_id in JOKE_AGENTS:
        return None, JOKE_AGENTS.get(agent_id)
    return None, None


async def environment_reload_handler(db, async_tbl, action):
    action_id = action.get("action_id")
    try:
        from environment import environment_reload as _environment_reload
        await _environment_reload(action)
    finally:
        if action_id:
            await mark_action_processed_async(async_tbl, action_id)

# Agent action handlers

async def agent_create(db, async_tbl, action):
    import functools, uuid

    print(f"Creating agent: {action.get('action_id')} ...")
    action_id = action.get("action_id")
    try:
        payload = json.loads(action.get("payload") or "{}")

        agent_id = payload.get("agent_id")
        agent_type = payload.get("agent_type") or "JokeAgent"
        conversation_id = payload.get("conversation_id")
        persona_config = payload.get("persona_config") or {}
        initial_subject = payload.get("initial_subject", "foot")
        
        session_id = payload.get("session_id") or action.get("session_id") or str(uuid.uuid4())

        if not agent_id:
            print("create_agent missing agent_id in payload")
            return

        if session_id in SESSIONS:
            print(f"Session {session_id} already exists; skipping.")
            return

        if agent_type == "PersonaAgent":
            agent = PersonaAgent(
                agent_id,
                session_id,
                state_updater=functools.partial(upsert_state_async, session_id=session_id),
                steps_appender=functools.partial(
                    __import__("store.steps_async", fromlist=["append_step_async"]).append_step_async,
                    agent_id,
                    session_id=session_id
                ),
                conversation_id=conversation_id,
                persona_config=persona_config,
                loop_interval=payload.get("loop_interval", 1.5),
            )
        else:
            agent = JokeAgent(
                agent_id,
                session_id,
                state_updater=functools.partial(upsert_state_async, session_id=session_id),
                steps_appender=functools.partial(
                    __import__("store.steps_async", fromlist=["append_step_async"]).append_step_async,
                    agent_id,
                    session_id=session_id
                ),
                initial_subject=initial_subject,
            )


        # Register
        SESSIONS[session_id] = agent
        AGENT_LATEST[agent_id] = session_id
        JOKE_AGENTS[agent_id] = agent  # legacy compatibility

        try:
            if agent_type == "PersonaAgent" and conversation_id:
                add_participant_if_absent(conversation_id, agent_id, session_id, persona_config)


                from store.conversations import get_conversation_messages_and_participants
                from queue_imp import agent_interrupt_action

                if agent_type == "PersonaAgent" and conversation_id:
                    snap = get_conversation_messages_and_participants(conversation_id)
                    parts = snap.get("participants", [])
                    for p in parts:
                        aid = p.get("agent_id")
                        sid = p.get("session_id")
                        if not aid or not sid or aid == agent_id:
                            continue
                        agent_interrupt_action(aid, sid, "system", {"type": "participants_changed"})

                
        except Exception as e:
            print(f"add_participant failed: {e}")

        task = asyncio.create_task(agent.run())

        def _log_task_result(t):
            import traceback, asyncio
            try:
                t.result()
                print(f"Agent {agent.agent_id}/{session_id} task completed.")
            except asyncio.CancelledError:
                print(f"Agent {agent.agent_id}/{session_id} task cancelled.")
            except Exception as e:
                print(f"Agent {agent.agent_id}/{session_id} task failed: {e!r}")
                traceback.print_exception(type(e), e, e.__traceback__)

        task.add_done_callback(_log_task_result)
        agent._task = task

        atype = "PersonaAgent" if agent_type == "PersonaAgent" else "JokeAgent"
        print(f"Agent {agent_id}/{session_id}: launching {atype} loop"
        + (f" (conversation={conversation_id})" if agent_type == "PersonaAgent" else f" (subject={initial_subject})"))

    finally:
        if action_id:
            await mark_action_processed_async(async_tbl, action_id)
            print(f"Marked action_id {action_id} as processed.")


async def agent_destroy(db, async_tbl, action):
    action_id = action.get("action_id")
    try:
        payload = json.loads(action.get("payload") or "{}")
        agent_id = payload.get("agent_id") or action.get("agent_id")
        session_id = payload.get("session_id") or action.get("session_id")
        sid, agent = _resolve_agent(agent_id=agent_id, session_id=session_id)
        if not agent:
            print(f"Agent not found for agent_id={agent_id}, session_id={session_id}")
            await upsert_state_async(agent_id, status="stopped", context={"ended_at": datetime.now(timezone.utc).isoformat()}, session_id=sid or session_id)
            return

        await upsert_state_async(agent.agent_id, status="stopping", session_id=sid or session_id)

        if hasattr(agent, "resume"):
            agent.resume()
        if hasattr(agent, "request_stop"):
            agent.request_stop()
        task = getattr(agent, "_task", None)
        if isinstance(task, asyncio.Task):
            try:
                await asyncio.wait_for(task, timeout=5.0)
            except asyncio.TimeoutError:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        
        # Cleanup
        if sid:
            SESSIONS.pop(sid, None)
        if agent_id and AGENT_LATEST.get(agent_id) == sid:
            AGENT_LATEST.pop(agent_id, None)
        if agent_id:
            JOKE_AGENTS.pop(agent_id, None)

        await upsert_state_async(agent.agent_id, status="stopped", context={"ended_at": datetime.now(timezone.utc).isoformat()}, session_id=sid or session_id)
        print(f"Agent {agent.agent_id}/{sid or session_id} destroyed.")
    finally:
        if action_id:
            await mark_action_processed_async(async_tbl, action_id)


async def agent_pause(db, async_tbl, action):
    action_id = action.get("action_id")
    try:
        payload = json.loads(action.get("payload") or "{}")
        agent_id = payload.get("agent_id") or action.get("agent_id")
        session_id = payload.get("session_id") or action.get("session_id")
        sid, agent = _resolve_agent(agent_id=agent_id, session_id=session_id)
        if agent:
            agent.pause()
            await upsert_state_async(agent.agent_id, status="paused", context={"paused": True}, session_id=sid or session_id)
            print(f"Paused agent {agent.agent_id}/{sid or session_id}")
        else:
            print(f"Agent not found for agent_id={agent_id}, session_id={session_id}")
    finally:
        if action_id:
            await mark_action_processed_async(async_tbl, action_id)


async def agent_resume(db, async_tbl, action):
    action_id = action.get("action_id")
    try:
        payload = json.loads(action.get("payload") or "{}")
        agent_id = payload.get("agent_id") or action.get("agent_id")
        session_id = payload.get("session_id") or action.get("session_id")
        sid, agent = _resolve_agent(agent_id=agent_id, session_id=session_id)
        if agent:
            agent.resume()
            await upsert_state_async(agent.agent_id, status="running", context={"paused": False}, session_id=sid or session_id)
            print(f"Resumed agent {agent.agent_id}/{sid or session_id}")
        else:
            print(f"Agent not found for agent_id={agent_id}, session_id={session_id}")
    finally:
        if action_id:
            await mark_action_processed_async(async_tbl, action_id)


async def agent_interrupt(db, async_tbl, action):
    print("IN INITER")
    action_id = action.get("action_id")
    payload_raw = action.get("payload") or ""
    try:
        payload = json.loads(payload_raw)
        agent_id = payload.get("agent_id") or action.get("agent_id")
        session_id = payload.get("session_id") or action.get("session_id")
        guidance = payload.get("guidance")
        print(agent_id, session_id, guidance)
        sid, agent = _resolve_agent(agent_id=agent_id, session_id=session_id)
        if agent is not None:
            await agent.interrupt(guidance)
            await upsert_state_async(agent.agent_id, status="running", context={"last_guidance": guidance}, session_id=sid or session_id)
            print(f"Sent guidance to agent {agent.agent_id}/{sid or session_id}: {guidance}")
        else:
            print(f"Agent not found for agent_id={agent_id}, session_id={session_id}")
    except Exception as e:
        print(f"agent_interrupt payload error: {e}; raw={payload_raw!r}")
    finally:
        if action_id:
            await mark_action_processed_async(async_tbl, action_id)



ACTION_HANDLERS = {
'create_agent': agent_create,
'agent_destroy': agent_destroy,
'agent_pause': agent_pause,
'agent_resume': agent_resume,
'agent_interrupt': agent_interrupt,
'environment_reload': environment_reload_handler,
}

IN_FLIGHT_ACTION_IDS = set()

async def handle_actions(db, async_tbl, actions):
    for action in actions:
        aid = action.get("action_id")
        if not aid:
            print(f"Skipping action without action_id: {action}")
            continue
        if aid in IN_FLIGHT_ACTION_IDS:
            continue
        handler = ACTION_HANDLERS.get(action["type"])
        if not handler:
            print(f"Unknown action type: {action}")
            continue
        IN_FLIGHT_ACTION_IDS.add(aid)

        async def run_one(aid=aid, action=action, handler=handler):
            try:
                await handler(db, async_tbl, action)
            except Exception as e:
                import traceback
                print(f"Action {aid} raised: {e}")
                traceback.print_exc()
            finally:
                IN_FLIGHT_ACTION_IDS.discard(aid)
        asyncio.create_task(run_one())



async def poll_lancedb_for_actions(db, async_tbl):
    await asyncio.sleep(15)
    print("c")
    async_tbl = await db.open_table(QUEUE_NAME)

    result = await async_tbl.query().where("processed == False").to_pandas()
    return result.to_dict(orient="records")
    

