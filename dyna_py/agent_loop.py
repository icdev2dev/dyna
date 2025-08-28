import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Awaitable, Callable, Optional, Dict, Union

from agent_core import AgentBase, StopMixin

GuidanceInput = Union[str, dict, list, None]
GuidanceDict = Optional[dict]

@dataclass
class StepOutcome:
# Default status is "ok"; use "error" or "info" as needed
    status: str = "ok"
    text: Optional[str] = None
    data: Optional[Union[dict, list, str]] = None
    state: Optional[Union[dict, list]] = None  # JSON-encoded by store layer
    notes: Optional[str] = None
    latency_ms: Optional[int] = None
    error: Optional[str] = None
    guidance: Optional[dict] = None  # normalized guidance affecting this tick

class LoopingAgentBase(AgentBase, StopMixin):
    def __init__ (
        self,
        agent_id: str,
        session_id: str,
        *,
        state_updater: Optional[Callable[..., Awaitable[None]]] = None,
        steps_appender: Optional[Callable[..., Awaitable[None]]] = None,
        loop_interval: float = 3.0,
        guidance_interpreter: Optional[Callable[[GuidanceInput], Awaitable[GuidanceDict]]] = None,
        persist_guidance_raw: bool = True,
        persist_guidance_normalized: bool = True,
    ):
        
        super().__init__(agent_id)
        self.session_id = session_id
        self._state_updater = state_updater
        self._steps_appender = steps_appender
        self.loop_interval = loop_interval
        self.guidance_interpreter = guidance_interpreter
        self.persist_guidance_raw = persist_guidance_raw
        self.persist_guidance_normalized = persist_guidance_normalized

        # Internal
        self._task: Optional[asyncio.Task] = None
        self._context: Dict[str, Any] = dict(self.initial_context() or {})
        # Ensure agent_type in context by default
        self._context.setdefault("agent_type", self.__class__.__name__)
        self.current_subject = None
        # Paused flag is computed per-tick if PauseMixin is present

    # ---------- Overridables (subclasses implement minimal logic) ----------
    def initial_context(self) -> Optional[dict]:
        return {"agent_type": self.__class__.__name__}

    async def on_start(self) -> Optional[dict]:
        return None

    async def on_stop(self) -> None:
        return None

    async def do_tick(self, step: int) -> StepOutcome:
        raise NotImplementedError

    async def apply_guidance(self, normalized_guidance: GuidanceInput) -> Optional[dict]:
        # Subclasses may update internal state based on guidance and return context delta
        return None

    async def interpret_guidance(self, raw: GuidanceInput) -> GuidanceDict:
        # If a custom interpreter is provided, use it; else minimal normalization
        if self.guidance_interpreter:
            try:
                return await self.guidance_interpreter(raw)
            except Exception:
                # Fall back to naive behavior on interpreter failure
                pass
        if isinstance(raw, dict):
            return raw
        if raw is None:
            return None
        # Put free-form text under a conventional key
        return {"_raw_text": str(raw)}

    def should_continue_on_error(self, exc: Exception) -> bool:
        return True  # default: keep going

    # ---------- Helpers ----------
    async def _state_update(self, status=None, iteration=None, result=None, context=None, history=None):
        if not self._state_updater:
            return
        await self._state_updater(
            agent_id=self.agent_id,
            status=status,
            iteration=iteration,
            result=result,
            context=context,
            history=history,
        )

    def _paused_flag(self) -> bool:
        # Duck-typed PauseMixin
        try:
            return bool(getattr(self, "is_paused")())
        except Exception:
            return False

    async def _wait_if_paused(self):
        # Duck-typed PauseMixin
        w = getattr(self, "wait_if_paused", None)
        if callable(w):
            await w()

    async def _check_interrupt(self) -> GuidanceInput:
        # Duck-typed InterruptMixin
        c = getattr(self, "check_interrupt", None)
        if callable(c):
            return await c()
        return None

    def _merge_context(self, delta: Optional[dict]):
        if delta and isinstance(delta, dict):
            self._context.update(delta)

    def _context_snapshot(self) -> dict:
        # Always include paused for transparency when available
        snap = dict(self._context)
        snap["paused"] = self._paused_flag()
        return snap

    # ---------- Main run loop ----------
    async def run(self):
        step = 0
        # starting
        await self._state_update(
            status="starting",
            iteration=step,
            context=self._context_snapshot(),
        )
        start_delta = await self.on_start() or {}
        self._merge_context(start_delta)
        await self._state_update(
            status="running",
            iteration=step,
            context=self._context_snapshot(),
        )
        print(f"{self.__class__.__name__} {self.agent_id} started (session {self.session_id}).")

        while True:
            if self.should_stop():
                print(f"{self.__class__.__name__} {self.agent_id}: stopping.")
                break

            await self._wait_if_paused()

            # Allow stop after pause
            if self.should_stop():
                print(f"{self.__class__.__name__} {self.agent_id}: stopping after pause.")
                break

            # Handle guidance (if InterruptMixin present)
            guidance_raw = await self._check_interrupt()
            guidance_norm = None
            context_delta_from_guidance = None
            guidance_to_persist = None

            if guidance_raw is not None:
                try:
                    guidance_norm = await self.interpret_guidance(guidance_raw)
                    context_delta_from_guidance = await self.apply_guidance(guidance_norm if guidance_norm is not None else guidance_raw)
                    self._merge_context(context_delta_from_guidance)
                except Exception as ge:
                    # Guidance processing error; record as info step later
                    print(f"{self.__class__.__name__} {self.agent_id}: guidance error: {ge}")

                # Build guidance object to persist this tick (if any)
                g_obj: Dict[str, Any] = {}
                if self.persist_guidance_raw:
                    g_obj["raw"] = guidance_raw
                if self.persist_guidance_normalized:
                    g_obj["normalized"] = guidance_norm
                guidance_to_persist = g_obj if g_obj else None

            # Execute one tick
            outcome = StepOutcome()

            
            try:
                outcome = await self.do_tick(step)
                if not isinstance(outcome, StepOutcome):
                    # Allow simple returns
                    outcome = StepOutcome(text=str(outcome))
            except Exception as e:
                outcome = StepOutcome(
                    status="error",
                    error=str(e),
                    text=None,
                    data=None,
                    state=None,
                )
                print(f"{self.__class__.__name__} {self.agent_id} tick error @ step {step}: {e}")
                if not self.should_continue_on_error(e):
                    # Record and then stop
                    await self._append_step(step, outcome, guidance_to_persist)
                    await self._state_update(
                        status="error",
                        iteration=step,
                        result=outcome.error,
                        context=self._context_snapshot(),
                    )
                    break

            # If guidance influenced this tick and outcome.guidance is empty, attach it
            if guidance_to_persist and outcome.guidance is None:
                outcome.guidance = guidance_to_persist

            # Persist step and state
            await self._append_step(step, outcome, outcome.guidance)
            await self._state_update(
                status="running",
                iteration=step,
                result=outcome.text if outcome.text is not None else outcome.error,
                context=self._context_snapshot(),
            )

            await asyncio.sleep(self.loop_interval)
            step += 1

        try:
            await self.on_stop()
        finally:
            await self._state_update(
                status="stopped",
                context={"ended_at": datetime.now().isoformat(), **self._context_snapshot()},
            )

    async def _append_step(self, step: int, outcome: StepOutcome, guidance: Optional[dict]):
        if not self._steps_appender:
            return
        try:
            await self._steps_appender(
                iteration=step,
                status=outcome.status,
                text=outcome.text,
                data=outcome.data,
                state=outcome.state,
                guidance=guidance,
                notes=outcome.notes,
                latency_ms=outcome.latency_ms,
                error=outcome.error,
            )
        except Exception as e:
            print(f"{self.__class__.__name__} {self.agent_id}: steps_appender error: {e}")
