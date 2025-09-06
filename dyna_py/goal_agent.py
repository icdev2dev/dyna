from baml_client import b
# Flask snippet
from flask import Flask, request, jsonify

from dataclasses import is_dataclass, asdict
from enum import Enum



def to_plain(obj):
# Recursively convert dataclasses, enums, lists, dicts to plain JSON types
    if obj is None:
        return None
    if isinstance(obj, Enum):
        return obj.value
    if is_dataclass(obj):
    # asdict then post-process (asdict doesn’t convert enums)
        return {k: to_plain(v) for k, v in asdict(obj).items()}
    if isinstance(obj, (list, tuple)):
        return [to_plain(x) for x in obj]
    if isinstance(obj, dict):
        return {str(k): to_plain(v) for k, v in obj.items()}
    # Pydantic-like models
    if hasattr(obj, "model_dump"):
        return to_plain(obj.model_dump())
    # Fallback for objects with dict
    if hasattr(obj, "dict"):
        return {k: to_plain(v) for k, v in vars(obj).items()}
    return obj

def api_generate_task_graph():
    data = request.get_json(force=True) or {}

    in_arg = data.get("in_arg", "") or data.get("prompt", "")

    if not in_arg:
        return jsonify({"error": "in_arg required"}), 400
    tg = b.GenerateTaskGraph(in_arg=in_arg)

# Convert to plain JSON-able structure
    tg_plain = to_plain(tg)

# Optional: quick sanity checks to help the UI
    if not isinstance(tg_plain, dict) or not isinstance(tg_plain.get("tasks"), list):
        return jsonify({"error": "Invalid TaskGraph from backend"}), 500

# Debug print (pretty JSON)
# import json; print(json.dumps(tg_plain, indent=2))

    return jsonify(tg_plain)
    

    

