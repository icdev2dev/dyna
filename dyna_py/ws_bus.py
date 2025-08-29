socketio = None

def init(sio):
    global socketio
    socketio = sio

def room_for_run(run_id: str) -> str:
    return f"run::{run_id}"

def emit_run_update(run_id: str, payload: dict):
# safe no-op if socketio not initialized yet
    if socketio is None:
        return
    try:
        print(f"now emiting: {payload}")
        socketio.emit("run_update", payload, to=room_for_run(run_id))
    except Exception as e:
        print(f"emit_run_update error for {run_id}: {e}")

