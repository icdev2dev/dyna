# environment.py
import asyncio

async def environment_reload(action):
    print(f"Reloading environment {action['env_id']}")
    await asyncio.sleep(1)
    print(f"Environment {action['env_id']} reloaded.")
    