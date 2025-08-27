import asyncio
from baml_test2 import tell_a_joke

from baml_client.types import MonikerStepFrameIn, MonikerStepFrameOut, MonikerGuidance, MonikerState

from agent_core import InterruptMixin, AgentBase, PauseMixin, StopMixin

from datetime import datetime


class JokeAgent(StopMixin, PauseMixin, InterruptMixin, AgentBase):
    def __init__(self, agent_id, session_id,  initial_subject="foot",  state_updater=None, steps_appender=None):
        super().__init__(agent_id)
        self.session_id = session_id
        self.current_subject = initial_subject
        self._task = None  # set by creator
        self._state_updater = state_updater  # async callable: (status, iteration, result, context, history)
        self._steps_appender = steps_appender


    async def _state_update(self, status=None, iteration=None, result=None, context=None, history=None):
        if self._state_updater:
            await self._state_updater(
                agent_id=self.agent_id,
                status=status,
                iteration=iteration,
                result=result,
                context=context,
                history=history,
            )

    async def run(self):
        step = 0

        await self._state_updater(status="starting", iteration=step, context={"agent_type": "JokeAgent", "current_subject": self.current_subject, "paused": False})
        print(f"JokeAgent {self.agent_id} started!")
        await self._state_updater(status="running", iteration=step, context={"agent_type": "JokeAgent", "current_subject": self.current_subject, "paused": False})

        while True:
            if self.should_stop():
                print(f"JokeAgent {self.agent_id}: stopping.")
                break

            await self.wait_if_paused()

                    # Allow stop to break out even if we were paused
            if self.should_stop():
                print(f"JokeAgent {self.agent_id}: stopping after pause.")
                break

            # Check for new guidance
            guidance = await self.check_interrupt()
            if guidance is not None and isinstance(guidance, dict) and "subject" in guidance:
                
                self.current_subject = guidance["subject"]
                print(f"JokeAgent {self.agent_id}: now telling jokes about {self.current_subject}")

            joke = await tell_a_joke(self.current_subject)

            joke = joke.text

            print(f"[Agent {self.agent_id}] Joke: {joke}")

            if self._state_updater:
                try:
                    print("---------------------------------------------")
                    print(f"STEP: {step}")
                    print("---------------------------------------------")
                    
                    await self._state_updater(status="running", iteration=step, result=joke, context={"subject": self.current_subject, "paused": self.is_paused()},)                    
                except Exception as e:
                    print(f"state_updater error for {self.agent_id}: {e}")

            if self._steps_appender:
                try:
                    await self._steps_appender(
                        iteration=step,
                        status="ok",
                        text=joke,
                        state={"subject": self.current_subject, "paused": self.is_paused()},
                        # guidance can be included if you retain the last guidance applied
                    )
                except Exception as e:
                    print(f"steps_appender error for {self.agent_id}: {e}")

            await asyncio.sleep(3)
            step += 1

        await self._state_updater(status="stopped", context={"ended_at": datetime.now().isoformat()})
