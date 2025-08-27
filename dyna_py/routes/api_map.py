# routes/api_map.py

from flask_socketio import SocketIO, emit, disconnect, join_room, leave_room
from flask import request


from .static_endpoints import serve_plugin_file
from .agents_endpoints import list_agents_endpoint, list_sessions_for_agent

from .chat_api import chat_endpoint
from .form_api import prompt_to_schema_endpoint
from .not_impl import not_implemented

# 1. All your websocket handlers go here.
def ws_test(data, socketio, sid):
    # Example simple echo
    socketio.emit('response', {'msg': 'Echo: ' + str(data)}, room=sid)

def handle_request_response(data, socketio: SocketIO):
    sid = request.sid  # Session ID for this websocket connection
    real_request = data.get('realRequest')
    if real_request and real_request in MAP_WS_FUNCS:
        try:
            MAP_WS_FUNCS[real_request](data=data, socketio=socketio, sid=sid)
        except Exception as e:
            # Optionally log error and respond
            socketio.emit('response', {'error': str(e)}, room=sid)
    else:
        # Unknown request type
        socketio.emit('response', {'error': 'Unknown ws request: ' + str(real_request)}, room=sid)



MAP_WS_FUNCS = {
    'ws_test': ws_test,
    # Add new handlers here!
}

MAP_HTTP_FUNCS = [

    ['/plugins/<path:subpath>', serve_plugin_file, ['GET']],
    ["/api/list-agent-configs",list_agents_endpoint , ['GET']],
    ["/api/prompt-to-schema", prompt_to_schema_endpoint, ['POST']],
    ["/api/chat", chat_endpoint, ['POST']],
    ["/api/list-sessions-for-agent",list_sessions_for_agent , ['GET']],
    

    # ...add more
]