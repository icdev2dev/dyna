from flask import jsonify, request
from store.conversations import list_conversations_for_window

from store.conversations import get_conversation_messages_and_participants
import json
from flask import Response


def list_conversations_endpoint():
    status = request.args.get("status", "all")
    q = request.args.get("q")
    try:
        limit = int(request.args.get("limit", "100"))
    except ValueError:
        limit = 100
    try:
        offset = int(request.args.get("offset", "0"))
    except ValueError:
        offset = 0
    order = request.args.get("order", "desc")
    if order not in ("asc", "desc"):
        order = "desc"

    data = list_conversations_for_window(
        status=status,
        q=q,
        limit=limit,
        offset=offset,
        order=order,
    )
    return jsonify(data)




def _safe_jsonify(data):
    return Response(json.dumps(data, ensure_ascii=False, allow_nan=False),
        mimetype="application/json")

def conversation_messages_endpoint():
    conversation_id = request.args.get("conversation_id")
    if not conversation_id:
        return _safe_jsonify({"messages": [], "participants": [], "error": "missing conversation_id"}), 400

    try:
        limit = int(request.args.get("limit", "500"))
    except ValueError:
        limit = 500
    try:
        offset = int(request.args.get("offset", "0"))
    except ValueError:
        offset = 0
    order = request.args.get("order", "asc")
    if order not in ("asc", "desc"):
        order = "asc"

    data = get_conversation_messages_and_participants(
        conversation_id,
        limit=limit,
        offset=offset,
        order=order,
    )
    return _safe_jsonify(data)
    