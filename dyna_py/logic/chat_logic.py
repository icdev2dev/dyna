import json
import asyncio

ALLOWED_CHAT_TYPES = {"default", "support", "analysis"}
ALLOWED_ROLES = {"user", "assistant", "system"}

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

def parse_mcp_result(res):
    """
    Attempt to extract a text snippet from a fastmcp result.
    Handles either a structured object with content[0].text or raw JSON/text.
    """
    try:
        if hasattr(res, "content") and res.content:
            txt = getattr(res.content[0], "text", None)
            if txt is not None:
                try:
                    data = json.loads(txt)
                    # Adapt this line to your MCP format!
                    return data['response']['payload']['content']['result'][0]['context']
                except Exception:
                    return txt
            else:
                return "No content found."
        if isinstance(res, dict):
            return (
                res.get("response", {})
                .get("payload", {})
                .get("content", {})
                .get("result")
                or json.dumps(res)
            )
        return str(res)
    except Exception as e:
        return f"Tool response parse error: {e}"

def build_reply(messages, chat_type, config, mcp_search_async=None):
    """
    Returns the assistant's reply as plain text (use for streaming).
    mcp_search_async is an optional async search callback, if using external tool.
    """
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
        # For "default" type, fall back to search or LLM, if mcp_search_async is provided.
        if mcp_search_async:
            # Note: In Flask handler, call using run_async(mcp_search_async(last_user))
            try:
                result = mcp_search_async(last_user)  # if callable returns string
                return str(result)
            except Exception as e:
                return f"Tool call failed: {e}"
        return "Default assistant reply: " + last_user

def run_async(coro):
    """Run an async coroutine from sync context safely."""
    try:
        loop = asyncio.get_running_loop()
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
        return asyncio.run(coro)

import time

def stream_text(text, chunk_size=16, delay=0.02):
    """Yield plain text chunks (no SSE framing), for Flask streaming."""
    try:
        for i in range(0, len(text), chunk_size):
            yield text[i:i+chunk_size]
            time.sleep(delay)
    except (GeneratorExit, BrokenPipeError):
        return

# Optionally: for explicit export
__all__ = [
    "sanitize_messages",
    "build_reply",
    "stream_text",
    "run_async",
    "clamp_str",
    "parse_mcp_result"
]