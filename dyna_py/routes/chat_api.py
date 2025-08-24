from flask import  request, Response, stream_with_context
from logic.chat_logic import sanitize_messages, build_reply, stream_text

from logic.chat_logic import sanitize_messages, build_reply,stream_text

def chat_endpoint():
    
    data = request.get_json(silent=True) or {}
    print(data)
    chat_type = data.get("type") or "default"
    print(chat_type)
    if chat_type not in {"default", "support", "analysis"}:
        chat_type = "default"
    messages = sanitize_messages(data.get("messages"))
    config = data.get("config") if isinstance(data.get("config"), dict) else {}

    if not messages:
        reply = "No messages received. Please say something to start the chat."
    else:
        # Optionally, pass mcp_search_async here if using it
        reply = build_reply(messages, chat_type, config)

    return Response(
        stream_with_context(stream_text(reply)),
        mimetype="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-store"}
    )