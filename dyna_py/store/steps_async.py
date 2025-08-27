import asyncio
from .agent_steps import append_agent_step as _append

async def append_step_async(agent_id: str, iteration: int, **fields):
    return await asyncio.to_thread(_append, agent_id, iteration, **fields)
