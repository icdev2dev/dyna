# app.py

import flask
from flask_cors import CORS
from routes.api_map import MAP_HTTP_FUNCS, handle_request_response


from flask_socketio import SocketIO, emit, disconnect, join_room, leave_room
from flask import request

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

def create_app():
    app = flask.Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    socketio = SocketIO(app, cors_allowed_origins=["http://localhost:5173"])

    configure_http(app)
    configure_ws(socketio=socketio)
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
