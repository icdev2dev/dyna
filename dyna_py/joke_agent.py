import asyncio
from baml_test import tell_a_joke
from agent_core import InterruptMixin, AgentBase, PauseMixin, StopMixin

class JokeAgent(StopMixin, PauseMixin, InterruptMixin, AgentBase):
    def __init__(self, agent_id, initial_subject="foot"):
        super().__init__(agent_id)
        self.current_subject = initial_subject
        self._task = None  # set by creator

    async def run(self):
        step = 0
        print(f"JokeAgent {self.agent_id} started!")
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
            if guidance is not None:
                # Expect guidance as a dict: { "subject": "cats" }
                if isinstance(guidance, dict) and "subject" in guidance:
                    self.current_subject = guidance["subject"]
                    print(f"JokeAgent {self.agent_id}: now telling jokes about {self.current_subject}")
                    # Optionally, you could print a cue or do something else

            joke = await tell_a_joke(self.current_subject)
            print(f"[Agent {self.agent_id}] Joke: {joke}")

            await asyncio.sleep(3)
            step += 1

