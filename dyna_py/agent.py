
import asyncio
from environment import environment_reload
from queue_imp import mark_action_processed_async, QUEUE_NAME

from agent_core import AgentBase, InterruptMixin
from joke_agent import JokeAgent
import json

import json
from environment import environment_reload as _environment_reload

JOKE_AGENTS = {}  # agent_id -> JokeAgent


async def environment_reload_handler(db, async_tbl, action):
    action_id = action.get("action_id")
    try:
        await _environment_reload(action)
    finally:
        if action_id:
            await mark_action_processed_async(async_tbl, action_id)

# Agent action handlers


async def agent_create(db, async_tbl, action):
    print(f"Creating agent: {action.get('action_id')} ...")
    action_id = action.get("action_id")
    try:
        payload = json.loads(action.get("payload") or "{}")
        agent_id = payload.get("agent_id")
        initial_subject = payload.get("initial_subject", "foot")
        if not agent_id:
            print("create_agent missing agent_id in payload")
            return

        if agent_id not in JOKE_AGENTS:
            agent = JokeAgent(agent_id, initial_subject=initial_subject)
            JOKE_AGENTS[agent_id] = agent
            task = asyncio.create_task(agent.run())
            agent._task = task
            print(f"Agent {agent_id}: launching JokeAgent loop (subject={initial_subject})")
        else:
            print(f"Agent {agent_id} already exists; skipping.")
    finally:
        if action_id:
            await mark_action_processed_async(async_tbl, action_id)
            print(f"Marked action_id {action_id} as processed.")



async def agent_destroy(db, async_tbl, action):
    action_id = action.get("action_id")
    try:
        payload = json.loads(action.get("payload") or "{}")
        agent_id = payload.get("agent_id") or action.get("agent_id")
        if not agent_id:
            print("agent_destroy missing agent_id")
            return

        agent = JOKE_AGENTS.get(agent_id)
        if not agent:
            print(f"Agent {agent_id} not found.")
            return

        # If paused, wake it so it can exit
        if hasattr(agent, "resume"):
            agent.resume()
        # Request cooperative stop
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

        # Cleanup registry
        JOKE_AGENTS.pop(agent_id, None)
        print(f"Agent {agent_id} destroyed.")
    finally:
        if action_id:
            await mark_action_processed_async(async_tbl, action_id)

async def agent_pause(db, async_tbl, action):
    action_id = action.get("action_id")
    try:
        payload = json.loads(action.get("payload") or "{}")
        agent_id = payload.get("agent_id") or action.get("agent_id")
        if not agent_id:
            print("agent_pause missing agent_id")
            return
        agent = JOKE_AGENTS.get(agent_id)
        if agent:
            agent.pause()
            print(f"Paused agent {agent_id}")
        else:
            print(f"Agent {agent_id} not found")
    finally:
        if action_id:
            await mark_action_processed_async(async_tbl, action_id)

async def agent_resume(db, async_tbl, action):
    action_id = action.get("action_id")
    try:
        payload = json.loads(action.get("payload") or "{}")
        agent_id = payload.get("agent_id") or action.get("agent_id")
        if not agent_id:
            print("agent_resume missing agent_id")
            return
        agent = JOKE_AGENTS.get(agent_id)
        if agent:
            agent.resume()
            print(f"Resumed agent {agent_id}")
        else:
            print(f"Agent {agent_id} not found")
    finally:
        if action_id:
            await mark_action_processed_async(async_tbl, action_id)


async def agent_interrupt(db, async_tbl, action):
    # payload is expected to be a JSON string with agent_id and guidance
    payload_raw = action.get("payload")
    try:
        payload = json.loads(payload_raw)
    except Exception:
        print(f"Malformed payload: {payload_raw}")
        return
    
    agent_id = payload["agent_id"]
    guidance = payload.get("guidance")
    agent = JOKE_AGENTS.get(agent_id)
    if agent is not None:
        await agent.interrupt(guidance)
        print(f"Sent guidance to agent {agent_id}: {guidance}")
    else:
        print(f"Agent {agent_id} not found.")

    # Mark as processed if action_id is present
    action_id = action.get("action_id")
    if action_id:
        await mark_action_processed_async(async_tbl, action_id)




# Action dispatcher mapping
ACTION_HANDLERS = {
    'create_agent': agent_create,
    'agent_destroy': agent_destroy,
    'agent_pause': agent_pause,
    'agent_resume': agent_resume,
    'agent_interrupt': agent_interrupt,
    'environment_reload': environment_reload_handler,
    # Add more
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

        async def run_one():
            try:
                await handler(db, async_tbl, action)
            finally:
                IN_FLIGHT_ACTION_IDS.discard(aid)
        asyncio.create_task(run_one())







async def poll_lancedb_for_actions(db, async_tbl):
    

    await asyncio.sleep(5)
    cnt = poll_lancedb_for_actions.counter
    poll_lancedb_for_actions.counter += 1
    if cnt % 3 == 0:
        print("c")
        async_tbl = await db.open_table(QUEUE_NAME)

        result = await async_tbl.query().where("processed == False").to_pandas()
        return result.to_dict(orient="records")  
    return []

poll_lancedb_for_actions.counter = 0



class InterruptibleAgent(InterruptMixin, AgentBase):
    async def run(self):
        step = 0
        print(f"Agent {self.agent_id} started!")
        while step < 10:
            await self.wait_if_paused()
            guidance = await self.check_interrupt()
            if guidance is not None:
                print(f"Agent {self.agent_id} got guidance: {guidance}")
                # Change behavior as needed
            print(f"Agent {self.agent_id} working: {step}")
            await asyncio.sleep(1)
            step += 1
        print(f"Agent {self.agent_id} finished!")


            
