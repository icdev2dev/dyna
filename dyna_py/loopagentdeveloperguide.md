# LoopingAgentBase Developer Guide
This guide explains how to build agents by subclassing LoopingAgentBase, how guidance works, and how to plug into the existing action/state/steps infrastructure. It includes examples, best practices, and an API reference.

## Why LoopingAgentBase?

LoopingAgentBase centralizes all the boilerplate so subclasses can focus on “doing work” each tick. It provides:

- A robust async run loop with start/stop lifecycle.
- Optional Pause/Resume and Interrupt support via mixins.
- Consistent state and step persistence.
- Guidance handling (free-form or structured) with optional normalization.
- Error capturing with “continue on error” default.

You only implement a few hooks like do_tick and optionally apply_guidance. Everything else (iteration, context, persistence, pauses, interrupts) is handled by the base.

## Quick Start

- Minimal agent that emits one output per tick:

`
from agent_loop import LoopingAgentBase, StepOutcome

class HelloAgent(LoopingAgentBase):
    async def do_tick(self, step: int) -> StepOutcome:
        text = f"Hello from step {step}"
        return StepOutcome(text=text, state={"step": step})
`

- With Pause/Interrupt support:

`
from agent_core import PauseMixin, InterruptMixin
from agent_loop import LoopingAgentBase, StepOutcome

class JokeAgent(PauseMixin, InterruptMixin, LoopingAgentBase):
    def __init__(self, agent_id, session_id, *, initial_subject="foot", **kwargs):
        super().__init__(agent_id, session_id, **kwargs)
        self.current_subject = initial_subject

    def initial_context(self):
        return {"agent_type": "JokeAgent", "subject": self.current_subject}

    async def apply_guidance(self, g):
        # g may be dict or normalized free-form. Update internal state and return context delta.
        if isinstance(g, dict) and "subject" in g:
            self.current_subject = str(g["subject"])
            return {"subject": self.current_subject}
        if isinstance(g, dict) and "_raw_text" in g:
            # very naive parse: “about cats”
            import re
            m = re.search(r"(?:subject\s*:\s*|about\s+)([A-Za-z0-9 _-]{2,})", g["_raw_text"], re.IGNORECASE)
            if m:
                self.current_subject = m.group(1).strip()
                return {"subject": self.current_subject}
        return None

    async def do_tick(self, step: int) -> StepOutcome:
        # Example: call a tool/LLM to get a joke
        from baml_test2 import tell_a_joke
        joke = await tell_a_joke(self.current_subject)
        text = getattr(joke, "text", None) or str(joke)
        return StepOutcome(text=text, state={"subject": self.current_subject, "paused": self._paused_flag()})
`

Constructing your agent is the same as today; agent.py and store code don’t need to change.

## Key Concepts
### Mixins: Opt-in Capabilities
- Stop capability is always present via StopMixin inside LoopingAgentBase.
- Add Pause support by inheriting PauseMixin.
- The base will detect and call wait_if_paused() automatically each loop.
- Add Interrupt support by inheriting InterruptMixin.
- The base will detect and non-blockingly call check_interrupt() each loop.
- This duck-typing design lets each agent choose only the features it needs.

### Guidance: Free-form or Structured
Incoming guidance can be:
- A dict (structured fields like {"subject": "cats"}), or
- Free-form string (e.g., “switch to cats jokes”)
- The base can use a guidance_interpreter callable to normalize free-form text into a structured dict your agent understands. If no interpreter is provided, the base wraps free-form text as {"_raw_text": "..."}
- Your agent applies the guidance in apply_guidance(...) and returns a context delta dict (what changed), which the base merges into context.

### Persistence: State and Steps
On every tick (by design), the base:
Appends a step via steps_appender including text/data/state/guidance/status/error.
Calls state_updater with status="running", current iteration, result, and context.
State and data are serialized following your existing store conventions:
state: should be dict/list and is JSON-encoded.
data: optional; if dict/list it’s JSON-encoded; strings are stored as-is.


### Error Handling
If do_tick raises, the base records an error step, logs the error, updates state, and continues by default. Override should_continue_on_error if you want to stop on certain exceptions.


## Lifecycle and Hooks
Subclass these methods to implement your agent logic.

- def initial_context(self) -> Optional[dict]
-- Provide initial context for state updates and observability.
-- Base ensures “agent_type” is set to the class name if you don’t provide it.


- async def on_start(self) -> Optional[dict]
-- Called once before the loop begins.
-- Return a context delta to merge (e.g., feature flags, initial parameters).

- async def do_tick(self, step: int) -> StepOutcome
-- Required. Perform one unit of work and return StepOutcome.
-- Keep it quick; if it must block, use async IO or split into sub-steps.


- async def apply_guidance(self, normalized_guidance) -> Optional[dict]
-- Optional. Update your internal state (e.g., change topic/difficulty).
-- Return a dict of context fields that changed. The base merges this into the saved context for transparency.

