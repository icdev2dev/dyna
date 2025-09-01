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
        super().__init__(agent_id, session_id, loop_interval=loop_interval, **kwargs)

    def initial_context(self) -> Optional[dict]:
        return {
            "agent_type": "PersonaAgent",
            "conversation_id": self.conversation_id,
            "persona": self.persona_config.get("name") or self.agent_id,
        }


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


        if last.get("author_id") == self.agent_id:
            return StepOutcome(status="info", data={"intent": {"type": "silent", "reason": "seen_self"}}, state={"conversation_id": self.conversation_id})

        if not self._can_speak_now() and not self._force_tick:
            return StepOutcome(status="info", data={"intent": {"type": "silent", "reason": "cooldown"}}, state={"conversation_id": self.conversation_id})

        window = msgs[-10:]
        reply = await self._generate_reply(window)

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
    