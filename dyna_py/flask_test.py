from flask import Flask, request, jsonify
from flask import  Response, stream_with_context
from flask_cors import CORS  # optional; prefer proxy in dev
from fastmcp import Client

CONFIG = {
    "mcpServers": {
        "aws-knowledge-mcp-server": { "url": "https://knowledge-mcp.global.api.aws"}
    }
}

CACHE_TOOLS = {
    "aws_kb_search": "aws___search_documentation"
}


CLIENT = Client(CONFIG)


app = Flask(__name__)
# If you can proxy via Vite (recommended), you can remove CORS.
CORS(app, resources={r"/api/*": {"origins": "*"}})
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5174", "http://127.0.0.1:5174"]}})

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

def form_from_prompt(prompt: str):
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
        else :
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
        schema = [s for s in (sanitize_field(f) for f in schema) if s is not None]
        out["schema"] = schema
        out["value"] = cfg.get("value") if isinstance(cfg.get("value"), dict) else {}
    elif kind == "metadata":
        val = cfg.get("value")
        out["value"] = val if isinstance(val, dict) else {"entities": []}
    elif kind == "chat":
        # Your Canvas supports chat; include minimal safe defaults
        out["messages"] = cfg.get("messages") if isinstance(cfg.get("messages"), list) else []
        out["chatConfig"] = cfg.get("chatConfig") if isinstance(cfg.get("chatConfig"), dict) else {}

    # optional: clamp size/position if provided
    def clamp(v, lo, hi, default):
        try:
            n = float(v)
            return max(lo, min(hi, n))
        except Exception:
            return default

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

@app.post("/api/prompt-to-schema")
def prompt_to_schema():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "prompt is required"}), 400

    # In a real system, you could call an LLM or rules engine here
    cfg = form_from_prompt(prompt)

    # Sanitize before returning
    safe = sanitize_config(cfg)
    if not safe:
        return jsonify({"error": "invalid response"}), 500
    return jsonify(safe), 200


ALLOWED_CHAT_TYPES = {"default", "support", "analysis"}
ALLOWED_ROLES = {"user", "assistant", "system"}


import asyncio


async def mcp_search_async(search_phrase: str):
    tool_name = CACHE_TOOLS.get("aws_kb_search", "aws___search_documentation")
    async with Client(CONFIG) as client:
        res = await client.call_tool(tool_name, {"search_phrase": search_phrase})
    return parse_mcp_result(res)


def run_async(coro):
    """Run an async coroutine from sync context."""
    try:
        loop = asyncio.get_running_loop()
    # If we are somehow already in an event loop, offload to a new thread.
    # In normal Flask sync routes this branch won't trigger.
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
    # No running loop in this thread
        return asyncio.run(coro)

import json

def parse_mcp_result(res):
    """
    Attempt to extract a text snippet from a fastmcp result.
    Handles either a structured object with content[0].text or raw JSON/text.
    """
    
    try:
    # Common fastmcp pattern: res.content is a list with .text
       
        if hasattr(res, "content") and res.content:
            
            txt = getattr(res.content[0], "text", None)
            if txt is not None:
                try:
                    data = json.loads(txt)
                    return data['response']['payload']['content']['result'][0]['context']
                    # adapt to your server's shape
                    return (
                    data.get("response", {})
                    .get("payload", {})
                    .get("content", {})
                    .get("result")
                    or txt
                    )
                except Exception:
                    return txt
            else:
                return "hjh"
        # Fallback: if res is already a dict-like
        if isinstance(res, dict):
            
            return (
                res.get("response", {})
                .get("payload", {})
                .get("content", {})
                .get("result")
                or json.dumps(res)
            )

        # Last resort: stringify
        return str(res)
    except Exception as e:
        return f"Tool response parse error: {e}"
    
def clamp_str(s, max_len=4000):
    try:
        s = str(s)
    except Exception:
        s = ""
    return s[:max_len]



def sanitize_messages(msgs, limit=30):
    """Keep only recent messages, strip to safe shape."""
    if not isinstance(msgs, list):
        return []
    out = []
    for m in msgs[-limit:]:
        if not isinstance(m, dict):
            continue
        role = m.get("role")
        content = clamp_str(m.get("content", ""), 4000)
        if role in ALLOWED_ROLES and content:
            out.append({"role": role, "content": content})
    return out



def build_reply(messages, chat_type, config):
    """Very basic demo behavior for each type."""
    # last user message
    last_user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
    if not last_user:
        last_user = "(no user message)"

    if chat_type == "support":
        return (
            "Support assistant here. I’m looking into your request...\n\n"
            f"Summary of your issue: {last_user}\n"
            "- Tip: You can provide order IDs or timestamps to speed things up.\n"
            "Let me know if you have screenshots or logs."
        )
    elif chat_type == "analysis":
        words = last_user.split()
        return (
            "Analysis assistant: quick take.\n\n"
            f"- Word count: {len(words)}\n"
            f"- First 8 tokens: {words[:8]}\n"
            "Conclusion: provide a dataset sample and the hypothesis you want to test."
        )
    else:
     


        try:

            result = run_async(mcp_search_async(last_user))
            return str(result)

        except Exception as e:
            return f"Tool call failed: {e}"
    
import time

def stream_text(text, chunk_size=16, delay=0.02):
    """Yield plain text chunks (no SSE framing)."""
    try:
        for i in range(0, len(text), chunk_size):
            yield text[i:i+chunk_size]
            time.sleep(delay)  # demo pacing; remove in prod
    except (GeneratorExit, BrokenPipeError):
    # Client disconnected; stop silently
        return

from fastmcp import Client


@app.post("/api/chat")
def chat():
    data = request.get_json(silent=True) or {}
    
      
    chat_type = data.get("type") or "default"
    if chat_type not in ALLOWED_CHAT_TYPES:
        chat_type = "default"

    messages = sanitize_messages(data.get("messages"))
    config = data.get("config") if isinstance(data.get("config"), dict) else {}

    # Basic guardrails
    if not messages:
        # It’s okay to continue, but show a friendly error
        reply = "No messages received. Please say something to start the chat."
    else:
        reply = build_reply(messages, chat_type, config)

    return Response(
        stream_with_context(stream_text(reply)),
        mimetype="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-store"}
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