- async def interpret_guidance(self, raw) -> Optional[dict]
-- Optional override; base will call guidance_interpreter if provided at construction, else:
-- If raw is dict: returns raw
-- If raw is string: returns {"_raw_text": raw}

- def should_continue_on_error(self, exc: Exception) -> bool
-- Default True (continue). Override if needed.

- async def on_stop(self) -> None

--Optional. Cleanup if needed.

## StepOutcome
StepOutcome standardizes what a tick returns.

- Fields:

status: "ok" | "error" | "info" (default "ok")
text: Optional[str] — Human-readable output for logs/UI
data: Optional[dict | list | str] — Machine-friendly payload
state: Optional[dict | list] — Agent state snapshot you want saved with this step
notes: Optional[str] — Free-form notes
latency_ms: Optional[int] — If you measure the work time
error: Optional[str] — Error message, if any
guidance: Optional[dict] — Guidance that influenced this tick (base can auto-fill)

- Tips:

Provide a minimal state on every tick with the fields your UI/tools care about (e.g., subject, step, mode).
If you return something other than StepOutcome, the base will coerce it to StepOutcome(text=str(value)).


## Constructor and Configuration
LoopingAgentBase.__init__:

- Parameters:

agent_id: str
session_id: str
state_updater: Optional[async callable] — Called every tick with status, iteration, result, context, history
steps_appender: Optional[async callable] — Appends a step row; see store.steps_async.append_step_async
loop_interval: float = 3.0 — Sleep time between ticks
guidance_interpreter: Optional[async callable] — Normalize free-form guidance into a dict
persist_guidance_raw: bool = True — Store raw input guidance on steps
persist_guidance_normalized: bool = True — Store normalized guidance on steps

- Notes:

The base updates state on every tick for transparency.
The base includes “paused” in the context snapshot if PauseMixin is present.


## Guidance Handling in Detail
### Flow per loop:

Base calls check_interrupt() if InterruptMixin is present.
If guidance received:
Normalize via guidance_interpreter (if provided) or default wrapper.
Call apply_guidance() with the normalized guidance.
Merge returned context delta into base context.
Optionally persist:
Raw guidance (persist_guidance_raw)
Normalized guidance (persist_guidance_normalized)
If you didn’t include guidance in your StepOutcome, the base adds it automatically.

### Design choices:

Accepting free-form text lets callers avoid hard-coded schemas.
Agent-specific interpretation/metadata can evolve independently.
Persisting both raw and normalized guidance improves auditability.

## Pause/Resume and Interrupt

### To enable pausing:

Inherit from PauseMixin
The base will automatically:
Wait for wait_if_paused() each loop
Include paused in the context


### To enable interrupts:

Inherit from InterruptMixin
The base will automatically:
Non-blockingly call check_interrupt() each loop
Interpret and apply guidance if present
Persist guidance
Your agent may also expose methods pause(), resume(), and interrupt(guidance) via these mixins — they are already wired to the action handlers in agent.py.

## Integration with agent.py and Stores (framework developer notes)
### No changes needed in agent.py:

create_agent: constructs your agent and passes state_updater and steps_appender.
agent_pause/agent_resume: call your mixin methods if present.
agent_interrupt: calls your interrupt(guidance); the base loop applies it next tick.
agent_destroy: requests stop and waits for loop to exit.

### Stores (unchanged):

store.agent_state.upsert_agent_state: called on every tick, including “starting”, “running”, “stopped”.
store.steps_async.append_step_async: called on every tick with your StepOutcome fields.

## Example: QuizAgent Variants
### No pause or interrupt:

class QuizAgent(LoopingAgentBase):
    def __init__(self, agent_id, session_id, *, questions, **kwargs):
        super().__init__(agent_id, session_id, **kwargs)
        self.questions = list(questions)
        self.index = 0

    def initial_context(self):
        return {"agent_type": "QuizAgent", "total_questions": len(self.questions)}

    async def do_tick(self, step: int) -> StepOutcome:
        if self.index >= len(self.questions):
            # You can request stop from inside if you want:
            self.request_stop()
            return StepOutcome(status="info", text="Quiz complete", state={"done": True})
        q = self.questions[self.index]
        self.index += 1
        return StepOutcome(text=f"Q{self.index}: {q}", state={"index": self.index})

### With interrupts (change difficulty) but no pause:

class QuizAgent(InterruptMixin, LoopingAgentBase):
    def __init__(self, agent_id, session_id, *, topic, difficulty="easy", **kwargs):
        super().__init__(agent_id, session_id, **kwargs)
        self.topic = topic
        self.difficulty = difficulty

    def initial_context(self):
        return {"agent_type": "QuizAgent", "topic": self.topic, "difficulty": self.difficulty}

    async def apply_guidance(self, g):
        if isinstance(g, dict) and "difficulty" in g:
            self.difficulty = g["difficulty"]
            return {"difficulty": self.difficulty}
        if isinstance(g, dict) and "_raw_text" in g:
            if "hard" in g["_raw_text"].lower():
                self.difficulty = "hard"
                return {"difficulty": self.difficulty}
        return None

    async def do_tick(self, step: int) -> StepOutcome:
        # Generate a question based on self.topic and self.difficulty
        text = f"[{self.difficulty}] What is ... about {self.topic}?"
        return StepOutcome(text=text, state={"difficulty": self.difficulty})


