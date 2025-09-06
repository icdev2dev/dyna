from typing import Optional

from baml_client.async_client import b
from baml_client.types import StepFrameIn, StepFrameOut

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

        guidance_interpreter="",  # optional: free-form -> structured dict

        persist_guidance_raw: bool = True,
        persist_guidance_normalized: bool = True,
    ):
        self.current_subject = initial_subject  # set first
        self.guidance_interpreter = guidance_interpreter

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
        self.guidance_interpreter = guidance_interpreter
        
    def initial_context(self) -> Optional[dict]:
        return {
            "agent_type": "JokeAgent",
            "subject": self.current_subject,
        }

    async def run(self):
# Explicitly call the LoopingAgentBase run to avoid AgentBase.run
        return await LoopingAgentBase.run(self)
    
    async def apply_guidance(self, g) -> Optional[dict]:
        
        try:
            if isinstance(g, dict) and "subject" in g:
                self.current_subject = str(g["subject"])
                return {"subject": self.current_subject}
            # Simple heuristic if free-form text is provided and no interpreter
            if isinstance(g, dict) and "_raw_text" in g:
                raw = g["_raw_text"]
                # naive parse: "subject: X" or "about X"
                import re
                m = re.search(r"(?:subject\s*:\s*|about\s+)([A-Za-z0-9 _-]{2,})", str(raw), re.IGNORECASE)
                if m:

                    self.guidance_interpreter = m.group(1).strip()
                    return {"subject": self.current_subject, 
                            "guidance": self.guidance_interpreter
                    }
        except Exception:
            pass
        return None

    async def do_tick(self, step: int) -> StepOutcome:

        in_arg = StepFrameIn(context=self.current_subject, guidance=self.guidance_interpreter)
        joke =  await b.TellAJokeV2(in_arg=in_arg)

        text = getattr(joke, "text", None) or str(joke)

        # Provide agent state for storage; include paused for transparency
        state = {"subject": self.current_subject, "guidance": self.guidance_interpreter, "paused": self._paused_flag()}

        return StepOutcome(
            status="ok",
            text=text,
            state=state,
        )
    