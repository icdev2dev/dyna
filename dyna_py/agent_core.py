import asyncio

class AgentBase:
    def __init__(self, agent_id, *args, **kwargs):
        super().__init__(*args, **kwargs)  # cooperate in MRO
        self.agent_id = agent_id
    async def run(self):
        raise NotImplementedError

class InterruptMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interrupt_queue = asyncio.Queue()
    @classmethod
    def interrupt_data_type(cls):
        return None
    async def interrupt(self, guidance):
        await self.interrupt_queue.put(guidance)
    async def check_interrupt(self):
        if not self.interrupt_queue.empty():
            return await self.interrupt_queue.get()
        return None

class PauseMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # start unpaused

    async def wait_if_paused(self):
        await self._pause_event.wait()

    def pause(self):
        self._pause_event.clear()

    def resume(self):
        self._pause_event.set()

    def is_paused(self):
        return not self._pause_event.is_set()



class StopMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stop_event = asyncio.Event()

    def request_stop(self):
        self._stop_event.set()

    def should_stop(self):
        return self._stop_event.is_set()
