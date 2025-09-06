from typing import Optional, Dict, Any, List

from agent_core import PauseMixin, InterruptMixin
from agent_loop import LoopingAgentBase, StepOutcome
from store.messages import list_messages_since
from datetime import datetime, timedelta


class PersonaAgent(PauseMixin, InterruptMixin, LoopingAgentBase):
    def __init__(
        self,
        agent_id: str,
        session_id: str,
        *,
        conversation_id: str,
        persona_config: dict,
        loop_interval: float = 1.5,
        cooldown_seconds: float = 2.0,
        **kwargs
    ):
        self.conversation_id = conversation_id
        self.persona_config = dict(persona_config or {})
        self.last_seen_iso: Optional[str] = None
        self.cooldown_seconds = cooldown_seconds
        self._last_spoke_at: Optional[datetime] = None
        self._force_tick = False
        
        self.participants: dict[str, dict] = {}
        self._participants_last_fetch = None
        self.participants_refresh_secs = 5.0  # tune as you like
        super().__init__(agent_id, session_id, loop_interval=loop_interval, **kwargs)




    def initial_context(self) -> Optional[dict]:
        return {
            "agent_type": "PersonaAgent",
            "conversation_id": self.conversation_id,
            "persona": self.persona_config.get("name") or self.agent_id,
        }


    async def _refresh_participants(self, force: bool = False) -> dict | None:
        from datetime import datetime, timedelta
        now = datetime.now()
        if (not force) and self._participants_last_fetch and (now - self._participants_last_fetch).total_seconds() < self.participants_refresh_secs:
            return None
        try:
            # Option 1:
            from store.conversations import list_participants
            plist = list_participants(self.conversation_id)
            # Option 2:
            # from store.conversations import get_conversation_messages_and_participants
            # plist = get_conversation_messages_and_participants(self.conversation_id)["participants"]

            # Normalize into a dict keyed by agent_id
            pmap = {}
            for p in plist:
                aid = p.get("agent_id")
                if not aid: 
                    continue
                cfg = p.get("persona_config") or {}
                name = cfg.get("name") or aid
                pmap[aid] = {
                    "agent_id": aid,
                    "session_id": p.get("session_id"),
                    "name": name,
                    "tone": cfg.get("tone"),
                    "joined_at": p.get("joined_at"),
                }
            self.participants = pmap
            self._participants_last_fetch = now

            # Merge a compact summary into context for observability
            summary = sorted([v["name"] for v in pmap.values()])
            return {"participants": summary, "participants_count": len(summary)}
        except Exception:
            return None

    async def on_start(self):
        ctx = await self._refresh_participants(force=True)
        return ctx or {}



    def _can_speak_now(self) -> bool:
        if self._last_spoke_at is None:
            return True
        return (datetime.now() - self._last_spoke_at) >= timedelta(seconds=self.cooldown_seconds)

    async def _generate_reply(self, window: List[dict]) -> str:
        # Minimal template; plug in your baml client/tool here
        persona = self.persona_config.get("name") or self.agent_id
        tone = self.persona_config.get("tone") or "default"
        last_user = next((m["text"] for m in reversed(window) if m["role"] == "user"), window[-1]["text"])
        return f"[{persona} | tone={tone}] {last_user}"

    async def do_tick(self, step: int) -> StepOutcome:
        
        await self._refresh_participants()

        msgs = list_messages_since(self.conversation_id, self.last_seen_iso, limit=50)

        if not msgs:
            return StepOutcome(status="info", text=None, state={"idle": True, "conversation_id": self.conversation_id})

        self.last_seen_iso = msgs[-1]["created_at"]
        last_msg_id = msgs[-1].get("message_id")


        try:
            # Merge into agent context so agent_state.context carries it
            self._merge_context({"last_seen_iso": self.last_seen_iso, "last_msg_id": last_msg_id})
        except Exception:
            pass

        last = msgs[-1]
        # Example: use awareness
        author_id = last.get("author_id")
        author_name = self.participants.get(author_id, {}).get("name", author_id)


        if last.get("author_id") == self.agent_id:
            return StepOutcome(status="info", data={"intent": {"type": "silent", "reason": "seen_self"}}, state={"conversation_id": self.conversation_id})

        if not self._can_speak_now() and not self._force_tick:
            return StepOutcome(status="info", data={"intent": {"type": "silent", "reason": "cooldown"}}, state={"conversation_id": self.conversation_id})

        window = msgs[-10:]
        reply = await self._generate_reply(window)
        reply = f"{reply}\n\n(p.s. I heard {author_name}; participants: {', '.join(sorted([v['name'] for v in self.participants.values()]))})"


        return StepOutcome(
            status="ok",
            data={"intent": {"type": "speak", "mode": "answer", "text": reply}},
            state={"conversation_id": self.conversation_id}
        )
    

    
    async def run(self):
    # Explicitly call the LoopingAgentBase run to avoid AgentBase.run
        return await LoopingAgentBase.run(self)
    
        # Optionally handle 'stop' guidance (kept optional)
    async def apply_guidance(self, g) -> Optional[dict]:
        if not isinstance(g, dict):
            return None
        t = (g.get("type") or "").strip()

        if t in ("rehydrate", "set_last_seen"):
            lsi = g.get("last_seen_iso") or g.get("last_seen")
            if lsi:
                self.last_seen_iso = str(lsi)
                return {"last_seen_iso": self.last_seen_iso}


        if t == "participants_changed": 
            ctx = await self._refresh_participants(force=True) 
            return ctx or {"participants_refreshed": True}

        if t == "set_tone":
            tone = str(g.get("tone") or "").strip()
            if tone:
                self.persona_config["tone"] = tone
                return {"tone": tone}

        if t == "speak_now":
            self._force_tick = True
            return {"force_tick": True}

        if t == "set_cooldown":
            try:
                self.cooldown_seconds = float(g.get("seconds", self.cooldown_seconds))
                return {"cooldown_seconds": self.cooldown_seconds}
            except Exception:
                pass

        # NEW: When a new_message arrives, wake the agent and bypass cooldown for this tick
        if t == "new_message":
            self._force_tick = True
            # optionally include a tiny breadcrumb for observability
            return {"force_tick": True, "last_new_message_id": g.get("message_id")}

        if t == "stop":
            self.request_stop()
            return {"stopping": True}

        return None
    