import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
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

        self._tick_event: Optional[asyncio.Event] = asyncio.Event()
        self._tick_event.set()  # ensure the first tick runs immediately
        # Paused flag is computed per-tick if PauseMixin is present
        # NEW: simple tool registry (name -> async callable(args)->result)
        self._tool_registry: Dict[str, Any] = {}

    # ---------- Overridables (subclasses implement minimal logic) ----------
    def initial_context(self) -> Optional[dict]:
        return {"agent_type": self.__class__.__name__}


    # NEW: allow registering tools per agent (or wire at construction)
    def register_tool(self, name: str, coro):
        self._tool_registry[name] = coro

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
        try:
            await self._state_updater(
                agent_id=self.agent_id,
                status=status,
                iteration=iteration,
                result=result,
                context=context,
                history=history,
            )
        except Exception as e:
            
            print(f"{self.__class__.__name__} {self.agent_id}: state_updater error: {e}")

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



    async def _wait_for_tick_or_timeout(self):
        try:
        # Wake either by interrupt (event set) or fallback timer
            await asyncio.wait_for(self._tick_event.wait(), timeout=self.loop_interval)
        except asyncio.TimeoutError:
            pass
        finally:
        # Clear event (if it was set). If new interrupts arrive later, they set it again.
            try:
                self._tick_event.clear()
            except Exception:
                pass



    async def _drain_interrupts_and_apply(self) -> Optional[dict]:
        """
        Drain the interrupt queue fully. For each item:
        - interpret -> normalized
        - apply_guidance(normalized)
        - merge context deltas
        Returns a guidance object to persist for this tick (includes raw+normalized of the LAST item by default).
        If you want to persist all, you could aggregate into a list instead.
        """
        persisted = None
        while True:
            g_raw = await self._check_interrupt()
            if g_raw is None:
                break
            try:
                g_norm = await self.interpret_guidance(g_raw)
                ctx_delta = await self.apply_guidance(g_norm if g_norm is not None else g_raw)
                self._merge_context(ctx_delta)
                # Build guidance-to-persist payload respecting flags
                g_obj = {}
                if self.persist_guidance_raw:
                    g_obj["raw"] = g_raw
                if self.persist_guidance_normalized:
                    g_obj["normalized"] = g_norm
                persisted = g_obj if g_obj else None
            except Exception as ge:
            # Keep draining; log and continue
                print(f"{self.__class__.__name__} {self.agent_id}: guidance error: {ge}")
            # You could also set persisted to an error marker if desired
                continue
        return persisted



    async def run(self):
        step = 0
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

            # Wait to be woken by interrupts or fallback timer
            await self._wait_for_tick_or_timeout()

            # Pause gate
            await self._wait_if_paused()
            if self.should_stop():
                print(f"{self.__class__.__name__} {self.agent_id}: stopping after pause.")
                break

            # Drain and apply all interrupts for this tick
            guidance_to_persist = await self._drain_interrupts_and_apply()

            outcome = StepOutcome()
            try:
                outcome = await self.do_tick(step)
                if not isinstance(outcome, StepOutcome):
                    outcome = StepOutcome(text=str(outcome))
            except Exception as e:
                outcome = StepOutcome(status="error", error=str(e))
                print(f"{self.__class__.__name__} {self.agent_id} tick error @ step {step}: {e}")
                if not self.should_continue_on_error(e):
                    await self._append_step(step, outcome, guidance_to_persist)
                    await self._state_update(status="error", iteration=step, result=outcome.error, context=self._context_snapshot())
                    break

            # Execute agent intent (silent/speak/stop for now)
            try:
                if isinstance(outcome.data, dict):
                    intent = outcome.data.get("intent")
                    if intent:
                        outcome = await self._execute_intent(step, intent, outcome)
            except Exception as ie:
                print(f"{self.__class__.__name__} {self.agent_id}: intent execution error: {ie}")
                outcome = StepOutcome(status="error", error=str(ie))

            if guidance_to_persist and outcome.guidance is None:
                outcome.guidance = guidance_to_persist

            await self._append_step(step, outcome, outcome.guidance)
            await self._state_update(
                status="running",
                iteration=step,
                result=outcome.text if outcome.text is not None else outcome.error,
                context=self._context_snapshot(),
            )

            step += 1
            # No sleep; next loop waits on tick event or timeout
            
        try:
            await self.on_stop()
        finally:
            await self._state_update(
                status="stopped",
                context={"ended_at": datetime.now(timezone.utc).isoformat(), **self._context_snapshot()},
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



# NEW: Core executor for agent intents
    async def _execute_intent(self, step: int, intent: dict, outcome: StepOutcome) -> StepOutcome:
        t = (intent.get("type") or "").lower()

        if t == "silent":
            # no text; annotate state
            st = (outcome.state or {}) | {"silent": True, "reason": intent.get("reason")}
            outcome.status = "info"
            outcome.text = None
            outcome.state = st
            return outcome

        if t == "speak":
            text = intent.get("text") or ""
            mode = intent.get("mode")
            await self._append_conversation_message_if_persona(text, mode)
            outcome.status = "ok"
            outcome.text = text
            st = (outcome.state or {}) | {"spoke": True, "mode": mode}
            outcome.state = st
            # Clear force_tick if present
            try:
                if getattr(self, "_force_tick", False):
                    self._force_tick = False
            except Exception:
                pass
            return outcome

        if t == "call_tool":
            exec_mode = (intent.get("execution") or "inline").lower()
            if exec_mode != "inline":
                raise ValueError("Only inline tool execution is supported right now")
            tools = intent.get("tools") or []
            mode_after = intent.get("mode_after") or "insight"
            timeout_s = float(intent.get("timeout_s", 12.0))
            tool_results = await self._run_tools(tools, timeout_s=timeout_s)

            # Race-avoid: if newer message arrived in the conversation, skip speaking
            if await self._conversation_changed_since_last_seen():
                outcome.status = "info"
                outcome.text = None
                outcome.data = (outcome.data or {}) | {"tool_results": tool_results}
                outcome.state = (outcome.state or {}) | {"race_avoided": True}
                return outcome

            # Ask agent to compose final reply after tools if such hook exists
            if hasattr(self, "_compose_reply_after_tools"):
                try:
                    text = await self._compose_reply_after_tools(tool_results, mode_after)
                except Exception:
                    text = f"[{mode_after}] {tool_results}"
            else:
                text = f"[{mode_after}] {tool_results}"

            await self._append_conversation_message_if_persona(text, mode_after)
            outcome.status = "ok"
            outcome.text = text
            outcome.data = (outcome.data or {}) | {"tool_results": tool_results}
            outcome.state = (outcome.state or {}) | {"spoke": True, "mode": mode_after}
            try:
                if getattr(self, "_force_tick", False):
                    self._force_tick = False
            except Exception:
                pass
            return outcome

        if t == "stop":
            self.request_stop()
            outcome.status = "info"
            outcome.text = None
            outcome.state = (outcome.state or {}) | {"stopping": True, "reason": intent.get("reason")}
            return outcome

        # Unknown
        outcome.notes = (outcome.notes or "") + " | unknown_intent"
        return outcome

    # NEW: Post a message if this is a PersonaAgent (has conversation_id)
    async def _append_conversation_message_if_persona(self, text: str, mode: Optional[str] = None):
        try:
            conv_id = getattr(self, "conversation_id", None)
            if not conv_id:
                return
            from store.messages import append_message
            meta = {"session_id": self.session_id}
            if mode:
                meta["mode"] = mode
            append_message(conv_id, self.agent_id, "agent", text, meta=meta)
            if hasattr(self, "_last_spoke_at"):
                from datetime import datetime as _dt
                self._last_spoke_at = _dt.now()
        except Exception as e:
            print(f"{self.__class__.__name__} {self.agent_id}: append_message error: {e}")

    # NEW: Inline tools with timeout, registry-based
    async def _run_tools(self, tools: list[dict], timeout_s: float = 10.0):
        async def call_one(t):
            name = t.get("name")
            args = t.get("args", {}) or {}
            fn = self._tool_registry.get(name)
            if not fn or not callable(fn):
                return {"name": name, "args": args, "error": "unknown_tool"}
            try:
                res = await fn(args)
                return {"name": name, "args": args, "result": res}
            except Exception as e:
                return {"name": name, "args": args, "error": str(e)}

        try:
            return await asyncio.wait_for(asyncio.gather(*(call_one(t) for t in tools)), timeout=timeout_s)
        except asyncio.TimeoutError:
            return [
                {"name": t.get("name"), "args": t.get("args", {}) or {}, "error": "timeout"}
                for t in tools
            ]

    # NEW: Race-avoidance: did new messages arrive?
    async def _conversation_changed_since_last_seen(self) -> bool:
        try:
            conv_id = getattr(self, "conversation_id", None)
            last_seen = getattr(self, "last_seen_iso", None)
            if not conv_id or not last_seen:
                return False
            from store.messages import list_messages_since
            return bool(list_messages_since(conv_id, last_seen, limit=1))
        except Exception:
            return False
        