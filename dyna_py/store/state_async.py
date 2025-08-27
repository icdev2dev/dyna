import asyncio
from store.agent_state import upsert_agent_state as _upsert

async def upsert_state_async(agent_id, **fields):
    return await asyncio.to_thread(_upsert, agent_id, **fields)