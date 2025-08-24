import asyncio
from agent import handle_actions, poll_lancedb_for_actions
import lancedb
from queue_imp import  AGENTS_URI, QUEUE_NAME


async def queue_watcher(db, async_tbl):
    while True:
        actions = await poll_lancedb_for_actions(db, async_tbl)
        _ = await handle_actions(db, async_tbl, actions=actions)

async def get_db_tbl(): 
    db = await lancedb.connect_async(AGENTS_URI)
    async_tbl = await db.open_table(QUEUE_NAME)
    return (db, async_tbl)

async def main():
    (db, async_tbl) = await get_db_tbl()

    await asyncio.gather(
        queue_watcher(db, async_tbl),
        # ...other background tasks
    )

if __name__ == "__main__":
    asyncio.run(main())
