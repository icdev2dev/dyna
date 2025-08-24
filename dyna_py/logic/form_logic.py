import re

ALLOWED_FIELD_TYPES = {"text", "number", "select", "checkbox"}

def sanitize_field(f):
    if not isinstance(f, dict):
        return None
    t = f.get("type")
    if t not in ALLOWED_FIELD_TYPES:
        t = "text"
    name = (f.get("name") or "").strip()
    if not name:
        return None
    label = f.get("label") or name
    out = {"type": t, "name": name, "label": str(label)}
    if t == "select":
        opts = f.get("options") or []
        norm = []
        for o in opts:
            if isinstance(o, str):
                norm.append({"value": o, "label": o})
            elif isinstance(o, dict) and "value" in o and "label" in o:
                norm.append({"value": o["value"], "label": o["label"]})
        out["options"] = norm
    return out

def sanitize_form_schema(schema):
    """Sanitizes a list of form field dicts."""
    if not isinstance(schema, list):
        return []
    return [s for s in (sanitize_field(f) for f in schema) if s is not None]

def clamp(v, lo, hi, default):
    try:
        n = float(v)
        return max(lo, min(hi, n))
    except Exception:
        return default

def sanitize_config(cfg):
    if not isinstance(cfg, dict):
        return None
    kind = cfg.get("kind") or "form"
    # allow only kinds the Canvas knows
    if kind not in {"form", "metadata", "chat"}:
        kind = "form"

    out = {
        "kind": kind,
        "title": str(cfg.get("title") or ("Metadata Editor" if kind == "metadata" else "Form")),
        "persist": "keep" if cfg.get("persist") == "keep" else "destroy"
    }

    if kind == "form":
        schema = cfg.get("schema") or []
        schema = sanitize_form_schema(schema)
        out["schema"] = schema
        out["value"] = cfg.get("value") if isinstance(cfg.get("value"), dict) else {}
    elif kind == "metadata":
        val = cfg.get("value")
        out["value"] = val if isinstance(val, dict) else {"entities": []}
    elif kind == "chat":
        out["messages"] = cfg.get("messages") if isinstance(cfg.get("messages"), list) else []
        out["chatConfig"] = cfg.get("chatConfig") if isinstance(cfg.get("chatConfig"), dict) else {}

    size = cfg.get("size") or {}
    out["size"] = {
        "w": clamp(size.get("w"), 320, 1200, 420),
        "h": clamp(size.get("h"), 200, 900, 280)
    }
    pos = cfg.get("position") or {}
    out["position"] = {
        "x": clamp(pos.get("x"), 0, 4000, 40),
        "y": clamp(pos.get("y"), 0, 4000, 40)
    }

    return out

def form_from_prompt(prompt: str):
    """
    Very basic rules demo: you likely want to replace this with real LLM logic!
    """
    p = prompt.lower()
    if "product" in p:
        return {
            "kind": "form",
            "title": "Product Form",
            "persist": "keep",
            "schema": [
                {"type": "text", "name": "title", "label": "Title"},
                {"type": "number", "name": "price", "label": "Price"},
                {"type": "select", "name": "category", "label": "Category", "options": ["A", "B", "C"]},
                {"type": "checkbox", "name": "active", "label": "Active"},
            ],
            "value": {"active": True}
        }
    elif "metadata" in p:
        return {
            "kind": "metadata",
            "title": "Metadata Editor",
            "persist": "keep",
            "value": {"entities": []}
        }
    elif "chat" in p:
        if "aws" in p:
            return {
                "kind": "chat",
                "title": "Chat with AWS",
                "persist": "keep",
                "chatType": "support",
                "value": {"entities": []}
            }
        else:
            return {
                "kind": "chat",
                "title": "Chat with OpenAI",
                "persist": "keep",
                "chatType": "analysis",
                "value": {"entities": []}
            }
    else:
        return {
            "kind": "form",
            "title": "User Form",
            "persist": "keep",
            "schema": [
                {"type": "text", "name": "name", "label": "Name"},
                {"type": "number", "name": "age", "label": "Age"},
                {"type": "select", "name": "role", "label": "Role", "options": ["User", "Admin"]},
                {"type": "checkbox", "name": "agree", "label": "Agree to terms"},
            ],
            "value": {"agree": False}
        }

def prompt_to_schema(prompt: str):
    """
    Top-level function to process a prompt into a sanitized Canvas-ready config.
    Call this from Flask or elsewhere.
    """
    # In a real system, swap in LLM or smarter logic here.
    cfg = form_from_prompt(prompt)
    safe = sanitize_config(cfg)
    return safe

# Optionally: for explicit export
__all__ = [
    "prompt_to_schema",
    "sanitize_config",
    "form_from_prompt",
    "sanitize_field",
    "sanitize_form_schema"
]