import asyncio
from agent import handle_actions, poll_lancedb_for_actions
import lancedb
from queue_imp import  AGENTS_URI, QUEUE_NAME

import pandas as pd
from store.schemas import MESSAGES_NAME, PARTICIPANTS_NAME, CONVERSATIONS_NAME
from queue_imp import agent_interrupt_action, persona_agent_create
from store.agent_state import get_agent_state
import json
from collections import deque






async def queue_watcher(db, async_tbl):
    while True:
        actions = await poll_lancedb_for_actions(db, async_tbl)
        _ = await handle_actions(db, async_tbl, actions=actions)

async def get_db_tbl(): 
    db = await lancedb.connect_async(AGENTS_URI)
    async_tbl = await db.open_table(QUEUE_NAME)
    return (db, async_tbl)







async def conversation_fanout(db, interval_s: float = 1.0):
    """
    Fan-out new conversation messages into agent_interrupt queue actions.
    Keeps in-memory cursor (last_ts) and a small dedupe set with bounded size.
    """
    last_ts: str | None = None
    processed_ids_set: set[str] = set()
    processed_order = deque(maxlen=5000)  # cap memory

    while True:
        try:
            mtbl = await db.open_table(MESSAGES_NAME)
            q = mtbl.query()
            if last_ts:
                q = q.where(f"created_at > '{last_ts}'")
            df = await q.to_pandas()

            if df is None or df.empty:
                await asyncio.sleep(interval_s)
                continue

            # Bootstrap: advance cursor to latest on first run
            if last_ts is None:
                try:
                    last_ts = df["created_at"].max()
                except Exception:
                    last_ts = str(df.iloc[-1]["created_at"])
                await asyncio.sleep(interval_s)
                continue

            try:
                df = df.sort_values("created_at", ascending=True)
            except Exception:
                pass

            for _, r in df.iterrows():
                mid = str(r.get("message_id"))
                if not mid:
                    continue

                # bounded dedupe
                if mid in processed_ids_set:
                    continue
                if len(processed_order) == processed_order.maxlen:
                    old = processed_order.popleft()
                    processed_ids_set.discard(old)
                processed_order.append(mid)
                processed_ids_set.add(mid)

                last_ts = str(r.get("created_at"))
                cid = str(r.get("conversation_id"))
                author_id = str(r.get("author_id") or "")
                role = str(r.get("role") or "")
                text = str(r.get("text") or "")

                # Load participants for the conversation
                ptbl = await db.open_table(PARTICIPANTS_NAME)
                pdf = await ptbl.query().where(f"conversation_id == '{cid}'").to_pandas()


                if pdf is None or pdf.empty:
                    continue

                seen_pairs = set()  # (agent_id, session_id)

                for _, pr in pdf.iterrows():
                    agent_id_p = str(pr.get("agent_id"))
                    session_id_p = str(pr.get("session_id"))
                    pair = (agent_id_p, session_id_p)
                    if pair in seen_pairs:
                        continue
                    seen_pairs.add(pair)

                    # Skip if the author is the same agent
                    if author_id and author_id == agent_id_p:
                        continue

                    guidance = {
                        "type": "new_message",
                        "message_id": mid,
                        "conversation_id": cid,
                        "author_id": author_id,
                        "role": role,
                        "text": text,
                        "created_at": last_ts,
                    }

                    await asyncio.to_thread(
                        agent_interrupt_action,
                        agent_id_p,
                        session_id_p,
                        "conversation",
                        guidance
                    )


            await asyncio.sleep(interval_s)
        except Exception as e:
            print(f"conversation_fanout error: {e}")
            await asyncio.sleep(interval_s)




async def rehydrate_active_personas(db, interval_s: float = 60.0):
    """
    Rehydrate PersonaAgents for active conversations based on participants table.
    For sessions not already live, enqueue create_agent; then enqueue a rehydrate interrupt
    carrying last_seen_iso if available from agent_state.context.
    """
    # Avoid re-enqueueing during our own lifetime
    rehydrated_sessions: set[str] = set()

    # Late import to avoid cycles
    from agent import SESSIONS

    while True:
        try:
            conv_tbl = await db.open_table(CONVERSATIONS_NAME)
            cdf = await conv_tbl.query().where("status == 'active'").to_pandas()

            if cdf is None or cdf.empty:
                await asyncio.sleep(interval_s)
                continue

            # For each active conversation, fetch participants
            part_tbl = await db.open_table(PARTICIPANTS_NAME)
            for _, c in cdf.iterrows():
                cid = str(c.get("conversation_id"))
                pdf = await part_tbl.query().where(f"conversation_id == '{cid}'").to_pandas()
                if pdf is None or pdf.empty:
                    continue

                for _, pr in pdf.iterrows():
                    agent_id = str(pr.get("agent_id"))
                    session_id = str(pr.get("session_id") or "")
                    if not session_id:
                        continue
                    if session_id in SESSIONS or session_id in rehydrated_sessions:
                        continue

                    # persona_config is JSON string in participants table; load it if present
                    persona_config_raw = pr.get("persona_config")
                    try:
                        if isinstance(persona_config_raw, (dict, list)):
                            persona_config = persona_config_raw
                        elif isinstance(persona_config_raw, str) and persona_config_raw.strip():
                            persona_config = json.loads(persona_config_raw)
                        else:
                            persona_config = {}
                    except Exception:
                        persona_config = {}

                    # Enqueue PersonaAgent creation preserving session_id
                    await asyncio.to_thread(
                        persona_agent_create,
                        agent_id,
                        "rehydrator",
                        cid,
                        persona_config,
                        session_id=session_id
                    )

                    # Fetch stored state to get last_seen_iso (if any) to avoid replay
                    try:
                        st = await asyncio.to_thread(get_agent_state, agent_id, session_id)
                        ctx = (st or {}).get("context") or {}
                        last_seen_iso = ctx.get("last_seen_iso")
                    except Exception:
                        last_seen_iso = None

                    guidance = {"type": "rehydrate"}
                    if last_seen_iso:
                        guidance["last_seen_iso"] = last_seen_iso

                    # Enqueue a rehydrate interrupt
                    await asyncio.to_thread(
                        agent_interrupt_action,
                        agent_id,
                        session_id,
                        "rehydrator",
                        guidance
                    )

                    rehydrated_sessions.add(session_id)

            await asyncio.sleep(interval_s)

        except Exception as e:
            print(f"rehydrate_active_personas error: {e}")
            await asyncio.sleep(interval_s)



async def main():
    (db, async_tbl) = await get_db_tbl()

    await asyncio.gather(
        queue_watcher(db, async_tbl),
        conversation_fanout(db),         # Phase 4
        rehydrate_active_personas(db),   # Phase 5
        # ...other background tasks
    )

if __name__ == "__main__":
    asyncio.run(main())