## Best Practices
- Keep do_tick responsive:
Use async IO for network calls.
If long work is needed, consider more frequent, smaller ticks or background tasks with progress in state.

- Always return a state snapshot the UI/ops care about (e.g., subject, paused, mode).
- Let the base persist guidance automatically for auditability; turn off raw persistence if guidance may contain PII.
- Use initial_context to identify your agent type and initial parameters.
- Use apply_guidance to alter internal state; return the context delta so observers see changes immediately.
- Log sparingly inside ticks; rely on steps/state for observability.
- If your agent sometimes needs to stop itself, call self.request_stop() inside do_tick.

## Error Handling and Recovery
- Defaults:
Tick errors are recorded as a step with status="error".
State updates continue; loop keeps going.

- Customize:
Override should_continue_on_error to stop on certain exceptions.

- Guidance errors:
Interpreter or apply_guidance errors are logged; the tick proceeds.

## Debugging Tips
- Verify LanceDB tables exist and schema match:
store/schemas.py has helpers to create/drop tables.

- Inspect steps and state directly:
store/agent_steps.list_agent_steps_latest(...)
store/agent_state.get_agent_state(...)

- Enable ad hoc logging in your agent; ensure it won’t block.
- Use the queue (queue_imp.py) to push actions:
Create agent, send guidance, pause/resume, destroy.
- If development server uses Flask + SocketIO, check for event loop conflicts. All agent loops run under asyncio.


## Advanced Topics
### Custom guidance schema/metadata:
Agents can publish a GuidanceSchema (e.g., JSON Schema) describing understood fields (subject, tone, difficulty).
Tooling could use this to build UIs for structured guidance while still accepting free-form text.

### Dynamic loop interval:
You can adjust self.loop_interval at runtime based on load, signals, or state.

### Backoff and retries:
Implement in do_tick and capture retry metadata in state or notes.

### Metrics:
Track latency_ms by timing your tick or key operations.
### Last guidance caching:
If you need last guidance in logic, store it in your agent’s internal fields during apply_guidance.

# API Reference
## LoopingAgentBase
### Constructor:

agent_id: str
session_id: str
state_updater: Optional[async callable(agent_id, status, iteration, result, context, history)]
steps_appender: Optional[async callable(agent_id, iteration, ...fields)]
loop_interval: float = 3.0
guidance_interpreter: Optional[async callable(raw_guidance) -> dict]
persist_guidance_raw: bool = True
persist_guidance_normalized: bool = True

### Hooks:

def initial_context(self) -> Optional[dict]
async def on_start(self) -> Optional[dict]
async def do_tick(self, step: int) -> StepOutcome
async def apply_guidance(self, normalized_guidance) -> Optional[dict]
async def interpret_guidance(self, raw) -> Optional[dict] # usually rely on guidance_interpreter
def should_continue_on_error(self, exc: Exception) -> bool
async def on_stop(self) -> None

### Helpers (available to subclasses):

self.request_stop() — ask loop to stop
self._paused_flag() — True if PauseMixin is present and paused
self._context_snapshot() — the current context (including paused)

### Mixins you can add:

PauseMixin:
pause(), resume(), is_paused(), wait_if_paused()
InterruptMixin:
interrupt(guidance), check_interrupt()


## StepOutcome dataclass
### Fields:

status: str = "ok"
text: Optional[str] = None
data: Optional[dict | list | str] = None
state: Optional[dict | list] = None
notes: Optional[str] = None
latency_ms: Optional[int] = None
error: Optional[str] = None
guidance: Optional[dict] = None

# FAQ
Q: Do I need to implement pause/resume/interrupt for every agent?
A: No. Only inherit the mixins you need. The base will use them if present.

Q: How often does state update?
A: Every tick, by design, to maximize transparency.

Q: How is guidance stored?
A: Per tick when received; includes raw and/or normalized forms depending on flags.

Q: How do I stop after finishing work?
A: Call self.request_stop() from inside do_tick.

Q: What if my tick needs to do multiple actions?
A: You can compose actions and return a single StepOutcome, or split actions across ticks by manipulating agent state.

# Migration Notes

If you’re refactoring an existing agent:

Move long-running loop logic to LoopingAgentBase.
Keep only agent-specific state, do_tick, and apply_guidance in your subclass.
Remove direct calls to state/steps persistence; the base now handles them.
Ensure agent.py still constructs the agent with state_updater and steps_appender.
If you want a ready-to-commit base implementation and an updated JokeAgent, ask for a unified diff and we’ll generate the exact file changes.

