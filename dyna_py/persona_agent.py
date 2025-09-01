from typing import Optional, Dict, Any, List

from agent_core import PauseMixin, InterruptMixin
from agent_loop import LoopingAgentBase, StepOutcome
from store.messages import list_messages_since, append_message
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

    async def apply_guidance(self, g) -> Optional[dict]:
        if not isinstance(g, dict):
            return None
        t = g.get("type")
        if t == "set_tone":
            tone = str(g.get("tone") or "").strip()
            if tone:
                self.persona_config["tone"] = tone
                return {"tone": tone}
        if t == "speak_now":
            self._force_tick = True
        if t == "set_cooldown":
            try:
                self.cooldown_seconds = float(g.get("seconds", self.cooldown_seconds))
                return {"cooldown_seconds": self.cooldown_seconds}
            except Exception:
                pass
        return None

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
        last = msgs[-1]
        if last.get("author_id") == self.agent_id:
            return StepOutcome(status="info", text=None, state={"seen_self": True, "conversation_id": self.conversation_id})

        if not self._can_speak_now():
            return StepOutcome(status="info", text=None, state={"cooldown": True, "conversation_id": self.conversation_id})

        # Simple activation: reply if last message is user or another agent
        window = msgs[-10:]  # small recent window
        reply = await self._generate_reply(window)
        append_message(self.conversation_id, self.agent_id, "agent", reply, meta={"session_id": self.session_id})
        self._last_spoke_at = datetime.now()

        return StepOutcome(
            status="ok",
            text=reply,
            state={"conversation_id": self.conversation_id, "spoke": True, "tone": self.persona_config.get("tone")}
        )