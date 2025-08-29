# app.py

import flask
from flask_cors import CORS
from routes.api_map import MAP_HTTP_FUNCS, handle_request_response
from flask_socketio import SocketIO, emit, join_room, leave_room

import threading, asyncio, time
from flask import request

from ws_bus import init as ws_init, room_for_run
from store.sessions import get_last_step_for_session_id
import agents  # your asyncio agent runner (agents.main, etc.)

def configure_ws(socketio: SocketIO):    
    def request_response_wrapper(data):
        handle_request_response(data, socketio)
    socketio.on('request_response')(handler=request_response_wrapper)

def configure_http(app: flask.app.Flask):
    for http_func in MAP_HTTP_FUNCS:
        path, func, *rest = http_func
        kwargs = {}
        if rest:
            kwargs['methods'] = rest[0]
        app.add_url_rule(path, view_func=func, **kwargs)

def create_app_and_socket():
    app = flask.Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    # Use threading async_mode to avoid eventlet/gevent. It’s fine for dev and simple prod.
    socketio = SocketIO(app, cors_allowed_origins=["http://localhost:5173", "http://127.0.0.1:5173"])
    print("SocketIO async mode:", socketio.async_mode)  # should print 'eventlet'


    # Initialize emitter hub
    ws_init(socketio)

    # Socket.IO: subscribe/unsubscribe to run updates
    @socketio.on("subscribe_run")
    def on_subscribe_run(data):
        run_id = (data or {}).get("run_id") or ""
        if not run_id:
            emit("error", {"error": "missing run_id"})
            return
        join_room(room_for_run(run_id))
        # Send an immediate snapshot if we can figure out session_id
        try:
            # run_id is "agent_id::session_id" per your Svelte code
            parts = run_id.split("::", 1)
            session_id = parts[1] if len(parts) == 2 else None
            last_text = ""
            if session_id:
                last_text = get_last_step_for_session_id(session_id=session_id) or ""
            emit("run_update", {
                "run_id": run_id,
                "last_text": last_text,
                "timestamp": int(time.time() * 1000),
            })
        except Exception as e:
            print(f"subscribe_run snapshot error: {e}")

    @socketio.on("unsubscribe_run")
    def on_unsubscribe_run(data):
        run_id = (data or {}).get("run_id") or ""
        if not run_id:
            return
        leave_room(room_for_run(run_id))

    configure_http(app)
    configure_ws(socketio=socketio)
    return app, socketio

def start_background_agents():
# Run your asyncio agents loop in a dedicated thread
# agents.main() is async, so run it in its own event loop.
    def runner():
        try:
            asyncio.run(agents.main())
        except Exception as e:
            print(f"Agents main exited: {e}")
    t = threading.Thread(target=runner, daemon=True)
    t.start()


if __name__ == "__main__":
    app, socketio = create_app_and_socket()
    start_background_agents()
    # Important: disable the reloader to avoid starting agents twice
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, use_reloader=False)
