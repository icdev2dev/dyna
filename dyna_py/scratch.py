from dataclasses import dataclass, field
from typing import Optional, Any, Dict


@dataclass
class StepFrame:
    
    # Input (loop -> agent)
    iteration: int
    context: Dict[str, Any] = field(default_factory=dict)      # snapshot from loop
    guidance: Optional[Dict[str, Any]] = None                  # latest normalized guidance

    # Output (agent -> loop)
    status: str = "ok"                                         # "ok" | "error" | "info"
    control: str = "continue"                                  # "continue" | "pause" | "stop" | "done"
    
    reason: Optional[str] = None                                # e.g., "need_user_input", "complete"
    hint: Optional[Dict[str, Any]] = None                       # e.g., {"resume_when": "user_uploaded_csv"}

    
    text: Optional[str] = None
    payload: Any = None
    context_delta: Optional[Dict[str, Any]] = None
    
    