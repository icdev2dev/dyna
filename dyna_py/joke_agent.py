import asyncio
from typing import Optional, Dict, Any

from baml_test2 import  tell_a_joke_v2

from agent_core import PauseMixin, InterruptMixin
from agent_loop import LoopingAgentBase, StepOutcome

class JokeAgent(PauseMixin, InterruptMixin, LoopingAgentBase):
    def __init__(
        self,
        agent_id: str,
        session_id: str,
        *,
        initial_subject: str = "foot",

        state_updater=None,
        steps_appender=None,

        loop_interval: float = 30.0,

        guidance_interpreter=None,  # optional: free-form -> structured dict

        persist_guidance_raw: bool = True,
        persist_guidance_normalized: bool = True,
    ):
        self.current_subject = initial_subject  # set first
        super().__init__(
            agent_id,
            session_id,
            state_updater=state_updater,
            steps_appender=steps_appender,
            loop_interval=loop_interval,
            guidance_interpreter=guidance_interpreter,
            persist_guidance_raw=persist_guidance_raw,
            persist_guidance_normalized=persist_guidance_normalized,
        )
        self.current_subject = initial_subject

    def initial_context(self) -> Optional[dict]:
        return {
            "agent_type": "JokeAgent",
            "subject": self.current_subject,
        }

    async def apply_guidance(self, g) -> Optional[dict]:
        # g may be a dict (preferred) or contain {"_raw_text": "..."} if free-form
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        print(g)        
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        
        try:
            if isinstance(g, dict) and "subject" in g:
                self.current_subject = str(g["subject"])
                print(f"JokeAgent {self.agent_id}: now telling jokes about {self.current_subject}")
                return {"subject": self.current_subject}
            # Simple heuristic if free-form text is provided and no interpreter
            if isinstance(g, dict) and "_raw_text" in g:
                raw = g["_raw_text"]
                # naive parse: "subject: X" or "about X"
                import re
                m = re.search(r"(?:subject\s*:\s*|about\s+)([A-Za-z0-9 _-]{2,})", str(raw), re.IGNORECASE)
                if m:
                    self.current_subject = m.group(1).strip()
                    print(f"JokeAgent {self.agent_id}: now telling jokes about {self.current_subject}")
                    return {"subject": self.current_subject}
        except Exception:
            pass
        return None

    async def do_tick(self, step: int) -> StepOutcome:
        # Call your BAML function; it returns an object with .text
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        joke = await tell_a_joke_v2(self.current_subject)
        text = getattr(joke, "text", None) or str(joke)

        print(f"[Agent {self.agent_id}] Joke: {text} ENTIRE THING : {joke}")

        # Provide agent state for storage; include paused for transparency
        state = {"subject": self.current_subject, "paused": self._paused_flag()}

        return StepOutcome(
            status="ok",
            text=text,
            state=state,
        )